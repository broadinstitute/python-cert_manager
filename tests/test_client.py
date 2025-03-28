"""Define the cert_manager.client.Client unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

# Link below used when digging into double underscore values in objects
# https://stackoverflow.com/questions/9323749/python-check-if-one-dictionary-is-a-subset-of-another-larger-dictionary
#

import sys
from unittest import mock

import responses
from requests.exceptions import HTTPError
from testtools import TestCase

from cert_manager.client import Client

from .lib.testbase import ClientFixture


class TestClient(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the Client class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Use the Client fixture
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

    def tearDown(self):  # pylint: disable=invalid-name
        """Test tear down method."""
        super().tearDown()

        mock.patch.stopall()


class TestTypes(TestClient):
    """Test hard-coded types in the Client class."""

    def test_types(self):
        """Certificate types need to be hard-coded into Client currently."""
        default_types = ["base64", "bin", "x509", "x509CO", "x509IO", "x509IOR"]

        self.assertEqual(default_types, self.client.DOWNLOAD_TYPES)


class TestInit(TestClient):
    """Test the class initializer."""

    def test_defaults(self):
        """Set parameters correctly inside the class using defaults."""
        client = Client(login_uri=self.cfixt.login_uri, username=self.cfixt.username, password=self.cfixt.password)

        # Use the hackity object mangling when dealing with double-underscore values in an object
        # This hard-coded test is to test that the default base_url is used when none is provided
        self.assertEqual(client._Client__base_url, "https://cert-manager.com/api")
        self.assertEqual(client._Client__login_uri, self.cfixt.login_uri)
        self.assertEqual(client._Client__username, self.cfixt.username)
        self.assertEqual(client._Client__password, self.cfixt.password)
        self.assertEqual(client._Client__cert_auth, False)

        # Make sure all the headers make their way into the internal requests.Session object
        for head, headdata in self.cfixt.headers.items():
            self.assertTrue(head in client._Client__session.headers)
            self.assertEqual(client._Client__session.headers[head], headdata)

        # Because password was used and cert_auth was False, a password header should exist
        self.assertTrue("password" in client._Client__session.headers)
        self.assertEqual(self.cfixt.password, client._Client__session.headers["password"])

    def test_params(self):
        """Set parameters correctly inside the class using all parameters."""
        client = Client(
            base_url=self.cfixt.base_url, login_uri=self.cfixt.login_uri, username=self.cfixt.username,
            password=self.cfixt.password, cert_auth=True, user_crt_file=self.cfixt.user_crt_file,
            user_key_file=self.cfixt.user_key_file,
        )

        # Use the hackity object mangling when dealing with double-underscore values in an object
        self.assertEqual(client._Client__base_url, self.cfixt.base_url)
        self.assertEqual(client._Client__login_uri, self.cfixt.login_uri)
        self.assertEqual(client._Client__username, self.cfixt.username)
        self.assertEqual(client._Client__cert_auth, True)
        self.assertEqual(client._Client__user_crt_file, self.cfixt.user_crt_file)
        self.assertEqual(client._Client__user_key_file, self.cfixt.user_key_file)
        self.assertEqual(client._Client__session.cert, (self.cfixt.user_crt_file, self.cfixt.user_key_file))

        # Make sure all the headers make their way into the internal requests.Session object
        for head, headdata in self.cfixt.headers.items():
            self.assertTrue(head in client._Client__session.headers)
            self.assertEqual(client._Client__session.headers[head], headdata)

        # If cert_auth is True, make sure a password header does not exist
        self.assertFalse("password" in client._Client__session.headers)

    def test_no_pass_with_certs(self):
        """Set parameters correctly inside the class certificate auth without a password."""
        client = Client(
            base_url=self.cfixt.base_url, login_uri=self.cfixt.login_uri, username=self.cfixt.username, cert_auth=True,
            user_crt_file=self.cfixt.user_crt_file, user_key_file=self.cfixt.user_key_file,
        )

        # Use the hackity object mangling when dealing with double-underscore values in an object
        self.assertEqual(client._Client__base_url, self.cfixt.base_url)
        self.assertEqual(client._Client__login_uri, self.cfixt.login_uri)
        self.assertEqual(client._Client__username, self.cfixt.username)
        self.assertEqual(client._Client__cert_auth, True)
        self.assertEqual(client._Client__user_crt_file, self.cfixt.user_crt_file)
        self.assertEqual(client._Client__user_key_file, self.cfixt.user_key_file)
        self.assertEqual(client._Client__session.cert, (self.cfixt.user_crt_file, self.cfixt.user_key_file))

        # Make sure all the headers make their way into the internal requests.Session object
        for head, headdata in self.cfixt.headers.items():
            self.assertTrue(head in client._Client__session.headers)
            self.assertEqual(client._Client__session.headers[head], headdata)

        # If cert_auth is True, make sure a password header does not exist
        self.assertFalse("password" in client._Client__session.headers)

    def test_versioning(self):
        """Change the user-agent header if the version number changes."""
        test_version = "10.9.8"
        ver_info = list(map(str, sys.version_info))
        pyver = ".".join(ver_info[:3])
        user_agent = f"cert_manager/{test_version} (Python {pyver})"

        ver_patcher = mock.patch("cert_manager.__version__.__version__", test_version)
        ver_patcher.start()

        client = Client(login_uri=self.cfixt.login_uri, username=self.cfixt.username, password=self.cfixt.password)

        # Make sure the user-agent header is correct in the class and the internal requests.Session object
        self.assertEqual(client.headers["User-Agent"], user_agent)
        self.assertEqual(client._Client__session.headers["User-Agent"], user_agent)

    def test_need_crt(self):
        """Raise an exception without a cert file if cert_auth=True."""
        self.assertRaises(KeyError, Client, base_url=self.cfixt.base_url, login_uri=self.cfixt.login_uri,
                          username=self.cfixt.username, cert_auth=True, user_key_file=self.cfixt.user_key_file)

    def test_need_key(self):
        """Raise an exception without a key file if cert_auth=True."""
        self.assertRaises(KeyError, Client, base_url=self.cfixt.base_url, login_uri=self.cfixt.login_uri,
                          username=self.cfixt.username, cert_auth=True, user_crt_file=self.cfixt.user_crt_file)

    def test_need_login_uri(self):
        """Raise an exception without a login_uri."""
        self.assertRaises(KeyError, Client, username=self.cfixt.username, password=self.cfixt.password)

    def test_need_username(self):
        """Raise an exception without a username."""
        self.assertRaises(KeyError, Client, login_uri=self.cfixt.login_uri, password=self.cfixt.password)

    def test_need_password(self):
        """Raise an exception without a password."""
        self.assertRaises(KeyError, Client, login_uri=self.cfixt.login_uri, username=self.cfixt.username)

    def test_need_public_key(self):
        """Raise an exception without a public key if cert_auth is enabled."""
        self.assertRaises(
            KeyError, Client, login_uri=self.cfixt.login_uri, username=self.cfixt.username,
            password=self.cfixt.password, cert_auth=True, user_key_file=self.cfixt.user_key_file,
        )

    def test_need_private_key(self):
        """Raise an exception without a private key if cert_auth is enabled."""
        self.assertRaises(
            KeyError, Client, login_uri=self.cfixt.login_uri, username=self.cfixt.username,
            password=self.cfixt.password, cert_auth=True, user_crt_file=self.cfixt.user_crt_file,
        )


class TestProperties(TestClient):
    """Test the property methods in the class."""

    def test_base_url(self):
        """The base_url property should return the correct value."""
        self.assertEqual(self.client.base_url, self.cfixt.base_url)

    def test_headers(self):
        """The headers property should return the correct value."""
        client = Client(login_uri=self.cfixt.login_uri, username=self.cfixt.username, password=self.cfixt.password)

        headers = self.cfixt.headers.copy()
        headers["password"] = self.cfixt.password

        # Since we initialized with a username/password, the password header will need to exist as well
        self.assertEqual(client.headers, headers)

    def test_session(self):
        """The session property should return the correct value."""
        self.assertEqual(self.client._Client__session, self.client.session)


class TestAddHeaders(TestClient):
    """Test the add_headers method."""

    def test_add(self):
        """The extra headers should be added correctly."""
        headers = {"Connection": "close"}

        self.client.add_headers(headers)

        # Make sure the new headers make their way into the internal requests.Session object
        for header, hval in headers.items():
            self.assertTrue(header in self.client._Client__session.headers)
            self.assertEqual(hval, self.client._Client__session.headers[header])

        # Make sure the original headers are still in the internal requests.Session object
        for head, headdata in self.cfixt.headers.items():
            self.assertTrue(head in self.client._Client__session.headers)
            self.assertEqual(self.client._Client__session.headers[head], headdata)

    def test_replace(self):
        """The already existing header should be modified."""
        headers = {"User-Agent": "test123"}

        self.client.add_headers(headers)

        # Make sure the new headers make their way into the internal requests.Session object
        for header, hval in headers.items():
            self.assertTrue(header in self.client._Client__session.headers)
            self.assertEqual(hval, self.client._Client__session.headers[header])

        # Removed the modified header from the check as it was checked above
        del self.cfixt.headers["User-Agent"]
        # Make sure the original headers are still in the internal requests.Session object
        for head, headdata in self.cfixt.headers.items():
            self.assertTrue(head in self.client._Client__session.headers)
            self.assertEqual(self.client._Client__session.headers[head], headdata)

    def test_not_dictionary(self):
        """Raise an exception when not passed a dictionary."""
        headers = ["User-Agent", "test123"]
        self.assertRaises(ValueError, self.client.add_headers, headers)


class TestRemoveHeaders(TestClient):
    """Test the remove_headers method."""

    def test_remove(self):
        """Remove headers correctly if passed a list."""
        headers = ["Accept", "customerUri"]

        self.client.remove_headers(headers)

        # Make sure the headers are removed from the requests.Session object
        for head in headers:
            self.assertFalse(head in self.client._Client__session.headers)

        # Make sure the rest of the headers we added before are still there
        for head, headdata in self.cfixt.headers.items():
            if head not in headers:
                self.assertTrue(head in self.client._Client__session.headers)
                self.assertEqual(self.client._Client__session.headers[head], headdata)

    def test_dictionary(self):
        """Remove headers correctly if passed a dictionary."""
        headers = {"Accept": "test123"}

        self.client.remove_headers(headers)

        # Make sure the headers are removed from the requests.Session object
        for head in headers:
            self.assertFalse(head in self.client._Client__session.headers)

        # Make sure the rest of the headers we added before are still there
        for head, headdata in self.cfixt.headers.items():
            if head not in headers:
                self.assertTrue(head in self.client._Client__session.headers)
                self.assertEqual(self.client._Client__session.headers[head], headdata)


class TestGet(TestClient):
    """Test the get method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # An example URL to use in testing
        self.test_url = f"{self.cfixt.base_url}/test/url"

    @responses.activate
    def test_success(self):
        """Return data correctly if a 200-level status code is returned with data."""
        # Setup the mocked response
        json_data = {"some": "data"}
        responses.add(responses.GET, self.test_url, json=json_data, status=200)

        # Call the function
        resp = self.client.get(self.test_url)

        # Verify all the query information
        self.assertEqual(resp.json(), json_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_headers(self):
        """Add passed headers."""
        # Setup the mocked response
        json_data = {"some": "data"}
        responses.add(responses.GET, self.test_url, json=json_data, status=200)

        # Call the function with extra headers
        headers = {"newheader": "123"}
        resp = self.client.get(self.test_url, headers=headers)

        # Verify all the query information
        self.assertEqual(resp.json(), json_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

        for header, hval in headers.items():
            self.assertTrue(header in responses.calls[0].request.headers)
            self.assertEqual(hval, responses.calls[0].request.headers[header])

    @responses.activate
    def test_params(self):
        """Add passed parameters."""
        # Setup the mocked response
        json_data = {"some": "data"}
        responses.matchers.query_string_matcher = False
        responses.add(responses.GET, self.test_url, json=json_data, status=200)

        # Call the function with extra parameters
        params = {"key": "value"}
        resp = self.client.get(self.test_url, params=params)
        (scheme, netloc, path, query_string, _) = responses.urlsplit(
            responses.calls[0].request.url)
        url_plain = responses.urlunsplit((scheme, netloc, path, None, None))

        # Verify all the query information
        self.assertEqual(resp.json(), json_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(url_plain, self.test_url)
        query_params = dict(responses.parse_qsl(query_string))
        # See https://stackoverflow.com/questions/20050913
        self.assertEqual(query_params, {**params, **query_params})

    @responses.activate
    def test_failure(self):
        """Raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        json_data = {"description": "some error"}
        responses.add(responses.GET, self.test_url, json=json_data, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.client.get, self.test_url)

        # Still make sure it actually did a query and received a result
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestPost(TestClient):
    """Test the post method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # An example URL to use in testing
        self.test_url = f"{self.cfixt.base_url}/test/url"

    @responses.activate
    def test_success(self):
        """Return data correctly if a 200-level status code is returned with data."""
        # Setup the mocked response
        input_data = {"input": "data"}
        output_data = {"output": "data"}
        responses.add(responses.POST, self.test_url, json=output_data, status=200)

        # Call the function
        resp = self.client.post(self.test_url, data=input_data)

        # Verify all the query information
        self.assertEqual(resp.json(), output_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_headers(self):
        """Add passed headers."""
        # Setup the mocked response
        input_data = {"input": "data"}
        output_data = {"output": "data"}
        responses.add(responses.POST, self.test_url, json=output_data, status=200)

        # Call the function with extra headers
        headers = {"newheader": "123"}
        resp = self.client.post(self.test_url, headers=headers, data=input_data)

        # Verify all the query information
        self.assertEqual(resp.json(), output_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

        for header, hval in headers.items():
            self.assertTrue(header in responses.calls[0].request.headers)
            self.assertEqual(hval, responses.calls[0].request.headers[header])

    @responses.activate
    def test_failure(self):
        """Raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        input_data = {"input": "data"}
        output_data = {"output": "data"}
        responses.add(responses.POST, self.test_url, json=output_data, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.client.post, self.test_url, data=input_data)

        # Still make sure it actually did a query and received a result
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestPut(TestClient):
    """Test the put method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # An example URL to use in testing
        self.test_url = f"{self.cfixt.base_url}/test/url"

    @responses.activate
    def test_success(self):
        """Return data correctly if a 200-level status code is returned with data."""
        # Setup the mocked response
        input_data = {"input": "data"}
        output_data = {"output": "data"}
        responses.add(responses.PUT, self.test_url, json=output_data, status=200)

        # Call the function
        resp = self.client.put(self.test_url, data=input_data)

        # Verify all the query information
        self.assertEqual(resp.json(), output_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_headers(self):
        """Add passed headers."""
        # Setup the mocked response
        input_data = {"input": "data"}
        output_data = {"output": "data"}
        responses.add(responses.PUT, self.test_url, json=output_data, status=200)

        # Call the function with extra headers
        headers = {"newheader": "123"}
        resp = self.client.put(self.test_url, headers=headers, data=input_data)

        # Verify all the query information
        self.assertEqual(resp.json(), output_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

        for header, hval in headers.items():
            self.assertTrue(header in responses.calls[0].request.headers)
            self.assertEqual(hval, responses.calls[0].request.headers[header])

    @responses.activate
    def test_failure(self):
        """Raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        input_data = {"input": "data"}
        output_data = {"output": "data"}
        responses.add(responses.PUT, self.test_url, json=output_data, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.client.put, self.test_url, data=input_data)

        # Still make sure it actually did a query and received a result
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestDelete(TestClient):
    """Test the delete method."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # An example URL to use in testing
        self.test_url = f"{self.cfixt.base_url}/test/url"

    @responses.activate
    def test_success(self):
        """Return successful if a 200-level status code is returned."""
        # Setup the mocked response
        input_data = {"input": "data"}
        responses.add(responses.DELETE, self.test_url, status=204)

        # Call the function
        self.client.delete(self.test_url, data=input_data)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_headers(self):
        """Add passed headers."""
        # Setup the mocked response
        input_data = {"input": "data"}
        responses.add(responses.DELETE, self.test_url, status=204)

        # Call the function
        headers = {"newheader": "123"}
        self.client.delete(self.test_url, headers=headers, data=input_data)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

        for header, hval in headers.items():
            self.assertTrue(header in responses.calls[0].request.headers)
            self.assertEqual(hval, responses.calls[0].request.headers[header])

    @responses.activate
    def test_failure(self):
        """Raise an HTTPError exception if a non-200 status code is returned."""
        # Setup the mocked response
        input_data = {"input": "data"}
        responses.add(responses.DELETE, self.test_url, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.client.delete, self.test_url, data=input_data)

        # Still make sure it actually did a query and received a result
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
