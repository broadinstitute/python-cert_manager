# -*- coding: utf-8 -*-
"""Define the cert_manager.admin.Admin unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

import json

from requests.exceptions import HTTPError
from testtools import TestCase

import responses

from cert_manager.admin import Admin, AdminCreationResponseError

from .lib.testbase import ClientFixture


class TestAdmin(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the Admin class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = f"{self.cfixt.base_url}/admin/v1"

        # Setup a test response one would expect normally
        self.valid_response = [
            {
                'id': 1234, 'login': 'user1@example.com', 'forename': 'Test1',
                'surname': 'User1', 'email': 'user1@example.com'
            },
            {
                'id': 4321, 'login': 'user2@example.com', 'forename': 'Test2',
                'surname': 'User2', 'email': 'user2@example.com'
            },
            {
                'id': 4322, 'login': 'user3', 'forename': 'Test3',
                'surname': 'User3', 'email': 'user3@example.com'
            }
        ]

        # Setup a test response for getting a specific Admin
        self.valid_individual_response = self.valid_response[0]
        self.valid_individual_response['status'] = "Active"

        # Setup a test response for IDPs
        self.valid_idp_response = [
            {'id': 12, 'name': 'Example IDP 1'},
            {'id': 34, 'name': 'Example IDP 2'}
        ]

        # Setup JSON to return in an error
        self.error_response = {"description": "admin error"}


class TestInit(TestAdmin):
    """Test the class initializer."""

    @responses.activate
    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)

        self.assertEqual(admin._Admin__admins, self.valid_response)

    @responses.activate
    def test_param(self):
        """The URL should change if api_version is passed as a parameter."""
        # Set a new version
        version = "v3"
        api_url = f"{self.cfixt.base_url}/admin/{version}"

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client, api_version=version)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)

        self.assertEqual(admin._Admin__admins, self.valid_response)

    def test_need_client(self):
        """The class should raise an exception without a client parameter."""
        self.assertRaises(TypeError, Admin)

    @responses.activate
    def test_bad_http(self):
        """The function should raise an HTTPError exception if admin accounts cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.error_response, status=400)

        self.assertRaises(HTTPError, Admin, client=self.client)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestAll(TestAdmin):
    """Test the .all method."""

    @responses.activate
    def test_cached(self):
        """The function should return all the data, but should not query the API twice."""
        # Setup the mocked response, refrain from matching the query string
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client)
        data = admin.all()

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_forced(self):
        """The function should return all the data, but should query the API twice."""
        # Setup the mocked response, refrain from matching the query string
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client)
        data = admin.all(force=True)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(responses.calls[1].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)


