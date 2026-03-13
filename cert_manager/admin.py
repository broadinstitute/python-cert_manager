"""Define the cert_manager.admin.Admin class."""

import logging
import re

from requests.exceptions import HTTPError

from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class AdminCreationResponseError(Exception):
    """An error (other than HTTPError) occurred while processing Admin Creation API response."""


class Admin(Endpoint):
    """Query the Sectigo Cert Manager REST API for Admin data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        Args:
            client: An instantiated cert_manager.Client object
            api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/admin", api_version=api_version)

        self._admins = None
        self.all()

    def all(self, force=False):
        """Return a list of admins from Sectigo.

        Args:
            force: If set to True, force refreshing the data from the API

        Returns:
            A list of dictionaries representing the admins
        """
        if (self._admins) and (not force):
            return self._admins

        result = self._client.get(self._api_url)

        self._admins = result.json()

        return self._admins

    def create(self, login, email, forename, surname, password, credentials, **kwargs):  # noqa: PLR0913
        """Create a new administrator.

        Formating for "Credentials" can be found in the Sectigo API Documentation.
        Additional request fields are documented in Sectigo API Documentation
        https://sectigo.com/faqs/detail/Sectigo-Certificate-Manager-SCM-REST-API/kA01N000000XDkE

        Other parameters that may be useful are privileges, identityProviderId, and idpPersonId

        Args:
            login: Login name of admin to create
            email: Email of admin to create
            forename: Fore/First name of admin
            surname: Sur/Last name of admin
            password: Password for the admin
            credentials: List of Credentials to apply to admin
            kwargs: Additional fields that will be passed to the API

        Returns:
            A dictionary containing the id of the created admin
        """
        data = {
            "login": login,
            "email": email,
            "forename": forename,
            "surname": surname,
            "password": password,
            "credentials": credentials,
        }

        for key, value in kwargs.items():
            data[key] = value

        try:
            result = self._client.post(self._api_url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == self._capture_err_code:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        # for status >= 400, HTTPError is raised
        if result.status_code != self._expected_code:
            raise AdminCreationResponseError(f"Unexpected HTTP status {result.status_code}")
        try:
            loc = result.headers["Location"]
            admin_id = re.search(r"/([0-9]+)$", loc)[1]
        # result.headers lookup fails
        except KeyError as exc:
            raise AdminCreationResponseError(
                "Response does not include a Location header"
            ) from exc
        # re.search does not match, at all or the first group
        except (TypeError, IndexError) as exc:
            raise AdminCreationResponseError(
                f"Did not find an Admin ID in Response Location URL: {loc}"
            ) from exc

        return {"id": int(admin_id)}

    def get(self, admin_id):
        """Return a dictionary of admin information.

        Args:
            admin_id: The ID of the admin to query

        Returns:
            A dictionary representing the admin information
        """
        url = self._url(str(admin_id))
        result = self._client.get(url)

        return result.json()

    def get_idps(self):
        """Return a list of IDPs.

        Returns:
            A list of dictionaries representing the IDPs
        """
        url = self._url("idp")
        result = self._client.get(url)

        return result.json()

    def delete(self, admin_id):
        """Delete an admin.

        Args:
            admin_id: The ID of the admin to delete

        Returns:
            Boolean indicating deletion success or failure
        """
        url = self._url(str(admin_id))
        result = self._client.delete(url)

        return result.ok

    def update(self, admin_id, **kwargs):
        """Update an admin.

        Args:
            admin_id: The ID of the admin to update
            kwargs: A dictionary of properties to update

        Returns:
            Boolean indicating update success or failure
        """
        data = {}
        for key, value in kwargs.items():
            data[key] = value
        url = self._url(str(admin_id))

        try:
            result = self._client.put(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == self._capture_err_code:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.ok
