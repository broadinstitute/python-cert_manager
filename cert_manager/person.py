# -*- coding: utf-8 -*-
"""Define the cert_manager.person.Person class."""

import logging
try:
    from urllib import quote
except Exception:
    from urllib.parse import quote

from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class Person(Endpoint):
    """Query the Sectigo Cert Manager REST API for Person data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super(Person, self).__init__(client=client, endpoint="/person", api_version=api_version)

    def find(self, email):
        """Return a list of people with the given email from the Sectigo API.

        :param str email: The email address for which we are searching
        :return list: A list of dictionaries representing the people found
        """
        # Make sure the email is both URL quoted and that "." is encoded as well.
        # This isn't necessary for a URL, but it is apparently necessary for this API.
        #
        # It is also required to replace "." *before* quoting as requests will convert back to the "." unless the
        # "%" is *also* quoted as part of the "quote" function.
        # So, basically: test@test.domain.com -> test%40test%252Edomain%252Ecom
        quoted_email = quote(email.replace(".", "%2E"))

        url = self._url("/id/byEmail/%s" % quoted_email)

        result = self._client.get(url)

        return result.json()
