# -*- coding: utf-8 -*-
"""Define the cert_manager.organization.Organization class."""

import logging

from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class Organization(Endpoint):
    """Query the Sectigo Cert Manager REST API for Organization data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        Note: The *all* method will be run on object instantiation to fetch all organizations

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super(Organization, self).__init__(client=client, endpoint="/organization", api_version=api_version)

        self.__orgs = None
        self.all()

    def all(self, force=False):
        """Return a list of organizations from Sectigo.

        :param bool force: If set to True, force refreshing the data from the API

        :return list: A list of dictionaries representing the organizations
        """
        if (self.__orgs) and (not force):
            return self.__orgs

        result = self._client.get(self._api_url)

        self.__orgs = result.json()

        return self.__orgs

    def find(self, org_name=None, dept_name=None):
        """Return a dictionary of organization information.

        If only an *org_name* is provided, a dictionary representing the organization will be returned if found.

        If only a *dept_name* is provided, all organizations will be searched for that department name, and a
        dictionary representing the department will be returned if found.

        If *both* parameters are provided, the organization specified will be search, and a dictionary representing
        the department will be returned if found.

        If *neither* parameter is provided, all organizations will be returned (i.e. an alias for *all*)

        :param str org_name: The name of the organization for which to search
        :param str org_name: The name of the department for which to search

        :return list: A list of dictionaries representing the organization or department
        """
        ret = {}

        # Use .all to get the data in case it still needs to be fetched
        result = self.all()

        # If we don't search for something, just return everything
        if (not org_name) and (not dept_name):
            return result

        # Start out with everything
        org_data = result
        if org_name:
            # If we are searching for an org name, start out with nothing
            org_data = []
            for res in result:
                # Only add to the org data if we find the org we were looking for
                if res["name"] == org_name:
                    org_data.append(res)

        ret = org_data
        if dept_name:
            ret = []
            # Go through all the remaining orgs
            for org in org_data:
                # If there's no department field, we can't check departments, so move on
                if "departments" not in org:
                    continue

                # Search through all departments for the provided department name
                for dept in org["departments"]:
                    if dept["name"] == dept_name:
                        ret.append(dept)

        return ret
