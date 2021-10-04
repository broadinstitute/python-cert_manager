# -*- coding: utf-8 -*-
"""Define the cert_manager.certificates.ssl.SSL class."""

import logging

from ._certificates import Certificates
from ._helpers import paginate

LOGGER = logging.getLogger(__name__)


class SSL(Certificates):
    """Query the Sectigo Cert Manager REST API for SSL data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/ssl", api_version=api_version)

    @paginate
    def list(self, **kwargs):
        """Return a list of all certificates from Sectigo.

        The 'size' and 'position' parameters passed as arguments to this function will be used
        by the pagination wrapper to page through results.  All other filtering parameters can be
        referenced at:
        https://sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resource-SSL-list

        :param dict kwargs: A dictionary of arguments to pass to the API

        :return iter: An iterator object is returned to cycle through the certificates
        """
        result = self._client.get(self._api_url, params=kwargs)

        return result.json()

    def get(self, cert_id):
        """Retrieve a certificate corresponding to the given certificate ID."""
        url = self._url(f"/{cert_id}")
        result = self._client.get(url)

        return result.json()
