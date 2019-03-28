# -*- coding: utf-8 -*-
"""Define the cert_manager.certificates.ssl.SSL class."""

import logging

from ._certificates import Certificates

LOGGER = logging.getLogger(__name__)


class SSL(Certificates):
    """Query the Sectigo Cert Manager REST API for SSL data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super(SSL, self).__init__(client=client, endpoint="/ssl", api_version=api_version)
