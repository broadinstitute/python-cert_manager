# -*- coding: utf-8 -*-
"""Define the cert_manager.certificates.ssl.SSL class."""

import logging

from ._certificates import Certificates
from ._helpers import paginate
from requests.exceptions import HTTPError

from ._helpers import Pending
from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class SSL(Certificates):
    """Query the Sectigo Cert Manager REST API for SSL data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super(SSL, self).__init__(client=client, endpoint="/ssl", api_version=api_version)

    @paginate
    def list(self, **kwargs):
        # size, position, commonName, subjectAlternativeName, status , sslTypeId
        # discoveryStatus, vendor, ordIg, installStatus, renewalStatus, issuer, serialNumber, requester
        # externalRequester, signatureAlgorithm, keyAlgorithm, keySize sha1Hash md5Hash keyUsage extendedKeyUsage
        # requestedVia
        # Status filter. Possible values: 'Invalid', 'Requested', 'Approved', 'Declined', 'Applied', 'Issued', 'Revoked', 'Expired', 'Replaced', 'Rejected', 'Unmanaged', 'SAApproved', 'Init'
        # Discovery status filter. Possible values: 'NotDeployed', 'Deployed'
        # Install status filter. Possible values: 'NOT_SCHEDULED', 'SCHEDULED', 'STARTED', 'SUCCESSFUL', 'FAILED'
        # Renewal status filter. Possible values: 'NOT_SCHEDULED', 'SCHEDULED', 'STARTED', 'SUCCESSFUL', 'FAILED'
        result = self._client.get(self._api_url, params=kwargs)
        return result.json()

    def get(self, cert_id):
        url = self._url("/{}".format(cert_id))
        result = self._client.get(url)
        return result.json()
