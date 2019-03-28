# -*- coding: utf-8 -*-
"""Define the cert_manager._endpoint.Endpoint base class."""

import logging

LOGGER = logging.getLogger(__name__)


class Endpoint(object):
    """Act as a superclass for all Sectigo Cert Manager APIs endpoints."""

    def __init__(self, client, endpoint, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string endpoint: The API endpoint you are accessing (for example: "/ssl")
        :param string api_version: The API version to use; the default is "v1"
        """
        self._client = client
        self._api_version = api_version
        self._api_url = self.create_api_url(client.base_url, endpoint, self._api_version)

    @property
    def api_version(self):
        """Return the internal _api_version value."""
        return self._api_version

    @property
    def api_url(self):
        """Return the internal _api_url value."""
        return self._api_url

    @staticmethod
    def create_api_url(base_url, service, version):
        """Build the entire Certificate Manager API URL for the service and version.

        :param str base_url: The base URL you have i.e. for https://hard.cert-manager.com/api/ssl/v1/ the base URL
            would be https://hard.cert-manager.com/api
        :param str service: The API service to use i.e. for https://hard.cert-manager.com/api/ssl/v1/ the service would
            be /ssl
        :param str version: The API version to use i.e. for https://hard.cert-manager.com/api/ssl/v1/ the version would
            be /v1
        :return: The full URL
        :rtype: str
        """
        url = base_url.rstrip("/")
        url += "/" + service.strip("/")
        url += "/" + version.strip("/")
        LOGGER.debug("URL created: %s", url)

        return url

    def _url(self, suffix):
        """Build the endpoint URL based on the API URL inside this object.

        :param str suffix: The suffix of the URL you wish to create i.e. for
            https://hard.cert-manager.com/api/ssl/v1/types the suffix would be /types
        :return str: The full URL
        """
        url = self._api_url.rstrip("/")
        url += "/" + suffix.strip("/")
        LOGGER.debug("URL created: %s", url)

        return url
