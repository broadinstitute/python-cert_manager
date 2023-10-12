"""Define the cert_manager.person.Person unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=no-member

import json
from urllib.parse import quote, unquote

import responses
from requests.exceptions import HTTPError
from testtools import TestCase

from cert_manager.person import Person

from .lib.testbase import ClientFixture


class TestPerson(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the Organization class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = f"{self.cfixt.base_url}/person/v1"


class TestInit(TestPerson):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        person = Person(client=self.client)

        self.assertEqual(person._client, self.client)  # pylint: disable=protected-access
        self.assertEqual(person._api_version, "v1")  # pylint: disable=protected-access
        self.assertEqual(person._api_url, self.api_url)  # pylint: disable=protected-access


class TestList(TestPerson):
    """Test the list method."""

    @responses.activate
    def test_list(self):
        """Return all persons."""
        # Setup the mocked response
        test_url = f"{self.api_url}?size=200&position=0"
        test_result = [
            {"email": "fry@example.org"}, {"email": "leila@example.org"},
            {"email": "farnsworth@example.org"}, {"email": "bender@example.org"}
        ]
        responses.add(responses.GET, test_url, json=test_result, status=200)

        person = Person(client=self.client)
        result = person.list()

        # Verify all the query information
        data = []
        for res in result:
            data.append(res)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
        self.assertEqual(data, test_result)


class TestFind(TestPerson):
    """Test the find method."""

    @responses.activate
    def test_email(self):
        """Return the Person ID corresponding to the email passed."""
        # Setup the mocked response
        test_email = "test@example.com"
        quoted_email = quote(test_email)
        test_url = f"{self.api_url}/id/byEmail/{quoted_email}"
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
        """Raise an HTTPError exception if a person by that email is not found."""
        # Setup the mocked response
        test_email = "test@example.com"
        quoted_email = quote(test_email)
        test_url = f"{self.api_url}/id/byEmail/{quoted_email}"
        test_result = {"code": -105, "description": f"Person with e-mail: {unquote(quoted_email)} was not found"}

        responses.add(responses.GET, test_url, json=test_result, status=404)

        person = Person(client=self.client)
        self.assertRaises(HTTPError, person.find, email=test_email)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)


class TestGet(TestPerson):
    """Test the get details method."""

    @responses.activate
    def test_id(self):
        """Return the details of the Person."""
        # Setup the mocked response
        test_id = 1234
        test_url = f"{self.api_url}/{test_id}"
        test_result = {"firstName": "Fry", "email": "fry@example.org"}
        responses.add(responses.GET, test_url, json=test_result, status=200)

        person = Person(client=self.client)
        data = person.get(test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
        self.assertEqual(data, test_result)

    @responses.activate
    def test_not_found(self):
        """Raise an HTTPError exception if a person with an ID is not found."""
        # Setup the mocked response
        test_id = 1234
        test_url = f"{self.api_url}/{test_id}"
        test_result = {"code": -105, "description": f"Person with ID: {test_id} was not found"}
        responses.add(responses.GET, test_url, json=test_result, status=404)

        person = Person(client=self.client)
        self.assertRaises(HTTPError, person.get, person_id=test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)


class TestCreate(TestPerson):
    """Test the create method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_email = "zoidberg.example.org"
        self.test_first_name = "Dr."
        self.test_last_name = "Zoidberg"
        self.test_org = 1234
        self.test_url = f"{self.api_url}"
        self.test_created_id = 12345
        self.test_result = json.dumps({"personId": str(self.test_created_id)})

    @responses.activate
    def test_create_success(self):
        """Return a JSON with the `personID` of the person created if a 201 response is given."""
        responses.add(
            responses.POST,
            self.test_url,
            body=self.test_result,
            status=201,
            headers={"Location": f"https://cert-manager.com/api/person/v1/{self.test_created_id}"}
        )

        person = Person(client=self.client)
        data = person.create(
            first_name=self.test_first_name,
            last_name=self.test_last_name,
            email=self.test_email,
            org_id=self.test_org,
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(json.dumps(data), self.test_result)


class TestUpdate(TestPerson):
    """Test the update method."""

    @responses.activate
    def test_update_success(self):
        """Return nothing when updating a person."""
        test_id = 1234
        test_url = f"{self.api_url}/{test_id}"
        responses.add(responses.PUT, test_url, status=200)

        person = Person(client=self.client)
        person.update(
            person_id=test_id,
            validation_type="HIGH",
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)


class TestDelete(TestPerson):
    """Test the delete method."""

    @responses.activate
    def test_delete_success(self):
        """Return nothing when deleting a person."""
        test_id = 1234
        test_url = f"{self.api_url}/{test_id}"
        responses.add(responses.DELETE, test_url, status=200)

        person = Person(client=self.client)
        person.delete(
            person_id=test_id,
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
