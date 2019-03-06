"""Define some basic classes and functions for use in unit tests."""

import fixtures

from cert_manager.client import Client


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

        # Headers to check later
        self.headers = {
            "login": self.username,
            "customerUri": self.login_uri,
            "Accept": "application/json",
        }

        # Make a Client object
        self.client = Client(base_url=self.base_url, login_uri=self.login_uri, username=self.username,
                             password=self.password)

        self.addCleanup(delattr, self, "client")
