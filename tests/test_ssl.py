# -*- coding: utf-8 -*-
"""Define the cert_manager.ssl.SSL unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=invalid-name

from testtools import TestCase

from requests.exceptions import HTTPError
import responses

from cert_manager.ssl import SSL

from .lib.testbase import ClientFixture


# pylint: disable=too-few-public-methods
class TestSSL(TestCase):
    """Serve as a Base class for all tests of the Certificates class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        # Set some default values
        self.ep_path = "/ssl"
        self.api_version = "v1"
        self.api_url = f"{self.cfixt.base_url}{self.ep_path}/{self.api_version}"


class TestInit(TestSSL):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        end = SSL(client=self.client)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, self.api_version)
        self.assertEqual(end._api_url, self.api_url)

    def test_version(self):
        """Parameters should be set correctly inside the class with a custom version."""
        version = "v2"
        api_url = f"{self.cfixt.base_url}{self.ep_path}/{version}"

        end = SSL(client=self.client, api_version=version)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, version)
        self.assertEqual(end._api_url, api_url)


class TestGet(TestSSL):
    """Test the class get method."""

    def test_defaults(self):
        """The function should raise an exception when no cert_id is passed."""
        # Setup the mocked response
        ssl = SSL(client=self.client)
        self.assertRaises(TypeError, ssl.get)

    @responses.activate
    def test_cert(self):
        """The function should return the record for the cert_id passed."""
        # Setup the mocked response
        cert_id = "1234567"
        test_url = f"{self.api_url}/{cert_id}"
        test_result = {"commonName": "test.example.org"}

        responses.add(responses.GET, test_url, json=test_result, status=200)

        ssl = SSL(client=self.client)
        data = ssl.get(cert_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
        self.assertEqual(data, test_result)

    @responses.activate
    def test_no_cert(self):
        """The function should raise an exception when the cert_id doesn't exist."""
        # Setup the mocked response
        cert_id = "1234567"
        test_url = f"{self.api_url}/{cert_id}"
        test_result = {"commonName": "test.example.org"}

        responses.add(responses.GET, test_url, json=test_result, status=400)

        ssl = SSL(client=self.client)
        self.assertRaises(HTTPError, ssl.get, cert_id)


class TestList(TestSSL):
    """Test the class list method."""

    @responses.activate
    def test_defaults(self):
        """The function should return all certificate records."""
        # Setup the mocked response
        test_url = f"{self.api_url}?size=200&position=0"
        test_result = [
            {"commonName": "test.example.org"}, {"commonName": "test2.example.org"},
            {"commonName": "test3.example.org"}, {"commonName": "test4.example.org"},
        ]

        responses.add(responses.GET, test_url, json=test_result, status=200)

        ssl = SSL(client=self.client)
        result = ssl.list()

        # Verify all the query information
        data = []
        for res in result:
            data.append(res)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
        self.assertEqual(data, test_result)


class TestRenew(TestSSL):
    """Test the renew method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_id = 1234
        self.test_url = f"{self.api_url}/renewById/{self.test_id}"
        # Create an SSL object to use in any tests that need one
        self.certobj = SSL(client=self.client)

    @responses.activate
    def test_success(self):
        """It should return JSON if a 200-level status code is returned with data."""
        # Setup the mocked responses
        responses.add(responses.POST, self.test_url, json={}, status=204)

        # Call the function
        resp = self.certobj.renew(cert_id=self.test_id)

        # Verify all the query information
        self.assertEqual(resp, {})
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, json={}, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.certobj.renew, self.test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestCount(TestSSL):
    """Test the count method."""

    @responses.activate
    def test_defaults(self):
        """The function should return all certificate records."""
        # Setup the mocked response
        test_url = f"{self.api_url}"
        count = 10
        responses.add(responses.HEAD, test_url, headers={'X-Total-Count': str(count)}, status=200)
        responses.add(responses.HEAD, test_url, headers={'X-Total-Count': str(count * 2)}, status=200)

        ssl = SSL(client=self.client)
        result = ssl.count()

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(result, count)

        result = ssl.count(status='Applied')

        # Verify all the query information
        self.assertEqual(result, count * 2)
