# -*- coding: utf-8 -*-
"""Define the cert_manager.person.Person unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=no-member

from testtools import TestCase
try:
    from urllib import quote, unquote
except Exception:
    from urllib.parse import quote, unquote

from requests.exceptions import HTTPError
import responses

from cert_manager.person import Person

from .lib.testbase import ClientFixture


class TestPerson(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the Organization class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super(TestPerson, self).setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = "%s/person/v1" % self.cfixt.base_url


class TestInit(TestPerson):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        person = Person(client=self.client)

        self.assertEqual(person._client, self.client)  # pylint: disable=protected-access
        self.assertEqual(person._api_version, "v1")  # pylint: disable=protected-access
        self.assertEqual(person._api_url, self.api_url)  # pylint: disable=protected-access


class TestFind(TestPerson):
    """Test the find method."""

    @responses.activate
    def test_email(self):
        """The function should return the Person ID corresponding to the email passed."""
        # Setup the mocked response
        test_email = "test@example.com"
        quoted_email = quote(test_email.replace(".", "%2E"))
        test_url = self.api_url + "/id/byEmail/" + quoted_email
        test_result = {"personId": 51}

        responses.add(responses.GET, test_url, json=test_result, status=200)

        person = Person(client=self.client)
        data = person.find(email=test_email)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
        self.assertEqual(data, test_result)

    @responses.activate
    def test_not_found(self):
        """The function should raise an HTTPError exception if a person by that email is not found."""
        # Setup the mocked response
        test_email = "test@example.com"
        quoted_email = quote(test_email.replace(".", "%2E"))
        test_url = self.api_url + "/id/byEmail/" + quoted_email
        test_result = {"code": -105, "description": "Person with e-mail: %s was not found" % unquote(quoted_email)}

        responses.add(responses.GET, test_url, json=test_result, status=404)

        person = Person(client=self.client)
        self.assertRaises(HTTPError, person.find, email=test_email)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
