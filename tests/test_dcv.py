"""Define the cert_manager.domain.Domain unit tests."""

# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

import json
from http import HTTPStatus

import responses
from requests.exceptions import HTTPError
from testtools import TestCase

from cert_manager.dcv import DomainControlValidation

from .lib.testbase import ClientFixture


class TestDcv(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the DomainControlValidation class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = f"{self.cfixt.base_url}/dcv/v1/validation"

        # Setup JSON to return in an error
        self.error_response = {"description": "dcv error"}


class TestInit(TestDcv):
    """Test the class initializer."""

    @responses.activate
    def test_param(self):
        """Change the URL if api_version is passed as a parameter."""
        # Set a new version
        version = "v3"
        api_url = f"{self.cfixt.base_url}/dcv/{version}/validation?position=0&size=10&expiresIn=30&department=some_id"

        # Setup the mocked response
        empty_response = "[]"
        responses.add(
            responses.GET,
            api_url,
            body=empty_response,
            status=HTTPStatus.OK,
        )

        dcv = DomainControlValidation(client=self.client, api_version=version)
        data = dcv.search(
            position=0,
            size=10,
            expiresIn=30,
            department="some_id",
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)

        self.assertEqual(data, [])

    def test_need_client(self):
        """Raise an exception when called without a client parameter."""
        self.assertRaises(TypeError, DomainControlValidation)


class TestSearch(TestDcv):
    """Test the .all method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()
        self.params = {
            "position": 0,
            "size": 10,
            "expiresIn": 30,
            "department": "some_id",
        }
        self.api_url = f"{self.cfixt.base_url}/dcv/v1/validation?position=0&size=10&expiresIn=30&department=some_id"
        self.valid_response = [
            {
                "domain": "*.mydomain.org",
                "dcvStatus": "VALIDATED",
                "dcvOrderStatus": "NOT_INITIATED",
                "dcvMethod": "CNAME",
                "expirationDate": "2024-03-19",
            },
            {
                "domain": "mydomain.org",
                "dcvStatus": "VALIDATED",
                "dcvOrderStatus": "NOT_INITIATED",
                "dcvMethod": "CNAME",
                "expirationDate": "2024-03-19",
            },
        ]

    @responses.activate
    def test_search(self):
        """Return all the data, but it should query the API twice."""
        # Setup the mocked response
        responses.add(
            responses.GET, self.api_url, json=self.valid_response, status=HTTPStatus.OK
        )

        dcv = DomainControlValidation(client=self.client)
        data = dcv.search(**self.params)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_bad_http(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.GET,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.BAD_REQUEST,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(HTTPError, domain.search, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestGetValidationStatus(TestDcv):
    """Test the .all method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()
        self.params = {
            "domain": "mydomain.org",
        }
        self.api_url = f"{self.cfixt.base_url}/dcv/v1/validation/status"
        self.valid_response = {
            "status": "EXPIRED",
            "orderStatus": "SUBMITTED",
            "expirationDate": "2020-01-14",
        }

    @responses.activate
    def test_success(self):
        """Return all the data, but it should query the API twice."""
        # Setup the mocked response
        responses.add(
            responses.POST, self.api_url, json=self.valid_response, status=HTTPStatus.OK
        )

        dcv = DomainControlValidation(client=self.client)
        data = dcv.get_validation_status(**self.params)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(
            json.loads(responses.calls[0].request.body)["domain"], "mydomain.org"
        )
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_bad_req(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.POST,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.BAD_REQUEST,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(ValueError, domain.get_validation_status, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)

    @responses.activate
    def test_server_error(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.POST,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(HTTPError, domain.get_validation_status, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestStartValidationCname(TestDcv):
    """Test the .all method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()
        self.params = {
            "domain": "mydomain.org",
        }
        self.api_url = f"{self.cfixt.base_url}/dcv/v1/validation/start/domain/cname"
        self.valid_response = {
            "host": "_916d6634d1728d3a8cfbb3f2cc31bdd0.ccmqa.com.",
            "point": "547a53b84c46e5327bc96cc40832ecc7.7ed2441a319900835df9cfc8326608fd.sectigo.com.",
        }

    @responses.activate
    def test_success(self):
        """Return all the data, but it should query the API twice."""
        # Setup the mocked response
        responses.add(
            responses.POST, self.api_url, json=self.valid_response, status=HTTPStatus.OK
        )

        dcv = DomainControlValidation(client=self.client)
        data = dcv.start_validation_cname(**self.params)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(
            json.loads(responses.calls[0].request.body)["domain"], "mydomain.org"
        )
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_bad_req(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.POST,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.BAD_REQUEST,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(ValueError, domain.start_validation_cname, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)

    @responses.activate
    def test_server_error(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.POST,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(HTTPError, domain.start_validation_cname, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)


class TestSubmitValidationCname(TestDcv):
    """Test the .all method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()
        self.params = {
            "domain": "mydomain.org",
        }
        self.api_url = f"{self.cfixt.base_url}/dcv/v1/validation/submit/domain/cname"
        self.valid_response = {
            "status": "NOT_VALIDATED",
            "orderStatus": "SUBMITTED",
            "message": "DCV status: Not Validated; DCV order status: Submitted",
        }

    @responses.activate
    def test_success(self):
        """Return all the data, but it should query the API twice."""
        # Setup the mocked response
        responses.add(
            responses.POST, self.api_url, json=self.valid_response, status=HTTPStatus.OK
        )

        dcv = DomainControlValidation(client=self.client)
        data = dcv.submit_validation_cname(**self.params)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
        self.assertEqual(
            json.loads(responses.calls[0].request.body)["domain"], "mydomain.org"
        )
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_bad_req(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.POST,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.BAD_REQUEST,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(ValueError, domain.submit_validation_cname, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)

    @responses.activate
    def test_server_error(self):
        """Raise an exception if domains cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(
            responses.POST,
            self.api_url,
            json=self.error_response,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        domain = DomainControlValidation(client=self.client)
        self.assertRaises(HTTPError, domain.submit_validation_cname, **self.params)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.api_url)
