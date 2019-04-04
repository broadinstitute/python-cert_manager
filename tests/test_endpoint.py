# -*- coding: utf-8 -*-
"""Define the cert_manager._endpoint.Endpoint unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=invalid-name

from testtools import TestCase

from cert_manager._endpoint import Endpoint

from .lib.testbase import ClientFixture


# pylint: disable=too-few-public-methods
class TestEndpoint(TestCase):
    """Serve as a Base class for all tests of the Endpoint class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super(TestEndpoint, self).setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        # Set some default values
        self.ep_path = "/test"
        self.api_version = "v1"
        self.api_url = self.cfixt.base_url + self.ep_path + "/" + self.api_version


class TestInit(TestEndpoint):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        end = Endpoint(client=self.client, endpoint=self.ep_path)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, self.api_version)
        self.assertEqual(end._api_url, self.api_url)

    def test_version(self):
        """Parameters should be set correctly inside the class with a custom version."""
        version = "v2"
        api_url = self.cfixt.base_url + self.ep_path + "/" + version

        end = Endpoint(client=self.client, endpoint=self.ep_path, api_version=version)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, version)
        self.assertEqual(end._api_url, api_url)


class TestProperties(TestEndpoint):
    """Test the class properties."""

    def test_api_version(self):
        """Return the internal _api_version value."""
        end = Endpoint(client=self.client, endpoint=self.ep_path)

        # Make sure the values match
        self.assertEqual(end.api_version, self.api_version)

    def test_api_url(self):
        """Return the internal _api_url value."""
        end = Endpoint(client=self.client, endpoint=self.ep_path)

        # Make sure the values match
        self.assertEqual(end.api_url, self.api_url)


class TestCreateApiUrl(TestEndpoint):
    """Test the create_api_url static function."""

    def test_normal(self):
        """Return the API URL when called with correct parameters."""
        url = Endpoint.create_api_url(self.cfixt.base_url, self.ep_path, self.api_version)

        # Make sure the values match
        self.assertEqual(url, self.api_url)

    def test_extra_slashes(self):
        """Return a clean API URL when called with parameters containing extra slashes."""
        url = Endpoint.create_api_url(
            self.cfixt.base_url + "///", "//" + self.ep_path, "////" + self.api_version
        )

        # Make sure the values match
        self.assertEqual(url, self.api_url)


class TestUrl(TestEndpoint):
    """Test the _url function."""

    def test_normal(self):
        """Return the full API URL when called with correct parameters."""
        end = Endpoint(client=self.client, endpoint=self.ep_path)

        suffix = "/help"
        url = self.api_url + suffix

        # Make sure the values match
        self.assertEqual(end._url(suffix), url)

    def test_no_slashes(self):
        """Return the full API URL when called with a suffix with no slash."""
        end = Endpoint(client=self.client, endpoint=self.ep_path)

        suffix = "help"
        url = self.api_url + "/" + suffix

        # Make sure the values match
        self.assertEqual(end._url(suffix), url)

    def test_many_slashes(self):
        """Return the full API URL when called with a suffix with too many slashes."""
        end = Endpoint(client=self.client, endpoint=self.ep_path)

        suffix = "//help///"
        url = self.api_url + "/help"

        # Make sure the values match
        self.assertEqual(end._url(suffix), url)
