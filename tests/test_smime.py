# -*- coding: utf-8 -*-
"""Define the cert_manager.ssl.SMIME unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=invalid-name

from testtools import TestCase

from cert_manager.smime import SMIME

from .lib.testbase import ClientFixture


# pylint: disable=too-few-public-methods
class TestSMIME(TestCase):
    """Serve as a Base class for all tests of the Certificates class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super(TestSMIME, self).setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        # Set some default values
        self.ep_path = "/smime"
        self.api_version = "v1"
        self.api_url = self.cfixt.base_url + self.ep_path + "/" + self.api_version


class TestInit(TestSMIME):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        end = SMIME(client=self.client)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, self.api_version)
        self.assertEqual(end._api_url, self.api_url)

    def test_version(self):
        """Parameters should be set correctly inside the class with a custom version."""
        version = "v2"
        api_url = self.cfixt.base_url + self.ep_path + "/" + version

        end = SMIME(client=self.client, api_version=version)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, version)
        self.assertEqual(end._api_url, api_url)