class TestGet(TestAdmin):
    """Test the .get method."""

    @responses.activate
    def test_need_admin_id(self):
        """The function should raise an exception without an admin_id parameter."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        admin = Admin(client=self.client)
        self.assertRaises(TypeError, admin.get)

    @responses.activate
    def test_admin_id(self):
        """The function should return data about the specified Admin ID."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 1234
        api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.valid_individual_response, status=200)

        admin = Admin(client=self.client)
        data = admin.get(admin_id)

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[1].request.url, api_url)
        self.assertEqual(data, self.valid_individual_response)

    @responses.activate
    def test_ne_admin_id(self):
        """The function should raise an HTTPError exception if the specified Admin ID does not exist."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 2345
        api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.GET, api_url, status=404)

        admin = Admin(client=self.client)
        self.assertRaises(HTTPError, admin.get, admin_id)


class TestGetIdps(TestAdmin):
    """Test the .get_idps method."""

    @responses.activate
    def test_get(self):
        """The function should return all IDPs."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        api_url = f"{self.api_url}/idp"

        responses.add(responses.GET, api_url, json=self.valid_idp_response, status=200)

        admin = Admin(client=self.client)
        data = admin.get_idps()

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[1].request.url, api_url)
        self.assertEqual(data, self.valid_idp_response)

        responses.add(responses.GET, self.api_url, json=self.error_response, status=400)

    @responses.activate
    def test_get_http_failure(self):
        """The function should raise an HTTPError exception if IDPs cannot be retrieved from the API."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        api_url = f"{self.api_url}/idp"

        responses.add(responses.GET, api_url, json=self.error_response, status=400)

        admin = Admin(client=self.client)

        self.assertRaises(HTTPError, admin.get_idps)


class TestCreate(TestAdmin):
    """Test the .create method."""

    @responses.activate
    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters.
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client)
        # Not going to check every permutation of missing parameters,
        # but verify that something is required
        self.assertRaises(TypeError, admin.create)

    @responses.activate
    def test_create_success(self):
        """
        The function should return the created admin ID,
        as well as add all parameters to the request body
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        # Setup the mocked response
        admin_id = 1234
        location = f"{self.api_url}/{str(admin_id)}"
        responses.add(responses.POST, self.api_url, headers={'Location': location}, status=201)

        admin = Admin(client=self.client)
        post_data = {
            'login': 'user1@example.com',
            'email': 'user1@example.com',
            'forename': 'Test1',
            'surname': 'User1',
            'password': 'password',
            'credentials': [{'role': 'DRAO_SSL', "orgId": 123}],
        }
        response = admin.create(**post_data)

        self.assertEqual(response, {"id": admin_id})
        self.assertEqual(responses.calls[1].request.body, json.dumps(post_data).encode('utf8'))

    @responses.activate
    def test_create_success_optional_params(self):
        """
        The function should return the created admin ID when additional params are specified,
        as well add the non-required parameters to the request body
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        # Setup the mocked response
        admin_id = 1234
        location = f"{self.api_url}/{str(admin_id)}"
        responses.add(responses.POST, self.api_url, headers={'Location': location}, status=201)

        admin = Admin(client=self.client)
        post_data = {
            'login': 'user1@example.com',
            'email': 'user1@example.com',
            'forename': 'Test1',
            'surname': 'User1',
            'password': '',
            'credentials': [{'role': 'DRAO_SSL', "orgId": 123}],
            'identityProviderId': 12,
            'idpPersonId': 'user1@example.com'
        }
        response = admin.create(**post_data)

        self.assertEqual(response, {"id": admin_id})
        self.assertEqual(responses.calls[1].request.body, json.dumps(post_data).encode('utf8'))

    @responses.activate
    def test_create_failure_http_error(self):
        """
        The function should return an error code and description if the Admin
        creation failed.
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      status=400)

        admin = Admin(client=self.client)

        create_args = {
            'login': 'user1@example.com',
            'email': 'user1',  # This would be a malformed email and would throw a 400 error from the API
            'forename': 'Test1',
            'surname': 'User1',
            'password': 'password',
            'credentials': [{'role': 'DRAO_SSL', "orgId": 123}],
        }
        self.assertRaises(ValueError, admin.create, **create_args)

    @responses.activate
    def test_create_failure_http_status_unexpected(self):
        """
        The function should return an error code and description if the Admin
        creation failed with AdminCreationResponseError
        (unexpected HTTP status code).
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      status=200)

        admin = Admin(client=self.client)

        create_args = {
            'login': 'user1@example.com',
            'email': 'user1@example.com',
            'forename': 'Test1',
            'surname': 'User1',
            'password': 'password',
            'credentials': [{'role': 'DRAO_SSL', "orgId": 123}],
        }
        self.assertRaises(AdminCreationResponseError, admin.create, **create_args)

    @responses.activate
    def test_create_failure_missing_location_header(self):
        """
        The function should return an error code and description if the Admin
        creation failed with AdminCreationResponseError
        (no Location header in response).
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, status=201)

        admin = Admin(client=self.client)

        create_args = {
            'login': 'user1@example.com',
            'email': 'user1@example.com',
            'forename': 'Test1',
            'surname': 'User1',
            'password': 'password',
            'credentials': [{'role': 'DRAO_SSL', "orgId": 123}],
        }
        self.assertRaises(AdminCreationResponseError, admin.create, **create_args)

    @responses.activate
    def test_create_failure_admin_id_not_found(self):
        """
        The function should return an error code and description if the Admin
        creation failed with AdminCreationResponseError
        (Admin ID not found in response).
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)
        # Setup the mocked response
        responses.add(responses.POST, self.api_url, headers={'Location': 'not a url'}, status=201)

        admin = Admin(client=self.client)

        create_args = {
            'login': 'user1@example.com',
            'email': 'user1@example.com',
            'forename': 'Test1',
            'surname': 'User1',
            'password': 'password',
            'credentials': [{'role': 'DRAO_SSL', "orgId": 123}],
        }
        self.assertRaises(AdminCreationResponseError, admin.create, **create_args)


class TestDelete(TestAdmin):
    """Test the .delete method."""

    @responses.activate
    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters.
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client)
        # missing admin_id
        self.assertRaises(TypeError, admin.delete)

    @responses.activate
    def test_delete_success(self):
        """The function should return True if the deletion succeeded."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 1234
        api_url = api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=204)

        admin = Admin(client=self.client)
        response = admin.delete(admin_id)

        self.assertEqual(True, response)

    @responses.activate
    def test_delete_failure_http_error(self):
        """
        The function should raise an HTTPError exception if the deletion
        failed.
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 1234
        api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=404)

        admin = Admin(client=self.client)

        self.assertRaises(HTTPError, admin.delete, admin_id)


class TestUpdate(TestAdmin):
    """Test the .update method."""

    @responses.activate
    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters.
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin = Admin(client=self.client)
        # missing admin_id
        self.assertRaises(TypeError, admin.update)

    @responses.activate
    def test_update_success(self):
        """The function should return True if the update succeeded."""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 1234
        api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=200)

        admin = Admin(client=self.client)
        response = admin.update(admin_id)

        self.assertEqual(True, response)

    @responses.activate
    def test_update_body_success(self):
        """Additional **kwargs should be added to request body"""

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 1234
        api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=200)

        admin = Admin(client=self.client)

        post_data = {
            'forename': 'Test1',
            'surname': 'User1',
        }
        response = admin.update(admin_id, **post_data)

        self.assertEqual(True, response)
        self.assertEqual(responses.calls[1].request.body, json.dumps(post_data).encode('utf8'))

    @responses.activate
    def test_update_failure_http_error(self):
        """
        The function should return an error code and description if the Admin
        creation failed.
        """

        # Setup the mocked response when class is initialized
        responses.add(responses.GET, self.api_url, json=self.valid_response, status=200)

        admin_id = 1234
        api_url = f"{self.api_url}/{str(admin_id)}"

        # Setup the mocked response
        responses.add(responses.PUT, api_url, json=self.error_response, status=400)

        admin = Admin(client=self.client)

        update_args = {'email': 'user1@example.com'}  # This malformed email would return an error from the API

        self.assertRaises(ValueError, admin.update, admin_id, **update_args)
