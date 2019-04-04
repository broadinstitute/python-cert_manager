# -*- coding: utf-8 -*-
"""Define the cert_manager.organization.Organization unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

# Link below used when digging into double underscore values in objects
# https://stackoverflow.com/questions/9323749/python-check-if-one-dictionary-is-a-subset-of-another-larger-dictionary
#

from requests.exceptions import HTTPError
import responses
from testtools import TestCase

from cert_manager.organization import Organization

from .lib.testbase import ClientFixture


class TestOrganization(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the Organization class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super(TestOrganization, self).setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = "%s/organization/v1" % self.cfixt.base_url

        # Setup a test response one would expect normally
        self.valid_response = [
            {"id": 1234, "name": "Some Organization", "certTypes": [], "departments": [
                {"id": 4321, "name": "Org Unit 1", "certTypes": ["CodeSign", "SMIME", "SSL"]},
                {"id": 4322, "name": "Org Unit 2", "certTypes": ["CodeSign", "SMIME", "SSL"]},
                {"id": 4323, "name": "Org Unit 3", "certTypes": ["CodeSign", "SMIME", "SSL"]},
            ]}]

        # Setup JSON to return in an error
        self.error_response = {"description": "org error"}


class TestInit(TestOrganization):
    """Test the class initializer."""

    @responses.activate
    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)

        self.assertEqual(org._Organization__orgs, self.valid_response)

    @responses.activate
    def test_param(self):
        """The URL should change if api_version is passed as a parameter."""
        # Set a new version
        version = "v3"
        api_url = "%s/organization/%s" % (self.cfixt.base_url, version)

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client, api_version=version)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)

        self.assertEqual(org._Organization__orgs, self.valid_response)

    def test_need_client(self):
        """The class should raise an exception without a client parameter."""
        self.assertRaises(TypeError, Organization)

    @responses.activate
    def test_bad_http(self):
        """The class should raise an HTTPError exception if organizations cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.error_response, status=404)

        self.assertRaises(HTTPError, Organization, client=self.client)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestAll(TestOrganization):
    """Test the .all method."""

    @responses.activate
    def test_cached(self):
        """The function should return all the data, but should not query the API twice."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.all()

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_forced(self):
        """The function should return all the data, but should query the API twice."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.all(force=True)

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(responses.calls[1].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)


class TestFind(TestOrganization):
    """Test the .find method."""

    @responses.activate
    def test_org(self):
        """The function should return all the data about the specified organization name."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find(org_name="Some Organization")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_dept(self):
        """The function should return all the data about the specified department name."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find(dept_name="Org Unit 1")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data[0], self.valid_response[0]["departments"][0])

    @responses.activate
    def test_org_and_dept(self):
        """The function should return department data for department under a specific org."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find(org_name="Some Organization", dept_name="Org Unit 1")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data[0], self.valid_response[0]["departments"][0])

    @responses.activate
    def test_ne_org_and_dept(self):
        """The function should return an empty list if the org name doesn't exist but the department does."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find(org_name="Nonexistent Organization", dept_name="Org Unit 1")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, [])

    @responses.activate
    def test_ne_org(self):
        """The function should return an empty list if the organization name doesn't exist."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find(org_name="Nonexistent Organization")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, [])

    @responses.activate
    def test_ne_dept(self):
        """The function should return an empty list if the department name doesn't exist."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find(dept_name="Nonexistent Department")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, [])

    @responses.activate
    def test_no_params(self):
        """The function should return the entire list of orgs if no parameters are passed."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        org = Organization(client=self.client)
        data = org.find()

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_no_org_depts(self):
        """The function should not error out if the departments field doesn't appear in any orgs."""
        org_data = [
            {"id": 1234, "name": "Some Organization", "certTypes": []},
            {"id": 4321, "name": "Another Organization", "certTypes": []},
            {"id": 9999, "name": "Some Organization", "certTypes": [], "departments": [
                {"id": 8888, "name": "Org Unit 1", "certTypes": ["CodeSign", "SMIME", "SSL"]},
            ]}
        ]
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=org_data, status=200)

        org = Organization(client=self.client)
        data = org.find(dept_name="abc123")

        # Verify all the query information
        # There should only be one call the first time "all" is called in the constructor.
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, [])
