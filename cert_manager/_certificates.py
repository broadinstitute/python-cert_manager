"""Define the cert_manager._certificate.Certificates base class."""

import logging

from requests.exceptions import HTTPError

from ._endpoint import Endpoint
from ._helpers import CustomFieldsError, PendingError

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

        Args:
            client: An instantiated cert_manager.Client object
            endpoint: The URL of the API endpoint (ex. "/ssl")
            api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint=endpoint, api_version=api_version)

        # Set to None initially.  Will be filled in by methods later.
        self._cert_types = None
        self._custom_fields = None
        self._reason_maxlen = 512

    @property
    def types(self):
        """Retrieve all certificate types that are currently available.

        Returns:
            A list of dictionaries of certificate types
        """
        # Only go to the API if we haven't done the API call yet, or if someone
        # specifically wants to refresh the internal cache
        if not self._cert_types:
            url = self._url("/types")
            result = self._client.get(url)

            # Build a dictionary instead of a flat list of dictionaries
            self._cert_types = {}
            for res in result.json():
                name = res["name"]
                self._cert_types[name] = {}
                self._cert_types[name]["id"] = res["id"]
                self._cert_types[name]["terms"] = res["terms"]

        return self._cert_types

    @property
    def custom_fields(self):
        """Retrieve all custom fields defined for SSL certificates.

        Returns:
            A list of dictionaries of custom fields
        """
        # Only go to the API if we haven't done the API call yet, or if someone
        # specifically wants to refresh the internal cache
        if not self._custom_fields:
            url = self._url("/customFields")
            result = self._client.get(url)

            self._custom_fields = result.json()

        return self._custom_fields

    def _validate_custom_fields(self, custom_fields):
        """Check the structure and contents of a list of custom fields dicts. Raise exceptions if validation fails.

        Args:
            custom_fields: A list of dictionaries representing custom fields

        Raises:
            CustomFieldsError: if any of the validation steps fail
        """
        # Make sure all custom fields are valid if present
        custom_field_names = [f['name'] for f in self.custom_fields]
        for custom_field in custom_fields:
            if not isinstance(custom_field, dict):
                msg = "Values in the custom_fields list must be dictionaries, not {}"
                raise CustomFieldsError(msg.format(type(custom_field)))
            if not ('name' in custom_field and 'value' in custom_field):
                raise CustomFieldsError(
                    "Dictionaries in the custom_fields list must contain both a 'name' key and 'value' key"
                )
            if custom_field.get('name') not in custom_field_names:
                msg = "Custom field {} not defined for your account. defined custom fields are {}"
                raise CustomFieldsError(msg.format(custom_field.get('name'), custom_field_names))
        mandatory_fields = [f['name'] for f in self.custom_fields if f['mandatory'] is True]
        for field_name in mandatory_fields:
            # for each mandatory field, there should be exactly one dict in the custom_fields list
            # whose name matches that mandatory field name
            matching_fields = [f for f in custom_fields if f['name'] == field_name]
            if len(matching_fields) < 1:
                raise CustomFieldsError(f"Missing mandatory custom field {field_name}")
            if len(matching_fields) > 1:
                raise CustomFieldsError(f"Too many custom field objects with name {field_name}")

    def collect(self, cert_id, cert_format):
        """Retrieve an existing certificate from the API.

        This method will raise a PendingError exception if the certificate is still in a pending state.

        Args:
            cert_id: The certificate ID
            cert_format: The format in which to retreive the certificate. Allowed values: *self.valid_formats*
        Returns:
            The string representing the certificate in the requested format
        """
        if cert_format not in self.valid_formats:
            raise ValueError(f"Invalid cert format {cert_format} provided")

        url = self._url(f"/collect/{cert_id}/{cert_format}")

        try:
            result = self._client.get(url)
        except HTTPError as exc:
            raise PendingError(f"certificate {cert_id} still in 'pending' state") from exc

        # The certificate is ready for collection
        encoding = result.encoding or "ascii"
        return result.content.decode(encoding)

    def enroll(self, **kwargs):
        """Enroll a certificate request with Sectigo to generate a certificate.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Required fields are:
            cert_type_name: The full cert type name
                Note: the name must match names returned from the get_types() method
            csr: The Certificate Signing Request (CSR)
            term: The length, in days, for the certificate to be issued
            org_id: The ID of the organization in which to enroll the certificate
            subject_alt_names: A list of Subject Alternative Names
            external_requester: One or more e-mail addresses
            custom_fields: zero or more objects representing custom fields and their values
                Note: each object must have a 'name' key and a 'value' key
        Returns:
            The certificate_id and the normal status messages for errors
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
            raise ValueError(f"Incorrect certificate type specified: '{cert_type_name}'")

        type_id = self.types[cert_type_name]["id"]
        terms = self.types[cert_type_name]["terms"]

        # Make sure a valid term is specified
        if term not in terms:
            # You have to do the list/map/str thing because join can only operate on
            # a list of strings, and this will be a list of numbers
            trm = ", ".join(list(map(str, terms)))
            raise ValueError(f"Incorrect term specified: {term}.  Valid terms are {trm}.")

        self._validate_custom_fields(custom_fields)

        # SAN field needs to be a comma-separated string, not a list, opposite to replace
        final_san = subject_alt_names
        if isinstance(subject_alt_names, list):
            final_san = ",".join(subject_alt_names)

        url = self._url("/enroll")
        data = {
            "orgId": org_id, "csr": csr.rstrip(), "subjAltNames": final_san, "certType": type_id,
            "numberServers": 1, "serverType": -1, "term": term, "comments": f"Enrolled by {self._client.user_agent}",
            "externalRequester": external_requester
        }
        if custom_fields:
            data['customFields'] = custom_fields
        result = self._client.post(url, data=data)

        return result.json()

    def replace(self, **kwargs):
        """Replace a pre-existing certificate.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Required fields are:
                cert_id: The certificate ID
                csr: The Certificate Signing Request (CSR)
                common_name: Certificate common name.
                reason: Reason for replacement (up to 512 characters), can be blank: "", but must exist.
                subject_alt_names: A list of Subject Alternative Names.

        Returns:
            An empty dictionary on success
        """
        # Retrieve all the arguments
        cert_id = kwargs.get("cert_id")
        csr = kwargs.get("csr")
        common_name = kwargs.get("common_name")
        reason = kwargs.get("reason")
        subject_alt_names = kwargs.get("subject_alt_names", None)

        # SAN field needs to be a list, different than enroll
        final_san = subject_alt_names
        if subject_alt_names and not isinstance(subject_alt_names, list):
            final_san = subject_alt_names.split(",")

        url = self._url(f"/replace/{cert_id}")
        data = {"csr": csr, "commonName": common_name, "subjectAlternativeNames": final_san, "reason": reason}

        result = self._client.post(url, data=data)
        result.raise_for_status()

        return {}

    def revoke(self, cert_id, reason=""):
        """Revoke the certificate specified by the certificate ID.

        Args:
            cert_id: The certificate ID
            reason: The Reason for revocation.
                Reason can be up to 512 characters and cannot be blank (i.e. empty string)

        Returns:
            An empty dictionary on success
        """
        url = self._url(f"/revoke/{cert_id}")

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if not reason or len(reason) >= self._reason_maxlen:
            raise ValueError(f"Sectigo limit: reason must be > 0 character and < {self._reason_maxlen} characters")

        data = {"reason": reason}

        result = self._client.post(url, data=data)
        result.raise_for_status()

        return {}
