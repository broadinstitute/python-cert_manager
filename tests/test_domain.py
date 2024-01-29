"""Define the cert_manager.domain.Domain unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

import json

import responses
from requests.exceptions import HTTPError
from testtools import TestCase

from cert_manager.domain import Domain, DomainCreationResponseError

from .lib.testbase import ClientFixture


class TestDomain(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the Domain class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = f"{self.cfixt.base_url}/domain/v1"

        # Setup a test response one would expect normally
        self.valid_response = [
            {"id": 1234, "name": "example.com"},
            {"id": 4321, "name": "*.example.com"},
            {"id": 4322, "name": "subdomain.example.com"},
        ]

        # Setup a test response for getting a specific Domain
        self.valid_individual_response = self.valid_response[0]
        self.valid_individual_response["status"] = "Active"

        # Setup JSON to return in an error
        self.error_response = {"description": "domain error"}


class TestInit(TestDomain):
    """Test the class initializer."""

    @responses.activate
    def test_param(self):
        """Change the URL if api_version is passed as a parameter."""
        # Set a new version
        version = "v3"
        api_url = f"{self.cfixt.base_url}/domain/{version}"

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.valid_response, status=200)

        domain = Domain(client=self.client, api_version=version)
        data = domain.all()

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)

        self.assertEqual(data, self.valid_response)

    def test_need_client(self):
        """Raise an exception when called without a client parameter."""
        self.assertRaises(TypeError, Domain)


class TestAll(TestDomain):
    """Test the .all method."""

    @responses.activate
    def test_cached(self):
        """Return all the data, but it should not query the API twice."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        domain = Domain(client=self.client)
        data = domain.all()
        data = domain.all()

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_forced(self):
        """Return all the data, but it should query the API twice."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        domain = Domain(client=self.client)
        data = domain.all()
        data = domain.all(force=True)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(responses.calls[1].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_bad_http(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.error_response, status=400)

        domain = Domain(client=self.client)
        self.assertRaises(HTTPError, domain.all)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestFind(TestDomain):
    """Test the .find method."""

    @responses.activate
    def test_no_params(self):
        """Return all domains when called without parameters."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        domain = Domain(client=self.client)
        data = domain.find()

        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_params(self):
        """Parameters will be passed to API."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response[0], status=200)

        api_url = f"{self.api_url}?name=example.com"
        domain = Domain(client=self.client)
        data = domain.find(name="example.com")

        # Verify all the query information

        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_response[0])

    @responses.activate
    def test_bad_http(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.error_response, status=400)

        domain = Domain(client=self.client)
        self.assertRaises(HTTPError, domain.find)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestCount(TestDomain):
    """Test the .count method."""

    @responses.activate
    def test_no_params(self):
        """Return the count of all domains when called without parameters."""
        # Setup the mocked response
        count = {"count": len(self.valid_response)}
        api_url = f"{self.api_url}/count"
        responses.add(responses.GET, api_url, json=count, status=200)

        domain = Domain(client=self.client)
        data = domain.count()

        self.assertEqual(data, count)
        self.assertEqual(responses.calls[0].request.url, api_url)

    @responses.activate
    def test_params(self):
        """Parameters will be passed to API."""
        # Setup the mocked response
        count = {"count": len(self.valid_response[0])}
        api_url = f"{self.api_url}/count"
        responses.add(responses.GET, api_url, json=count, status=200)

        domain = Domain(client=self.client)
        data = domain.count(name="example.com")

        # Verify all the query information
        self.assertEqual(responses.calls[0].request.url, f"{api_url}?name=example.com")
        self.assertEqual(data, count)

    @responses.activate
    def test_bad_http(self):
        """Raise an HTTPError exception if counts cannot be retrieved from the API."""
        # Setup the mocked response
        api_url = f"{self.api_url}/count"
        responses.add(responses.GET, api_url, json=self.error_response, status=400)

        domain = Domain(client=self.client)
        self.assertRaises(HTTPError, domain.count)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)


class TestGet(TestDomain):
    """Test the .get method."""

    @responses.activate
    def test_need_domain_id(self):
        """Raise an exception without an domain_id parameter."""
        domain = Domain(client=self.client)
        self.assertRaises(TypeError, domain.get)

    @responses.activate
    def test_domain_id(self):
        """Return data about the specified Domain ID."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}"

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.valid_individual_response, status=200)

        domain = Domain(client=self.client)
        data = domain.get(domain_id)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_individual_response)

    @responses.activate
    def test_ne_domain_id(self):
        """Raise an HTTPError exception if the specified Domain ID does not exist."""
        domain_id = 2345
        api_url = f"{self.api_url}/{str(domain_id)}"

        # Setup the mocked response
        responses.add(responses.GET, api_url, status=404)

        domain = Domain(client=self.client)
        self.assertRaises(HTTPError, domain.get, domain_id)


