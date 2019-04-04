# -*- coding: utf-8 -*-
"""Define the cert_manager.client.Client class."""

import logging
import re
import sys

import requests

from . import __version__
from ._helpers import traffic_log

LOGGER = logging.getLogger(__name__)


class Client(object):
    """Serve as a Base class for calls to the Sectigo Cert Manager APIs."""

    DOWNLOAD_TYPES = [
        "base64",   # PKCS#7 Base64 encoded
        "bin",      # PKCS#7 Bin encoded
        "x509",     # X509, Base64 encoded
        "x509CO",   # X509 Certificate only, Base64 encoded
        "x509IO",   # X509 Intermediates/root only, Base64 encoded
        "x509IOR",  # X509 Intermediates/root only Reverse, Base64 encoded
    ]

    def __init__(self, **kwargs):
        """Initialize the class.

        :param string base_url: The full URL to the Sectigo API server; the default is "https://cert-manager.com/api"
        :param string login_uri: The URI for the customer login
            If your login to the Sectigo GUI is https://cert-manager.com/customer/foo/, your login URI is "foo".
        :param string username: The username with which to login
        :param string password: The password with which to login
        :param bool cert_auth: Use client certificate authentication if True; the default is False
        :param string user_crt_file: The path to the certificate file if using client cert auth
        :param string user_key_file: The path to the key file if using client cert auth
        """
        # These options are required, so raise a KeyError if they are not provided.
        self.__login_uri = kwargs["login_uri"]
        self.__username = kwargs["username"]

        # Using get for consistency and to allow defaults to be easily set
        self.__base_url = kwargs.get("base_url", "https://cert-manager.com/api")
        self.__cert_auth = kwargs.get("cert_auth", False)
        self.__session = requests.Session()

        self.__user_crt_file = kwargs.get("user_crt_file")
        self.__user_key_file = kwargs.get("user_key_file")

        # Set the default HTTP headers
        self.__headers = {
            "login": self.__username,
            "customerUri": self.__login_uri,
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

        # Setup the Session for certificate auth
        if self.__cert_auth:
            # Require keys if cert_auth is True or raise a KeyError
            self.__user_crt_file = kwargs["user_crt_file"]
            self.__user_key_file = kwargs["user_key_file"]
            self.__session.cert = (self.__user_crt_file, self.__user_key_file)

            # Warn about using /api instead of /private/api if doing certificate auth
            if not re.search("/private", self.__base_url):
                cert_uri = re.sub("/api", "/private/api", self.__base_url)
                LOGGER.warning("base URI should probably be %s due to certificate auth", cert_uri)

        else:
            # If we're not doing certificate auth, we need a password, so make sure an exception is raised if
            # a password was not passed as an argument
            self.__password = kwargs["password"]
            self.__headers["password"] = self.__password

        self.__session.headers.update(self.__headers)

    @property
    def user_agent(self):
        """Return a user-agent string including the module version and Python version."""
        ver_info = list(map(str, sys.version_info))
        pyver = ".".join(ver_info[:3])
        useragent = "cert_manager/%s (Python %s)" % (__version__.__version__, pyver)

        return useragent

    @property
    def base_url(self):
        """Return the internal __base_url value."""
        return self.__base_url

    @property
    def headers(self):
        """Return the internal __headers value."""
        return self.__headers

    @property
    def session(self):
        """Return the setup internal __session requests.Session object."""
        return self.__session

    def add_headers(self, headers=None):
        """Add the provided headers to the internally stored headers.

        Note: This function will overwrite an existing header if the key in the headers parameter matches one of the
        keys in the internal dictionary of headers.

        :param dict headers: A dictionary where key is the header with its value being the setting for that header.
        """
        if headers:
            head = self.__headers.copy()
            head.update(headers)
            self.__headers = head
            self.__session.headers.update(self.__headers)

    def remove_headers(self, headers=None):
        """Remove the requested header keys from the internally stored headers.

        Note: If any of the headers in provided the list do not exist, the header will be ignored and will not raise
        an exception.

        :param list headers: A list of header keys to delete
        """
        if headers:
            for head in headers:
                if head in self.__headers:
                    del self.__headers[head]
                    del self.__session.headers[head]

    @traffic_log(traffic_logger=LOGGER)
    def get(self, url, headers=None):
        """Submit a GET request to the provided URL.

        :param str url: A URL to query
        :param dict headers: A dictionary with any extra headers to add to the request
        :return obj: A requests.Response object received as a response
        """
        result = self.__session.get(url, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def post(self, url, headers=None, data=None):
        """Submit a POST request to the provided URL and data.

        :param str url: A URL to query
        :param dict headers: A dictionary with any extra headers to add to the request
        :param dict data: A dictionary with the data to use for the body of the POST
        :return obj: A requests.Response object received as a response
        """
        result = self.__session.post(url, json=data, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def put(self, url, headers=None, data=None):
        """Submit a PUT request to the provided URL and data.

        :param str url: A URL to query
        :param dict headers: A dictionary with any extra headers to add to the request
        :param dict data: A dictionary with the data to use for the body of the PUT
        :return obj: A requests.Response object received as a response
        """
        result = self.__session.put(url, data=data, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result

    @traffic_log(traffic_logger=LOGGER)
    def delete(self, url, headers=None):
        """Submit a DELETE request to the provided URL.

        :param str url: A URL to query
        :param dict headers: A dictionary with any extra headers to add to the request
        :return obj: A requests.Response object received as a response
        """
        result = self.__session.delete(url, headers=headers)
        # Raise an exception if the return code is in an error range
        result.raise_for_status()

        return result
