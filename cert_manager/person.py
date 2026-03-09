"""Define the cert_manager.person.Person class."""

import logging
from urllib.parse import quote

from ._endpoint import Endpoint
from ._helpers import paginate

LOGGER = logging.getLogger(__name__)


class Person(Endpoint):
    """Query the Sectigo Cert Manager REST API for Person data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        Args:
            client: An instantiated cert_manager.Client object
            api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/person", api_version=api_version)

    @paginate
    def list(self, **kwargs):
        """Return a list of people in sectigo.

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

    def find(self, email):
        """Return a list of people with the given email from the Sectigo API.

        Args:
            email: The email address for which we are searching

        Returns:
            list: A list of dictionaries representing the people found
        """
        quoted_email = quote(email)

        url = self._url(f"/id/byEmail/{quoted_email}")

        result = self._client.get(url)

        return result.json()

    def get(self, person_id):
        """Returns the details of a person.

        Args:
            person_id: The person's ID

        Returns:
            dict: A dictionary of the person's details
        """
        url = self._url(str(person_id))
        result = self._client.get(url)
        return result.json()

    def create(self, **kwargs) -> dict:
        """Create a person.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Allowed fields are:
                first_name: The person's first name
                middleName: The person's middle name
                last_name: The person's last name
                email: The person's e-mail
                validation_type: Person's validation type. Values: [STANDARD, HIGH]
                org_id: The ID of the organization in which to enroll the certificate
                phone: The person's phone number
                common_name: The person's common name. If ommited, constructed from person's full name
                secondary_emails: The person's secondary e-mail(s)
                eppn: The person's EPPN
                upn: The person's UPN (User Principal Name)

        Returns:
            dict: A dict containing the 'personId' of the created person
        """
        # Retrieve all the arguments
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        secondary_emails = kwargs.get("secondary_emails", None)
        first_name = kwargs.get("first_name")
        middle_name = kwargs.get("middle_name")
        last_name = kwargs.get("last_name")
        common_name = kwargs.get("common_name")
        org_id = kwargs.get("org_id")
        validation_type = kwargs.get("validation_type")
        eppn = kwargs.get("eppn")
        upn = kwargs.get("upn")

        data = {
            "firstName": first_name, "middleName": middle_name, "lastName": last_name, "email": email,
            "validationType": validation_type, "organizationId": org_id, "phone": phone,
            "commonName": common_name, "secondaryEmails": secondary_emails, "eppn": eppn, "upn": upn,
        }
        result = self._client.post(self.api_url, data=data)
        # Sectigo api returns the created person's location in a header
        created_id = result.headers.get("Location").split("/")[-1]

        # Use personId to be consistent with the API return of the 'find' method
        return {"personId": created_id}

    def update(self, **kwargs) -> None:
        """Update a person.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Allowed fields are:
                person_id: The person's ID
                first_name: The person's first name
                middleName: The person's middle name
                last_name: The person's last name
                email: The person's e-mail
                validation_type: Person's validation type. Values: [STANDARD, HIGH]
                org_id: The ID of the organization in which to enroll the certificate
                phone: The person's phone number
                common_name: The person's common name. If ommited, constructed from person's full name
                secondary_emails: The person's secondary e-mail(s)
                eppn: The person's EPPN
                upn: The person's UPN (User Principal Name)
        """
        # Retrieve all the arguments
        person_id = kwargs.get("person_id")
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        secondary_emails = kwargs.get("secondary_emails", None)
        first_name = kwargs.get("first_name")
        middle_name = kwargs.get("middle_name")
        last_name = kwargs.get("last_name")
        common_name = kwargs.get("common_name")
        org_id = kwargs.get("org_id")
        validation_type = kwargs.get("validation_type")
        eppn = kwargs.get("eppn")
        upn = kwargs.get("upn")

        data = {
            "firstName": first_name, "middleName": middle_name, "lastName": last_name, email: "email",
            "validationType": validation_type, "organizationId": org_id, "phone": phone,
            "commonName": common_name, "secondaryEmails": secondary_emails, "eppn": eppn, "upn": upn,
        }
        self._client.put(self._url(str(person_id)), data=data)

    def delete(self, **kwargs):
        """Delete a person.

        Args:
            kwargs: A dictionary of arguments to pass to the API.
            Allowed fields are:
                person_id: The person's ID
        """
        person_id = kwargs.get("person_id")
        self._client.delete(self._url(str(person_id)))