class TestCreate(TestDomain):
    """Test the .create method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # Not going to check every permutation of missing parameters,
        # but verify that something is required
        self.assertRaises(TypeError, domain.create)

    @responses.activate
    def test_create_success(self):
        """Return the created domain ID, as well as add all parameters to the request body."""
        # Setup the mocked response
        domain_id = 1234
        org_id = 4321
        types = ["SSL"]
        location = f"{self.api_url}/{str(domain_id)}"
        responses.add(responses.POST, self.api_url, headers={"Location": location}, status=201)

        domain = Domain(client=self.client)
        post_data = {
            "name": "sub2.example.com",
            "delegations": [{"orgId": org_id, "certTypes": types}]
        }
        response = domain.create("sub2.example.com", org_id, types)

        self.assertEqual(response, {"id": domain_id})
        self.assertEqual(responses.calls[0].request.body, json.dumps(post_data).encode("utf8"))

    @responses.activate
    def test_create_success_optional_params(self):
        """Return the created domain ID when additional params are specified.

        Also, add the non-required parameters to the request body.
        """
        # Setup the mocked response
        domain_id = 1234
        location = f"{self.api_url}/{str(domain_id)}"
        responses.add(responses.POST, self.api_url, headers={"Location": location}, status=201)

        domain = Domain(client=self.client)
        post_data = {
            "name": "sub2.example.com",
            "delegations": [{"orgId": 4321, "certTypes": ["SSL"]}],
            "description": "Example sub domain"
        }
        response = domain.create("sub2.example.com", 4321, ["SSL"], description="Example sub domain")

        self.assertEqual(response, {"id": domain_id})
        self.assertEqual(responses.calls[0].request.body, json.dumps(post_data).encode("utf8"))

    @responses.activate
    def test_create_failure_http_error(self):
        """Return an error code and description if the Domain creation failed."""
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      status=400)

        domain = Domain(client=self.client)

        create_args = {
            "name": "sub2.example.com",
            "org_id": 4321,
            "cert_types": ["other"]
        }
        self.assertRaises(ValueError, domain.create, **create_args)

    @responses.activate
    def test_create_failure_http_status_unexpected(self):
        """Raise an exception if the Domain creation fails with unexpected http code."""
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      status=200)

        domain = Domain(client=self.client)

        create_args = {
            "name": "sub2.example.com",
            "org_id": 4321,
            "cert_types": ["SSL"]
        }
        self.assertRaises(DomainCreationResponseError, domain.create, **create_args)

    @responses.activate
    def test_create_failure_missing_location_header(self):
        """Raise an exception if the Domain creation fails due to no Location header in response."""
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, status=201)

        domain = Domain(client=self.client)

        create_args = {
            "name": "sub2.example.com",
            "org_id": 4321,
            "cert_types": ["SSL"]
        }
        self.assertRaises(DomainCreationResponseError, domain.create, **create_args)

    @responses.activate
    def test_create_failure_domain_id_not_found(self):
        """Raise an exception if the Domain creation fails because Domain ID not found in response."""
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, headers={"Location": "not a url"}, status=201)

        domain = Domain(client=self.client)

        create_args = {
            "name": "sub2.example.com",
            "org_id": 4321,
            "cert_types": ["SSL"]
        }
        self.assertRaises(DomainCreationResponseError, domain.create, **create_args)


class TestDelete(TestDomain):
    """Test the .delete method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.delete)

    @responses.activate
    def test_delete_success(self):
        """Return True if the deletion succeeded."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}"

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.delete(domain_id)

        self.assertEqual(True, response)

    @responses.activate
    def test_delete_failure_http_error(self):
        """Raise an HTTPError exception if the deletion failed."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}"

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.delete, domain_id)


