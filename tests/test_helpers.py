"""Define the cert_manager._helpers.traffic_log wrapper function unit tests."""
# Because pylint can't figure out how requests does some magic things
# pylint: disable=no-member

import json
import logging
import types
from unittest import mock

import requests
import responses
from testtools import TestCase

from cert_manager._helpers import paginate, traffic_log


class TestPaginate(TestCase):
    """Tests for the cert_manager._helpers.paginate wrapper function."""

    def setUp(self):  # noqa: N802
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        self.test_url = "http://example.com/api"
        self.test_headers = {"Content-Type": "application/json"}
        self.test_data = [
            {"some": "data", "another": "thing"},
            {"more": "things"},
            {"what": "is", "this": "record"},
            {"last": "item"}
        ]
        self.exc = None
        self.response_index = 0
        self.num_calls = 0

    @paginate
    def wrapped_function(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Provide a working function to wrap for the tests."""
        # Mimic raising an exception
        # pylint: disable=raising-bad-type
        if isinstance(self.exc, BaseException):
            raise self.exc

        self.assertEqual(kwargs.get("url"), self.test_url)
        self.assertEqual(kwargs.get("headers"), self.test_headers)

        return self.test_data

    @paginate
    def fake_paging(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Provide a working paging function for the tests."""
        self.num_calls += 1
        index = self.response_index
        if index < len(self.test_data):
            data = [self.test_data[index]]
            self.response_index += 1
            return data

        return []

    def test_correct(self):
        """Call the inner function with the correct parameters."""
        data = []

        # Call the test function
        result = self.wrapped_function(url=self.test_url, headers=self.test_headers)
        self.assertTrue(isinstance(result, types.GeneratorType))

        for res in result:
            data.append(res)

        # Test that the return value passes through correctly
        self.assertEqual(data, self.test_data)

    def test_paging(self):
        """Call the inner function with the correct parameters the correct number of times."""
        data = []

        # Call the test function
        result = self.fake_paging(url=self.test_url, headers=self.test_headers, size=1)

        for res in result:
            data.append(res)

        # Test that the return value passes through correctly
        self.assertEqual(data, self.test_data)
        self.assertEqual(self.num_calls, len(self.test_data) + 1)


class TestTrafficLog(TestCase):
    """Tests for the cert_manager._helpers.traffic_log wrapper function."""

    # Create the mocks outside so it can be used by the wrapper
    mock_logger = mock.Mock(spec=logging.Logger)

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # self.mock_logger = mock.Mock(spec=logging.Logger)

        self.test_url = "http://example.com/api"
        self.test_headers = {"TestHeader": "testvalue"}
        self.test_data = {"test": "somedata"}
        self.test_json_resp = {"success": "some message"}
        self.exc = None

        # Reset the mock on every run since it lives at the root of the class
        self.mock_logger.reset_mock()

        self.res_headers = "{'Content-Type': 'application/json'}"

    @responses.activate
    @traffic_log(traffic_logger=mock_logger)
    def wrapped_function(self, url=None, headers=None, data=None):
        """Provide a working function to wrap for the tests."""
        responses.add(responses.GET, url, json=self.test_json_resp, status=200)
        resp = requests.get("http://example.com/api", headers=headers, params=data)

        # Mimic raising an exception
        # pylint: disable=raising-bad-type
        if isinstance(self.exc, BaseException):
            raise self.exc

        return resp

    @responses.activate
    @traffic_log(traffic_logger=mock_logger)
    def wrapped_error_function(self, url=None, headers=None, data=None):
        """Provide a working function to wrap for the tests."""
        responses.add(responses.GET, url, json=self.test_json_resp, status=404)
        resp = requests.get("http://example.com/api", headers=headers, params=data)

        resp.raise_for_status()

        return resp

    @responses.activate
    @traffic_log()
    def bad_param_function(self, url=None, headers=None, data=None):
        """Provide a broken function to wrap for the tests."""
        responses.add(responses.GET, url, json=self.test_json_resp, status=200)
        resp = requests.get("http://example.com/api", headers=headers, params=data)

        # Mimic raising an exception
        # pylint: disable=raising-bad-type
        if isinstance(self.exc, BaseException):
            raise self.exc

        return resp

    def test_correct(self):
        """Data should be logged to the provided logger if passed as keyword arguments."""
        # Call the test function
        ret = self.wrapped_function(url=self.test_url, headers=self.test_headers, data=self.test_data)

        # Test that the return value passes through correctly
        self.assertEqual(ret.text, json.dumps(self.test_json_resp))

        # Test that all the logging calls happen as expected
        self.assertEqual(self.mock_logger.debug.call_count, 6)
        self.mock_logger.debug.assert_any_call(
            f"Performing a {'wrapped_function'.upper()} on url: {self.test_url}"
        )
        self.mock_logger.debug.assert_any_call(f"Extra request headers: {self.test_headers}")
        self.mock_logger.debug.assert_any_call(f"Data: {self.test_data}")
        self.mock_logger.debug.assert_any_call("Result code: 200")
        self.mock_logger.debug.assert_any_call(f"Result headers: {self.res_headers}")
        self.mock_logger.debug.assert_any_call(f"Text result: {json.dumps(self.test_json_resp)}")

    def test_correct_positional(self):
        """Data should be logged to the provided logger if passed as positional arguments."""
        # Call the test function
        ret = self.wrapped_function(self.test_url, self.test_headers, self.test_data)

        # Test that the return value passes through correctly
        self.assertEqual(ret.text, json.dumps(self.test_json_resp))

        # Test that all the logging calls happen as expected
        self.assertEqual(self.mock_logger.debug.call_count, 6)
        self.mock_logger.debug.assert_any_call(
            f"Performing a {'wrapped_function'.upper()} on url: {self.test_url}"
        )
        self.mock_logger.debug.assert_any_call(f"Extra request headers: {self.test_headers}")
        self.mock_logger.debug.assert_any_call(f"Data: {self.test_data}")
        self.mock_logger.debug.assert_any_call("Result code: 200")
        self.mock_logger.debug.assert_any_call(f"Result headers: {self.res_headers}")
        self.mock_logger.debug.assert_any_call(f"Text result: {json.dumps(self.test_json_resp)}")

    def test_inner_exception(self):
        """Raise an exception if an exception is raised by the wrapped function."""
        err_msg = "this is an error"
        self.exc = Exception(err_msg)

        # Make sure the proper exception is raised
        self.assertRaisesRegex(Exception, err_msg, self.wrapped_function, url=self.test_url)

    def test_inner_http_error(self):
        """Raise an exception if an HTTPError is raised by the wrapped function."""
        err_msg = "404 Client Error: Not Found for url: http://example.com/api"

        # Make sure the proper exception is raised
        self.assertRaisesRegex(requests.exceptions.HTTPError, err_msg, self.wrapped_error_function, url=self.test_url)
        self.mock_logger.debug.assert_any_call("Result code: 404")
        self.mock_logger.debug.assert_any_call(f"Result headers: {self.res_headers}")
        self.mock_logger.debug.assert_any_call(f"Text result: {json.dumps(self.test_json_resp)}")

    def test_bad_param_exception(self):
        """Raise an exception if no logging instance is provided."""
        err_msg = "traffic_log: No logging.Logger instance provided"

        # Make sure the proper exception is raised
        self.assertRaisesRegex(Exception, err_msg, self.bad_param_function, url=self.test_url)
