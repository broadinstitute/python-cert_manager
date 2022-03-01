# -*- coding: utf-8 -*-
"""Define the cert_manager.admin.Admin class."""

import re
import logging
from requests.exceptions import HTTPError

from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class AdminCreationResponseError(Exception):
    """An error (other than HTTPError) occurred while processing Admin Creation API response"""


class Admin(Endpoint):
    """Query the Sectigo Cert Manager REST API for Admin data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/admin", api_version=api_version)

        self.__admins = None
        self.all()

    def all(self, force=False):
        """Return a list of admins from Sectigo.

        :param bool force: If set to True, force refreshing the data from the API

        :return list: A list of dictionaries representing the admins
        """
        if (self.__admins) and (not force):
            return self.__admins

        result = self._client.get(self._api_url)

        self.__admins = result.json()

        return self.__admins

    def create(self, login, email, forename, surname,  # pylint: disable=too-many-arguments
               password, credentials, **kwargs):
        """Create a new administrator

        :param str login: Login name of admin to create
        :param str email: Email of admin to create
        :param str forename: Fore/First name of admin
        :param str surname: Sur/Last name of admin
        :param list credentials: List of Credentials to apply to admin
        :param dict kwargs: Additional fields that will be passed to the API

        Formating for "Credentials" can be found in the Sectigo API Documentation.
        Additional request fields are documented in Sectigo API Documentation
        https://sectigo.com/faqs/detail/Sectigo-Certificate-Manager-SCM-REST-API/kA01N000000XDkE

        Other parameters that may be useful are privileges, identityProviderId, and idpPersonId

        :return dict: The id of the created admin
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
            if status_code == 400:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        # for status >= 400, HTTPError is raised
        if result.status_code != 201:
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

        :param int admin_id: The ID of the admin to query

        return dict: The admin information
        """
        url = self._url(str(admin_id))
        result = self._client.get(url)

        return result.json()

    def get_idps(self):
        """Return a list of IDPs

        :return list: A list of dictionaries representing the IDPs
        """
        url = self._url("idp")
        result = self._client.get(url)

        return result.json()

    def delete(self, admin_id):
        """Delete an admin.

        :param int admin_id: The ID of the admin to delete

        :return bool: Deletion success or failure
        """
        url = self._url(str(admin_id))
        result = self._client.delete(url)

        return result.ok

    def update(self, admin_id, **kwargs):
        """Update an admin.

        :param int admin_id: The ID of the admin to update
        :param dict kwargs: A dictionary of properties to update

        :return bool: Update success or failure
        """
        data = {}
        for key, value in kwargs.items():
            data[key] = value
        url = self._url(str(admin_id))

        try:
            result = self._client.put(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == 400:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.ok
