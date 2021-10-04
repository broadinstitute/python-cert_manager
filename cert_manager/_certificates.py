# -*- coding: utf-8 -*-
"""Define the cert_manager._certificate.Certificates base class."""

import logging
from requests.exceptions import HTTPError

from ._helpers import Pending
from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class Certificates(Endpoint):
    """Act as a superclass for all certificate-related classes.

    This is due to the fact that several of the API endpoints have almost identical functions, so this allows code
    to be shared.
    """

    valid_formats = [
        "x509",     # for X509, Base64 encoded
        "x509CO",   # for X509 Certificate only, Base64 encoded
        "x509IO",   # for X509 Intermediates/root only, Base64 encoded
        "base64",   # for PKCS#7 Base64 encoded,
        "bin",      # for PKCS#7 Bin encoded
        "x509IOR",  # for X509 Intermediates/root only Reverse, Base64 encoded
        "pem",      # for Certificate (w/ chain), PEM encoded
        "pemco",    # for Certificate only, PEM encoded
        "pemia",    # for Certificate (w/ issuer after), PEM encoded
    ]

    def __init__(self, client, endpoint, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string endpoint: The URL of the API endpoint (ex. "/ssl")
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint=endpoint, api_version=api_version)

        # Set to None initially.  Will be filled in by methods later.
        self.__cert_types = None
        self.__custom_fields = None

    @property
    def types(self):
        """Retrieve all certificate types that are currently available.

        :return list: A list of dictionaries of certificate types
        """
        # Only go to the API if we haven't done the API call yet, or if someone
        # specifically wants to refresh the internal cache
        if not self.__cert_types:
            url = self._url("/types")
            result = self._client.get(url)

            # Build a dictionary instead of a flat list of dictionaries
            self.__cert_types = {}
            for res in result.json():
                name = res["name"]
                self.__cert_types[name] = {}
                self.__cert_types[name]["id"] = res["id"]
                self.__cert_types[name]["terms"] = res["terms"]

        return self.__cert_types

    @property
    def custom_fields(self):
        """Retrieve all custom fields defined for SSL certificates.

        :return list: A list of dictionaries of custom fields
        """
        # Only go to the API if we haven't done the API call yet, or if someone
        # specifically wants to refresh the internal cache
        if not self.__custom_fields:
            url = self._url("/customFields")
            result = self._client.get(url)

            self.__custom_fields = result.json()

        return self.__custom_fields

    def _validate_custom_fields(self, custom_fields):
        """Check the structure and contents of a list of dicts representing custom fields
        Raise exceptions if validation fails

        :raises Exception: if any of the validation steps fail
        """
        # Make sure all custom fields are valid if present
        custom_field_names = [f['name'] for f in self.custom_fields]
        for custom_field in custom_fields:
            if not isinstance(custom_field, dict):
                msg = "Values in the custom_fields list must be dictionaries, not {}"
                raise Exception(msg.format(type(custom_field)))
            if not ('name' in custom_field and 'value' in custom_field):
                raise Exception(
                    "Dictionaries in the custom_fields list must contain both a 'name' key and 'value' key"
                )
            if custom_field.get('name') not in custom_field_names:
                msg = "Custom field {} not defined for your account. defined custom fields are {}"
                raise Exception(msg.format(custom_field.get('name'), custom_field_names))
        mandatory_fields = [f['name'] for f in self.custom_fields if f['mandatory'] is True]
        for field_name in mandatory_fields:
            # for each mandatory field, there should be exactly one dict in the custom_fields list
            # whose name matches that mandatory field name
            matching_fields = [f for f in custom_fields if f['name'] == field_name]
            if len(matching_fields) < 1:
                raise Exception(f"Missing mandatory custom field {field_name}")
            if len(matching_fields) > 1:
                raise Exception(f"Too many custom field objects with name {field_name}")

    def collect(self, cert_id, cert_format):
        """Retrieve an existing certificate from the API.

        This method will raise a Pending exception if the certificate is still in a pending state.

        :param int cert_id: The certificate ID
        :param str cert_format: The format in which to retreive the certificate. Allowed values: *self.valid_formats*
        :return str: the string representing the certificate in the requested format
        """
        if cert_format not in self.valid_formats:
            raise Exception(f"Invalid cert format {cert_format} provided")

        url = self._url(f"/collect/{cert_id}/{cert_format}")

        try:
            result = self._client.get(url)
        except HTTPError as exc:
            raise Pending(f"certificate {cert_id} still in 'pending' state") from exc

        # The certificate is ready for collection
        return result.content.decode(result.encoding)

    def enroll(self, **kwargs):
        """Enroll a certificate request with Sectigo to generate a certificate.

        :param string cert_type_name: The full cert type name
            Note: the name must match names returned from the get_types() method
        :param string csr: The Certificate Signing Request (CSR)
        :param int term: The length, in days, for the certificate to be issued
        :param int org_id: The ID of the organization in which to enroll the certificate
        :param list subject_alt_names: A list of Subject Alternative Names
        :param list external_requester: One or more e-mail addresses
        :param list custom_fields: zero or more objects representing custom fields and their values
            Note: each object must have a 'name' key and a 'value' key
        :return dict: The certificate_id and the normal status messages for errors
        """
        # Retrieve all the arguments
        cert_type_name = kwargs.get("cert_type_name")
        csr = kwargs.get("csr")
        term = kwargs.get("term")
        org_id = kwargs.get("org_id")
        subject_alt_names = kwargs.get("subject_alt_names", None)
        external_requester = kwargs.get("external_requester", None)
        custom_fields = kwargs.get("custom_fields", [])

        # Make sure a valid certificate type name was provided
        if cert_type_name not in self.types:
            raise Exception(f"Incorrect certificate type specified: '{cert_type_name}'")

        type_id = self.types[cert_type_name]["id"]
        terms = self.types[cert_type_name]["terms"]

        # Make sure a valid term is specified
        if term not in terms:
            # You have to do the list/map/str thing because join can only operate on
            # a list of strings, and this will be a list of numbers
            trm = ", ".join(list(map(str, terms)))
            raise Exception(f"Incorrect term specified: {term}.  Valid terms are {trm}.")

        self._validate_custom_fields(custom_fields)

        url = self._url("/enroll")
        data = {
            "orgId": org_id, "csr": csr.rstrip(), "subjAltNames": subject_alt_names, "certType": type_id,
            "numberServers": 1, "serverType": -1, "term": term, "comments": f"Enrolled by {self._client.user_agent}",
            "externalRequester": external_requester
        }
        if custom_fields:
            data['customFields'] = custom_fields
        result = self._client.post(url, data=data)

        return result.json()

    def renew(self, cert_id):
        """Renew the certificate specified by the certificate ID.

        :param int cert_id: The certificate ID
        :return dict: The renewal result. "Successful" on success
        """
        url = self._url(f"/renewById/{cert_id}")
        result = self._client.post(url, data="")

        return result.json()

    def replace(self, **kwargs):
        """Replace a pre-existing certificate.

        :param int cert_id: The certificate ID
        :param string csr: The Certificate Signing Request (CSR)
        :param string common_name: Certificate common name.
        :param str reason: Reason for replacement (up to 512 characters), can be blank: "", but must exist.
        :param string subject_alt_names: Subject Alternative Names separated by a ",".
        :return: The result of the operation, "Successful" on success
        :rtype: dict
        """
        # Retrieve all the arguments
        cert_id = kwargs.get("cert_id")
        csr = kwargs.get("csr")
        common_name = kwargs.get("common_name")
        reason = kwargs.get("reason")
        subject_alt_names = kwargs.get("subject_alt_names", None)

        url = self._url(f"/replace/{cert_id}")
        data = {"csr": csr, "commonName": common_name, "subjectAlternativeNames": subject_alt_names, "reason": reason}

        result = self._client.post(url, data=data)
        result.raise_for_status()

        return {}

    def revoke(self, cert_id, reason=""):
        """Revoke the certificate specified by the certificate ID.

        :param int cert_id: The certificate ID
        :param str reason: The Reason for revocation.
            Reason can be up to 512 characters and cannot be blank (i.e. empty string)
        :return dict: The revocation result. "Successful" on success
        """
        url = self._url(f"/revoke/{cert_id}")

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if (not reason) or (len(reason) > 511):
            raise Exception("Sectigo limit: reason must be > 0 character and < 512 characters")

        data = {"reason": reason}

        result = self._client.post(url, data=data)
        result.raise_for_status()

        return {}
