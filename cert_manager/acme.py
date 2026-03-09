"""Define the cert_manager.acme.ACMEAccount class."""

import logging
import re

from ._endpoint import Endpoint
from ._helpers import paginate

LOGGER = logging.getLogger(__name__)


class ACMEAccountCreationResponseError(Exception):
    """An error (other than HTTPError) occurred while processing ACME Account Creation API response."""


class ACMEAccount(Endpoint):
    """Query the Sectigo Cert Manager REST API for ACME Account data."""
    _find_params_to_api = {
        "org_id": "organizationId",
        "name": "name",
        "acme_server": "acmeServer",
        "cert_validation_type": "certValidationType",
        "status": "status",
        "size": "size",
        "position": "position",
    }

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        Note: The *all* method will be run on object instantiation to fetch all acme accounts

        Args:
            client: An instantiated cert_manager.Client object
            api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/acme", api_version=api_version)
        self._api_url = self._url("/account")
        self._acme_accounts = None

    def all(self, org_id, force=False):
        """Return a list of acme accounts from Sectigo.

        Args:
            force: If set to True, force refreshing the data from the API
            org_id: The ID of the organization for which to fetch data

        Returns:
            A list of dictionaries representing the acme accounts
        """
        if (self._acme_accounts) and (not force):
            return self._acme_accounts

        self._acme_accounts = []
        result = self.find(org_id)
        for acct in result:
            self._acme_accounts.append(acct)

        return self._acme_accounts

    @paginate
    def find(self, org_id, **kwargs):
        """Return a list of acme accounts matching the parameters.

        Args:
            org_id: The ID of the organization for which to search
            kwargs: A dictionary of additional arguments to pass to the API
                Any other List ACME accounts request parameters can be provided as keyword arguments.

        Returns:
            A list of dictionaries representing the matched acme accounts
        """
        kwargs["org_id"] = org_id
        params = {
            self._find_params_to_api[param]: kwargs.get(param)
            for param in self._find_params_to_api  # pylint:disable=consider-using-dict-items
        }

        result = self._client.get(self._api_url, params=params)

        return result.json()

    def get(self, acme_id):
        """Return a dictionary of acme account information.

        Args:
            acme_id: The ID of the acme account to query

        Returns:
            A dictionary representing the acme account
        """
        url = self._url(str(acme_id))
        result = self._client.get(url)

        return result.json()

    def create(self, name, acme_server, org_id, ev_details=None):
        """Create an acme account.

        Args:
            name: The account name
            acme_server: The acme account server name (URL)
            org_id: The ID of the organization to associate the acme account with
            ev_details: The EV details for the acme account

        Returns:
            A dictionary representing the creation result
        """
        data = {
            "name": name,
            "acmeServer": acme_server,
            "organizationId": org_id,
            "evDetails": ev_details or {}
        }

        result = self._client.post(self._api_url, data=data)

        # for status >= 400, HTTPError is raised
        if result.status_code != self._expected_code:
            raise ACMEAccountCreationResponseError(f"Unexpected HTTP status {result.status_code}")
        try:
            loc = result.headers["Location"]
            acme_id = re.search(r"/([0-9]+)$", loc)[1]
        # result.headers lookup fails
        except KeyError as exc:
            raise ACMEAccountCreationResponseError(
                "Response does not include a Location header"
            ) from exc
        # re.search does not match, at all or the first group
        except (TypeError, IndexError) as exc:
            raise ACMEAccountCreationResponseError(
                f"Did not find an ACME ID in Response Location URL: {loc}"
            ) from exc

        return {"id": int(acme_id)}

    def update(self, acme_id, name):
        """Update an acme account.

        Args:
            acme_id: The ID of the acme account to update
            name: The account name

        Returns:
            Boolean indicating update success or failure
        """
        data = {"name": name}
        url = self._url(str(acme_id))
        result = self._client.put(url, data=data)

        return result.ok

    def delete(self, acme_id):
        """Delete an acme account.

        Args:
            acme_id: The ID of the acme account to delete

        Returns:
            Boolean indicating deletion success or failure
        """
        url = self._url(str(acme_id))
        result = self._client.delete(url)

        return result.ok

    def add_domains(self, acme_id, domains):
        """Add domains to an acme account.

        Args:
            acme_id: The ID of the acme account to add domains to
            domains: The domains to add

        Returns:
            A dictionary containing a list of domains not added
        """
        data = {
            "domains": [
                {"name": domain}
                for domain in domains
            ]
        }
        if self.api_version == "v1":
            url = self._url(f"/{acme_id}/domains")
        else:
            url = self._url(f"/{acme_id}/domain")
        result = self._client.post(url, data=data)

        return result.json()

    def remove_domains(self, acme_id, domains):
        """Remove domains from an acme account.

        Args:
            acme_id: The ID of the acme account to remove domains from
            domains: The domains to remove

        Returns:
            A dictionary containing a list of domains not removed
        """
        data = {
            "domains": [
                {"name": domain}
                for domain in domains
            ]
        }
        url = self._url(f"/{acme_id}/domains")
        # Client().delete does not accept json, so work around it
        result = self._client.session.request("DELETE", url, json=data)
        result.raise_for_status()

        return result.json()
