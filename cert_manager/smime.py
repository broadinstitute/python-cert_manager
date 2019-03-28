# -*- coding: utf-8 -*-
"""Define the cert_manager.certificates.smime.SMIME class."""

import logging
from ._certificates import Certificates

LOGGER = logging.getLogger(__name__)


class SMIME(Certificates):
    """Query the Sectigo Cert Manager REST API for S/MIME data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super(SMIME, self).__init__(client=client, endpoint="/smime", api_version=api_version)
