"""Define the cert_manager.certificates.smime.SMIME class."""
import logging

from requests.exceptions import HTTPError

from ._certificates import Certificates
from ._helpers import PendingError, RevokedError, paginate, version_hack

LOGGER = logging.getLogger(__name__)


class SMIME(Certificates):
    """Query the Sectigo Cert Manager REST API for S/MIME data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        Args:
            client: An instantiated cert_manager.Client object
            api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/smime", api_version=api_version)
        self._reason_maxlen = 512

    @paginate
    def list(self, **kwargs):
        """Return a list of all clients certificates from Sectigo.

        The 'size' and 'position' parameters passed as arguments to this function will be used
        by the pagination wrapper to page through results.  All other filtering parameters can be
        referenced at:
        https://sectigo.com/knowledge-base/detail/SCM-Sectigo-Certificate-Manager-REST-API/kA01N000000XDkE

        Args:
            kwargs: A dictionary of arguments to pass to the API

        Returns:
            iter: An iterator object is returned to cycle through the certificates
        """
        result = self._client.get(self._api_url, params=kwargs)
        return result.json()

    @version_hack(service="smime", version="v2")
    def list_by_email(self, **kwargs):
        """Return a list of all client certificates for a person with given email.

        Args:
            kwargs: A dictionary of arguments to pass to the API

        Returns:
            iter: An iterator object is returned to cycle through the certificates
        """
        email = kwargs["email"]

        result = self._client.get(self._url(f"/byPersonEmail/{email}"))
        return result.json()

    def enroll(self, **kwargs):
        """Enroll a client certificate request with Sectigo to generate a certificate.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Allowed fields are:
                cert_type_name: The full cert type name
                    Note: the name must match names returned from the get_types() method
                csr: The Certificate Signing Request (CSR)
                email: The person's e-mail
                phone: The person's phone number
                secondary_emails: The person's secondary e-mail(s)
                first_name: The person's first name
                middleName: The person's middle name
                last_name: The person's last name
                common_name: The person's common name.
                    If ommited, constructed from person's full name
                eppn: The person's EPPN
                upn: The person's UPN (User Principal Name)
                term: The length, in days, for the certificate to be issued
                org_id: The ID of the organization in which to enroll the certificate
                custom_fields: zero or more objects representing custom fields and their values
                    Note: each object must have a 'name' key and a 'value' key

        Returns:
            The orderNumber (Obsolete, backendCertId should be used instead) and backendCertId
        """
        # Retrieve all the arguments
        cert_type_name = kwargs.get("cert_type_name")
        csr = kwargs.get("csr")
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        secondary_emails = kwargs.get("secondary_emails", None)
        first_name = kwargs.get("first_name")
        middle_name = kwargs.get("middle_name")
        last_name = kwargs.get("last_name")
        common_name = kwargs.get("common_name")
        term = kwargs.get("term")
        org_id = kwargs.get("org_id")
        custom_fields = kwargs.get("custom_fields", [])
        eppn = kwargs.get("eppn")
        upn = kwargs.get("upn")

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
            "orgId": org_id, "csr": csr.rstrip(), "certType": type_id, "term": term,
            "email": email, "phone": phone, "secondaryEmails": secondary_emails,
            "firstName": first_name, "middleName": middle_name, "lastName": last_name,
            "commonName": common_name, "eppn": eppn, "upn": upn,
        }
        if custom_fields:
            data['customFields'] = custom_fields
        result = self._client.post(url, data=data)

        return result.json()

    def collect(self, cert_id):
        """Retrieve an existing client certificate from the API.

        This method will raise a PendingError exception if the certificate is still in a pending state.

        Args:
            cert_id: The Certificate ID given on enroll success

        Returns:
            The string representing the certificate in the requested format
        """
        if not cert_id:
            raise ValueError("Argument 'cert_id' can't be None")
        url = self._url(f"/collect/{cert_id}")

        try:
            result = self._client.get(url)
        except HTTPError as exc:
            err_code = exc.response.json().get("code")
            if err_code == RevokedError.CODE:
                raise RevokedError(f"certificate {cert_id} in 'revoked' state") from exc
            if err_code == PendingError.CODE:
                raise PendingError(f"certificate {cert_id} still in 'pending' state") from exc
            raise exc

        # The certificate is ready for collection
        encoding = result.encoding or "ascii"
        return result.content.decode(encoding)

    @version_hack(service="smime", version="v2")
    def replace(self, **kwargs):
        """Replace a pre-existing client certificate.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Allowed fields are:
                cert_id: The certificate ID
                csr: The Certificate Signing Request (CSR)
                reason: Reason for replacement (up to 512 characters), can be blank: "", but must exist.
                revoke: Revoke previous certificate if true. Default is True
        """
        # Retrieve all the arguments
        cert_id = kwargs["cert_id"]
        csr = kwargs["csr"]
        reason = kwargs.get("reason")
        revoke = kwargs.get("revoke", True)

        url = self._url(f"/replace/order/{cert_id}")
        data = {"csr": csr, "reason": reason, "revoke": revoke}
        self._client.post(url, data=data)

        return {}

    @version_hack(service="smime", version="v2")
    def renew(self, order_num="", serial_num=""):
        """Renew a client certificate with the specified order or serial number.

        Args:
            order_num: The certificate order number
            serial_num: The certificate serial number
                You can provide either the order or serial number, not both.

        Returns:
            dict: A dictionary containing the new order number and cert ID
        """
        if order_num and serial_num:
            raise ValueError("Cannot provide both order number and serial number")

        if order_num:
            url = self._url(f"/renew/order/{order_num}")
        else:
            url = self._url(f"/renew/serial/{serial_num}")
        ret = self._client.post(url)

        return ret.json()

    def revoke(self, cert_id, reason=""):
        """Revoke a client certificate specified by the certificate ID.

        Args:
            cert_id: The certificate ID
            reason: The Reason for revocation.
                Reason can be up to 512 characters and cannot be blank (i.e. empty string)
        """
        url = self._url(f"/revoke/order/{cert_id}")

        if not cert_id:
            raise ValueError("Argument 'cert_id' can't be None")

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if not reason or len(reason) >= self._reason_maxlen:
            raise ValueError(f"Sectigo limit: reason must be > 0 character and < {self._reason_maxlen} characters")

        data = {"reason": reason}
        self._client.post(url, data=data)

        return {}

    def revoke_by_email(self, email, reason=""):
        """Revoke all client certificate related to an email.

        Args:
            email: The person email address
            reason: The Reason for revocation.
                Reason can be up to 512 characters and cannot be blank (i.e. empty string)
        """
        url = self._url("/revoke")

        if not email:
            raise ValueError("Argument 'email' can't be empty or None")

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if not reason or len(reason) >= self._reason_maxlen:
            raise ValueError(f"Sectigo limit: reason must be > 0 character and < {self._reason_maxlen} characters")

        data = {"email": email, "reason": reason}
        self._client.post(url, data=data)

        return {}
