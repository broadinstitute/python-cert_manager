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
    ]

    def __init__(self, client, endpoint, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string endpoint: The URL of the API endpoint (ex. "/ssl")
        :param string api_version: The API version to use; the default is "v1"
        """
        super(Certificates, self).__init__(client=client, endpoint=endpoint, api_version=api_version)

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

    def collect(self, cert_id, cert_format):
        """Retrieve an existing certificate from the API.

        This method will raise a Pending exception if the certificate is still in a pending state.

        :param int cert_id: The certificate ID
        :param str cert_format: The format in which to retreive the certificate. Allowed values: *self.valid_formats*
        :return str: the string representing the certificate in the requested format
        """
        if cert_format not in self.valid_formats:
            raise Exception("Invalid cert format %s provided" % cert_format)

        url = self._url("/collect/{}/{}".format(cert_id, cert_format))

        try:
            result = self._client.get(url)
        except HTTPError:
            raise Pending("certificate %d still in 'pending' state" % cert_id)

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
        :return dict: The certificate_id and the normal status messages for errors
        """
        cert_types = self.types

        # Retrieve all the arguments
        cert_type_name = kwargs.get("cert_type_name")
        csr = kwargs.get("csr")
        term = kwargs.get("term")
        org_id = kwargs.get("org_id")
        subject_alt_names = kwargs.get("subject_alt_names", None)

        # Make sure a valid certificate type name was provided
        if cert_type_name not in cert_types:
            raise Exception("Incorrect certificate type specified: '{}'".format(cert_type_name))

        type_id = cert_types[cert_type_name]["id"]
        terms = cert_types[cert_type_name]["terms"]

        # Make sure a valid term is specified
        if term not in terms:
            # You have to do the list/map/str thing because join can only operate on
            # a list of strings, and this will be a list of numbers
            trm = ", ".join(list(map(str, terms)))
            raise Exception("Incorrect term specified: {}.  Valid terms are {}.".format(term, trm))

        url = self._url("/enroll")
        data = {
            "orgId": org_id, "csr": csr.rstrip(), "subjAltNames": subject_alt_names, "certType": type_id,
            "numberServers": 1, "serverType": -1, "term": term, "comments": "Enrolled by %s" % self._client.user_agent,
            "externalRequester": ""
        }
        result = self._client.post(url, data=data)

        return result.json()

    def renew(self, cert_id):
        """Renew the certificate specified by the certificate ID.

        :param int cert_id: The certificate ID
        :return dict: The renewal result. "Successful" on success
        """
        url = self._url("/renewById/{}".format(cert_id))
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

        url = self._url("/replace/{}".format(cert_id))
        data = {"csr": csr, "commonName": common_name, "subjectAlternativeNames": subject_alt_names, "reason": reason}

        result = self._client.post(url, data=data)

        return result.json()

    def revoke(self, cert_id, reason=""):
        """Revoke the certificate specified by the certificate ID.

        :param int cert_id: The certificate ID
        :param str reason: The Reason for revocation.
            Reason can be up to 512 characters and cannot be blank (i.e. empty string)
        :return dict: The revocation result. "Successful" on success
        """
        url = self._url("/revoke/{}".format(cert_id))

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if (not reason) or (len(reason) > 511):
            raise Exception("Sectigo limit: reason must be > 0 character and < 512 characters")

        data = {"reason": reason}

        result = self._client.post(url, data=data)

        return result.json()
