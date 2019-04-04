# -*- coding: utf-8 -*-
"""Define the cert_manager._helpers.traffic_log wrapper function unit tests."""
# Because pylint can't figure out how requests does some magic things
# pylint: disable=no-member

import json
import logging
import sys

import mock
from testtools import TestCase

import requests
import responses

from cert_manager._helpers import traffic_log


class TestTrafficLog(TestCase):
    """Tests for the cert_manager._helpers.traffic_log wrapper function."""

    # Create the mocks outside so it can be used by the wrapper
    mock_logger = mock.Mock(spec=logging.Logger)

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super(TestTrafficLog, self).setUp()

        # self.mock_logger = mock.Mock(spec=logging.Logger)

        self.test_url = "http://example.com/api"
        self.test_headers = {"TestHeader": "testvalue"}
        self.test_data = {"test": "somedata"}
        self.test_json_resp = {"success": "some message"}
        self.exc = None

        # Reset the mock on every run since it lives at the root of the class
        self.mock_logger.reset_mock()

        # This is special because of the difference in strings between Python 2 and 3
        self.res_headers = "{'Content-Type': 'application/json'}"
        if sys.version_info[0] < 3:
            self.res_headers = "{u'Content-Type': u'application/json'}"

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
            "Performing a %s on url: %s" % ("wrapped_function".upper(), self.test_url)
        )
        self.mock_logger.debug.assert_any_call("Extra request headers: %s" % self.test_headers)
        self.mock_logger.debug.assert_any_call("Data: %s" % self.test_data)
        self.mock_logger.debug.assert_any_call("Result code: 200")
        self.mock_logger.debug.assert_any_call("Result headers: %s" % self.res_headers)
        self.mock_logger.debug.assert_any_call('Text result: %s' % json.dumps(self.test_json_resp))

    def test_correct_positional(self):
        """Data should be logged to the provided logger if passed as positional arguments."""
        # Call the test function
        ret = self.wrapped_function(self.test_url, self.test_headers, self.test_data)

        # Test that the return value passes through correctly
        self.assertEqual(ret.text, json.dumps(self.test_json_resp))

        # Test that all the logging calls happen as expected
        self.assertEqual(self.mock_logger.debug.call_count, 6)
        self.mock_logger.debug.assert_any_call(
            "Performing a %s on url: %s" % ("wrapped_function".upper(), self.test_url)
        )
        self.mock_logger.debug.assert_any_call("Extra request headers: %s" % self.test_headers)
        self.mock_logger.debug.assert_any_call("Data: %s" % self.test_data)
        self.mock_logger.debug.assert_any_call("Result code: 200")
        self.mock_logger.debug.assert_any_call("Result headers: %s" % self.res_headers)
        self.mock_logger.debug.assert_any_call('Text result: %s' % json.dumps(self.test_json_resp))

    def test_fewer_lines(self):
        """Some logs should not be printed if the values are empty."""
        # Call the test function
        self.wrapped_function(url=self.test_url)

        # Test that all the logging calls happen as expected
        self.assertEqual(self.mock_logger.debug.call_count, 4)
        self.mock_logger.debug.assert_any_call(
            "Performing a %s on url: %s" % ("wrapped_function".upper(), self.test_url)
        )
        self.mock_logger.debug.assert_any_call("Result code: 200")
        self.mock_logger.debug.assert_any_call("Result headers: %s" % self.res_headers)
        self.mock_logger.debug.assert_any_call('Text result: %s' % json.dumps(self.test_json_resp))

    def test_inner_exception(self):
        """An exception should be raised by the wrapper if an exception is raised by the wrapped function."""
        err_msg = "this is an error"
        self.exc = Exception(err_msg)

        # Make sure the proper exception is raised
        self.assertRaisesRegex(Exception, err_msg, self.wrapped_function, url=self.test_url)

    def test_inner_http_error(self):
        """An exception should be raised by wrapper if an HTTPError is raised by the wrapped function."""
        err_msg = "404 Client Error: Not Found for url: http://example.com/api"

        # Make sure the proper exception is raised
        self.assertRaisesRegex(requests.exceptions.HTTPError, err_msg, self.wrapped_error_function, url=self.test_url)
        self.mock_logger.debug.assert_any_call("Result code: 404")
        self.mock_logger.debug.assert_any_call("Result headers: %s" % self.res_headers)
        self.mock_logger.debug.assert_any_call('Text result: %s' % json.dumps(self.test_json_resp))

    def test_bad_param_exception(self):
        """An exception should be raised by wrapper if no logging instance is provided."""
        err_msg = "traffic_log: No logging.Logger instance provided"

        # Make sure the proper exception is raised
        self.assertRaisesRegex(Exception, err_msg, self.bad_param_function, url=self.test_url)
