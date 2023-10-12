"""Define the cert_manager.domain.Domain class."""

import logging
import re

from requests.exceptions import HTTPError

from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class DomainCreationResponseError(Exception):
    """An error (other than HTTPError) occurred while processing Domain Creation API response."""


class Domain(Endpoint):
    """Query the Sectigo Cert Manager REST API for Domain data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/domain", api_version=api_version)

        self.__domains = None

    def all(self, force=False):
        """Return a list of domains from Sectigo.

        :param bool force: If set to True, force refreshing the data from the API

        :return list: A list of dictionaries representing the domains
        """
        if (self.__domains) and (not force):
            return self.__domains

        result = self._client.get(self._api_url)

        self.__domains = result.json()

        return self.__domains

    def find(self, **kwargs):
        """Return a list of domains matching the given parameters from Sectigo.

        :param dict kwargs: A dictonary of parameters that will be passed to the API to execute teh search

        :return list: A list of dictionaries representing the domains that match the given parameters
        """
        result = self._client.get(self._api_url, params=kwargs)

        return result.json()

    def count(self, **kwargs):
        """Return a count of domains matching the given parameters from Sectigo.

        If no parameters are given, the count will be of all domains.

        :return dict: Count of domains matching the given parameters
        """
        url = self._url("/count")
        result = self._client.get(url, params=kwargs)

        return result.json()

    def create(self, name, org_id, cert_types, **kwargs):
        """Create a domain.

        :param str name: Name of domain to create
        :param int org_id: Organization Id to delegate the newly created domain to
        :param list cert_types: Certificate types to delegate, allowed values are "SSL", "SMIME", and "CodeSign"
        :param dict kwargs: A dictionary of additional fields to pass to the API

        :return _type_: _description_
        """
        data = {
            "name": name,
            "delegations": [
                {
                    "orgId": org_id,
                    "certTypes": cert_types
                }
            ]
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
            raise DomainCreationResponseError(f"Unexpected HTTP status {result.status_code}")
        try:
            loc = result.headers["Location"]
            domain_id = re.search(r"/([0-9]+)$", loc)[1]
        # result.headers lookup fails
        except KeyError as exc:
            raise DomainCreationResponseError(
                "Response does not include a Location header"
            ) from exc
        # re.search does not match, at all or the first group
        except (TypeError, IndexError) as exc:
            raise DomainCreationResponseError(
                f"Did not find an Domain ID in Response Location URL: {loc}"
            ) from exc

        return {"id": int(domain_id)}

    def get(self, domain_id):
        """Return a dictionary of domain information.

        :param int domain_id: The ID of the domain to query

        return dict: The domain information
        """
        url = self._url(str(domain_id))
        result = self._client.get(url)

        return result.json()

    def delete(self, domain_id):
        """Delete a domain.

        :param int domain_id: The ID of the domain to delete

        :return bool: Deletion success or failure
        """
        url = self._url(str(domain_id))
        result = self._client.delete(url)

        return result.ok

    def activate(self, domain_id):
        """Activate a domain.

        :param int domain_id: The ID of the domain to activate

        :return bool: activation success or failure
        """
        url = self._url(str(domain_id), "activate")
        result = self._client.put(url)

        return result.ok

    def suspend(self, domain_id):
        """Suspend a domain.

        :param int domain_id: The ID of the domain to suspend

        :return bool: suspension success or failure
        """
        url = self._url(str(domain_id), "suspend")
        result = self._client.put(url)

        return result.ok

    def delegate(self, domain_id, org_id, cert_types):
        """Delegate a domain.

        :param int domain_id: The ID of the domain to delegate
        :param int org_id: The ID of the organization to delegate the domain to
        :param list cert_types: List of certificate types to delegate, allowed values are "SSL", "SMIME", and "CodeSign"

        :return bool: delegation success or failure
        """
        url = self._url(str(domain_id), "delegation")
        data = {
            "orgId": org_id,
            "certTypes": cert_types
        }
        result = self._client.post(url, data=data)

        return result.ok

    def remove_delegation(self, domain_id, org_id, cert_types):
        """Remove a delegation for a domain.

        :param int domain_id: The ID of the domain to remove delegation for
        :param int org_id: The ID of the organization to remove delegation from
        :param list cert_types: List of certificate types to remove delegation for,
        allowed values are "SSL", "SMIME", and "CodeSign"

        :return bool: delegation removal success or failure
        """
        url = self._url(str(domain_id), "delegation")
        data = {
            "orgId": org_id,
            "certTypes": cert_types
        }
        result = self._client.delete(url, data=data)

        return result.ok

    def approve_delegation(self, domain_id, org_id):
        """Approve a requested delegation.

        :param int domain_id: The ID of the domain to approve
        :param int org_id: The ID of the organization requesting the delegation

        :return bool: approval success or failure
        """
        url = self._url(str(domain_id), "delegation", "approve")
        data = {
            "orgId": org_id
        }
        result = self._client.post(url, data=data)

        return result.ok

    def reject_delegation(self, domain_id, org_id):
        """Reject a requested delegation.

        :param int domain_id: The ID of the domain to approve
        :param int org_id: The ID of the organization requesting the delegation

        :return bool: True if request was rejected, False otherwise
        """
        url = self._url(str(domain_id), "delegation", "reject")
        data = {
            "orgId": org_id
        }
        result = self._client.post(url, data=data)

        return result.ok
