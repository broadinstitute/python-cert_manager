# -*- coding: utf-8 -*-
"""Define some basic classes and functions for use in unit tests."""

import sys

import fixtures

from cert_manager.client import Client
from cert_manager import __version__


class ClientFixture(fixtures.Fixture):
    """Build a fixture for a default cert_manager.client.Client object."""

    def _setUp(self):
        """Setup the Client object and the values used to build the object."""
        # Setup default testing values
        self.base_url = "https://certs.example.com/api"
        self.login_uri = "Testing123"
        self.username = "test_user"
        self.password = "test_password"
        self.user_crt_file = "/path/to/pub.key"
        self.user_key_file = "/path/to/priv.key"

        # This is basically the same code as the code used in Client.  This is used just to lock in the
        # data that the user-agent should have in it.
        ver_info = list(map(str, sys.version_info))
        pyver = ".".join(ver_info[:3])
        self.user_agent = "cert_manager/%s (Python %s)" % (__version__.__version__, pyver)

        # Make a Client object
        self.client = Client(base_url=self.base_url, login_uri=self.login_uri, username=self.username,
                             password=self.password)

        # Headers to check later
        self.headers = {
            "login": self.username,
            "customerUri": self.login_uri,
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

        self.addCleanup(delattr, self, "client")
