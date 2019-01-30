"""Define the cert_manager._helpers.HttpError exception class unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

from testtools import TestCase

import requests

from cert_manager._helpers import HttpError


class TestHttpError(TestCase):
    """Test the cert_manager._helpers.HttpError exception class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super(TestHttpError, self).setUp()

        # Mock up a response
        self.resp = requests.Response()
        self.resp.status_code = 404
        self.resp.headers = {"SomeHeader": "some value"}

    def test_init(self):
        """The class should have correct values when initialized correctly."""
        self.resp._content = b'{"description": "error message"}'
        err_msg = "%s: error message" % self.resp.status_code

        # Create an HttpError exception
        exc = HttpError(result=self.resp)

        # Make sure internal values are set correctly
        self.assertEqual(exc._HttpError__result, self.resp)
        self.assertEqual(str(exc), err_msg)

    def test_no_json(self):
        """The class should have a generic error if JSON data is not returned."""
        self.resp._content = b"<html><body>Some Error</body></html>"
        err_msg = "%s: Unknown HTTP error" % self.resp.status_code

        # Create an HttpError exception
        exc = HttpError(result=self.resp)

        # Make sure internal values are set correctly
        self.assertEqual(exc._HttpError__result, self.resp)
        self.assertEqual(str(exc), err_msg)