class TestActivate(TestDomain):
    """Test the .activate method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.activate)

    @responses.activate
    def test_activate_success(self):
        """Return True if the activation succeeded."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}/activate"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.activate(domain_id)

        self.assertEqual(True, response)

    @responses.activate
    def test_activate_failure_http_error(self):
        """Raise an HTTPError exception if the deletion failed."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}/activate"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.activate, domain_id)


class TestSuspend(TestDomain):
    """Test the .suspend method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.suspend)

    @responses.activate
    def test_suspend_success(self):
        """Return True if the suspension succeeded."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}/suspend"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.suspend(domain_id)

        self.assertEqual(True, response)

    @responses.activate
    def test_suspend_failure_http_error(self):
        """Raise an HTTPError exception if the suspension failed."""
        domain_id = 1234
        api_url = f"{self.api_url}/{str(domain_id)}/suspend"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.suspend, domain_id)


class TestDelegate(TestDomain):
    """Test the .delegate method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.delegate)

    @responses.activate
    def test_delegate_success(self):
        """Return True if the delegation succeeded."""
        domain_id = 1234
        org_id = 4321
        types = ["SSL"]
        api_url = f"{self.api_url}/{str(domain_id)}/delegation"

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.delegate(domain_id, org_id, types)
        post_data = {
            "orgId": org_id,
            "certTypes": types
        }

        self.assertEqual(True, response)
        self.assertEqual(responses.calls[0].request.body, json.dumps(post_data).encode("utf8"))

    @responses.activate
    def test_delegate_failure_http_error(self):
        """Raise an HTTPError exception if the delegation failed."""
        domain_id = 1234
        org_id = 4321
        types = ["SSL"]
        api_url = f"{self.api_url}/{str(domain_id)}/delegation"

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.delegate, domain_id, org_id, types)


class TestRemoveDelegation(TestDomain):
    """Test the .remove_delegation method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.remove_delegation)

    @responses.activate
    def test_remove_delegation_success(self):
        """Return True if the delegation removal succeeded."""
        domain_id = 1234
        org_id = 4321
        types = ["SSL"]
        api_url = f"{self.api_url}/{str(domain_id)}/delegation"

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.remove_delegation(domain_id, org_id, types)
        post_data = {
            "orgId": org_id,
            "certTypes": types
        }

        self.assertEqual(True, response)
        self.assertEqual(responses.calls[0].request.body, json.dumps(post_data).encode("utf8"))

    @responses.activate
    def test_remove_delegation_failure_http_error(self):
        """Raise an HTTPError exception if the delegation removal failed."""
        domain_id = 1234
        org_id = 4321
        types = ["SSL"]
        api_url = f"{self.api_url}/{str(domain_id)}/delegation"

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.remove_delegation, domain_id, org_id, types)


class TestApproveDelegation(TestDomain):
    """Test the .approve_delegation method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.approve_delegation)

    @responses.activate
    def test_approve_delegation_success(self):
        """Return True if the approval succeeded."""
        domain_id = 1234
        org_id = 4321
        api_url = f"{self.api_url}/{str(domain_id)}/delegation/approve"

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.approve_delegation(domain_id, org_id)
        post_data = {
            "orgId": org_id,
        }

        self.assertEqual(True, response)
        self.assertEqual(responses.calls[0].request.body, json.dumps(post_data).encode("utf8"))

    @responses.activate
    def test_approval_failure_http_error(self):
        """Raise an HTTPError exception if the approval failed."""
        domain_id = 1234
        org_id = 4321
        api_url = f"{self.api_url}/{str(domain_id)}/delegation/approve"

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.approve_delegation, domain_id, org_id)


class TestRejectDelegation(TestDomain):
    """Test the .reject_delegation method."""

    @responses.activate
    def test_need_params(self):
        """Raise an exception when called without required parameters."""
        domain = Domain(client=self.client)
        # missing domain_id
        self.assertRaises(TypeError, domain.reject_delegation)

    @responses.activate
    def test_reject_delegation_success(self):
        """Return True if the rejection succeeded."""
        domain_id = 1234
        org_id = 4321
        api_url = f"{self.api_url}/{str(domain_id)}/delegation/reject"

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=200)

        domain = Domain(client=self.client)
        response = domain.reject_delegation(domain_id, org_id)
        post_data = {
            "orgId": org_id,
        }

        self.assertEqual(True, response)
        self.assertEqual(responses.calls[0].request.body, json.dumps(post_data).encode("utf8"))

    @responses.activate
    def test_reject_failure_http_error(self):
        """Raise an HTTPError exception if the rejection failed."""
        domain_id = 1234
        org_id = 4321
        api_url = f"{self.api_url}/{str(domain_id)}/delegation/reject"

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=404)

        domain = Domain(client=self.client)

        self.assertRaises(HTTPError, domain.reject_delegation, domain_id, org_id)
