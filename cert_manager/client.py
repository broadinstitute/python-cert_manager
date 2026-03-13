"""Define the cert_manager.client.Client class."""

import logging
import re
import sys

import requests

from . import __version__
from ._helpers import traffic_log

LOGGER = logging.getLogger(__name__)


class Client:  # pylint: disable=too-many-instance-attributes
    """Serve as a Base class for calls to the Sectigo Cert Manager APIs."""

    DOWNLOAD_TYPES = [
        "base64",  # PKCS#7 Base64 encoded
        "bin",  # PKCS#7 Bin encoded
        "x509",  # X509, Base64 encoded
        "x509CO",  # X509 Certificate only, Base64 encoded
        "x509IO",  # X509 Intermediates/root only, Base64 encoded
        "x509IOR",  # X509 Intermediates/root only Reverse, Base64 encoded
    ]

    def __init__(self, **kwargs):
        """Initialize the class.

        Args:
            kwargs: The keyword arguments to use for initialization. The following keys are accepted:
                base_url: The full URL to the Sectigo API server; the default is "https://cert-manager.com/api"
                login_uri: The URI for the customer login.
                    If your login to the Sectigo GUI is https://cert-manager.com/customer/foo/, your login URI is "foo".
                username: The username with which to login
                password: The password with which to login
                cert_auth: Boolean on whether to use client certificate authentication if True; the default is False
                user_crt_file: The path to the certificate file if using client cert auth
                user_key_file: The path to the key file if using client cert auth
                auth_url: The full URL to the Sectigo OAuth2 token endpoint; the default is "https://auth.sso.sectigo.com/auth/realms/apiclients/protocol/openid-connect/token"
                client_id: The Client ID to use for OAuth2 authentication
                client_secret: The Client Secret to use for OAuth2 authentication
                session: A requests.Session object to use instead of creating a new one; the default is None,
                    which will create a new session
        """
        # Initialize class variables
        self._base_url = None
        self._cert_auth = None
        self._login_uri = None
        self._oauth2_token = None
        self._password = None
        self._user_crt_file = None
        self._user_key_file = None
        self._username = None

        self._session = kwargs.get("session", requests.Session())

        # Set the default HTTP headers
        self._headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

        if "client_id" in kwargs or "client_secret" in kwargs:
            self._oauth2_login(
                client_id=kwargs["client_id"],
                client_secret=kwargs["client_secret"],
                auth_url=kwargs.get(
                    "auth_url", "https://auth.sso.sectigo.com/auth/realms/apiclients/protocol/openid-connect/token"
                ),
                base_url=kwargs.get("base_url", "https://admin.enterprise.sectigo.com/api"),
            )
        else:
            # These options are required, so raise a KeyError if they are not provided.
            self._login_uri = kwargs["login_uri"]
            self._username = kwargs["username"]

            # Using get for consistency and to allow defaults to be easily set
            self._base_url = kwargs.get("base_url", "https://cert-manager.com/api")
            self._cert_auth = kwargs.get("cert_auth", False)

            # Set the default HTTP headers
            self._headers.update({
                "login": self._username,
                "customerUri": self._login_uri,
            })

            if self._cert_auth:
                self._cert_login(
                    base_url=self._base_url,
                    login_uri=self._login_uri,
                    username=self._username,
                    user_crt_file=kwargs["user_crt_file"],
                    user_key_file=kwargs["user_key_file"],
                )
            else:
                self._password_login(username=self._username, password=kwargs["password"])

        self._session.headers.update(self._headers)

    def _cert_login(self, base_url, login_uri, username, user_crt_file, user_key_file):
        """Authenticate to the Sectigo API using client certificate authentication.

        Args:
            base_url: The full URL to the Sectigo API server
            login_uri: The URI for the customer login
            username: The username with which to login
            user_crt_file: The path to the client certificate file
            user_key_file: The path to the client key file
        """
        self._user_crt_file = user_crt_file
        self._user_key_file = user_key_file

        # Require keys if cert_auth is True or raise a KeyError
        self._session.cert = (self._user_crt_file, self._user_key_file)

        # Warn about using /api instead of /private/api if doing certificate auth
        if not re.search("/private", self._base_url):
            cert_uri = re.sub("/api", "/private/api", self._base_url)
            LOGGER.warning("base URI should probably be %s due to certificate auth", cert_uri)

    def _password_login(self, username,password):
        """Authenticate to the Sectigo API using password authentication.

        Args:
            username: The username with which to login
            password: The password with which to login
        """
        # If we're not doing certificate auth, we need a password, so make sure an exception is raised if
        # a password was not passed as an argument
        self._password = password
        self._headers.update({
            "password": self._password
        })

    def _oauth2_login(
        self,
        client_id,
        client_secret,
        auth_url="https://auth.sso.sectigo.com/auth/realms/apiclients/protocol/openid-connect/token",
        base_url="https://admin.enterprise.sectigo.com/api",
    ):
        """Initialize the class using OAuth2.

        Args:
            client_id: The Client ID to use for OAuth2 authentication
            client_secret: The Client Secret to use for OAuth2 authentication
            auth_url: The full URL to the Sectigo OAuth2 token endpoint; the default is "https://auth.sso.sectigo.com/auth/realms/apiclients/protocol/openid-connect/token"
            base_url: The base URL for the Sectigo API; the default is "https://admin.enterprise.sectigo.com/api"
        """
        self._base_url = base_url
        # Using get for consistency and to allow defaults to be easily set
        self._session = requests.Session()

        payload = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}

        response = requests.post(auth_url, data=payload, headers=headers)
        self._oauth2_token = response.json()['access_token']

        # Set the default HTTP headers
        self._headers = {
            "Authorization": f"Bearer {self._oauth2_token}",
        }

    @property
    def user_agent(self):
        """Return a user-agent string including the module version and Python version."""
        ver_info = list(map(str, sys.version_info))
        pyver = ".".join(ver_info[:3])
        useragent = f"cert_manager/{__version__.__version__} (Python {pyver})"

        return useragent

    @property
    def base_url(self):
        """Return the internal _base_url value."""
        return self._base_url

    @property
    def headers(self):
        """Return the internal _headers value."""
        return self._headers

    @property
    def session(self):
        """Return the setup internal _session requests.Session object."""
        return self._session

    def add_headers(self, headers=None):
        """Add the provided headers to the internally stored headers.

        Note: This function will overwrite an existing header if the key in the headers parameter matches one of the
        keys in the internal dictionary of headers.

        Args:
            headers: A dictionary where key is the header with its value being the setting for that header.
        """
        if headers:
            head = self._headers.copy()
            head.update(headers)
            self._headers = head
            self._session.headers.update(self._headers)

    def remove_headers(self, headers=None):
        """Remove the requested header keys from the internally stored headers.

        Note: If any of the headers in provided the list do not exist, the header will be ignored and will not raise
        an exception.

        Args:
            headers: A list of header keys to delete
        """
        if headers:
            for head in headers:
                if head in self._headers:
                    del self._headers[head]
                    del self._session.headers[head]

    @traffic_log(traffic_logger=LOGGER)
    def head(self, url, headers=None, params=None):
        """Submit a HEAD request to the provided URL.

        Args:
            url: A URL to query
            headers: A dictionary with any extra headers to add to the request
            params: A dictionary with any parameters to add to the request URL
        Returns:
            A requests.Response object received as a response
        """
        result = self._session.head(url, headers=headers, params=params)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def get(self, url, headers=None, params=None):
        """Submit a GET request to the provided URL.

        Args:
            url: A URL to query
            headers: A dictionary with any extra headers to add to the request
            params: A dictionary with any parameters to add to the request URL
        Returns:
            A requests.Response object received as a response
        """
        result = self._session.get(url, headers=headers, params=params)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def post(self, url, headers=None, data=None):
        """Submit a POST request to the provided URL and data.

        Args:
            url: A URL to query
            headers: A dictionary with any extra headers to add to the request
            data: A dictionary with the data to use for the body of the POST
        Returns:
            A requests.Response object received as a response
        """
        result = self._session.post(url, json=data, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def put(self, url, headers=None, data=None):
        """Submit a PUT request to the provided URL and data.

        Args:
            url: A URL to query
            headers: A dictionary with any extra headers to add to the request
            data: A dictionary with the data to use for the body of the PUT
        Returns:
            A requests.Response object received as a response
        """
        result = self._session.put(url, json=data, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def delete(self, url, headers=None, data=None):
        """Submit a DELETE request to the provided URL.

        Args:
            url: A URL to query
            headers: A dictionary with any extra headers to add to the request
            data: A dictionary with the data to use for the body of the DELETE
        Returns:
            A requests.Response object received as a response
        """
        result = self._session.delete(url, json=data, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result
