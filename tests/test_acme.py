# -*- coding: utf-8 -*-
"""Define the cert_manager.acme.ACMEAccount unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

from functools import wraps

from requests.exceptions import HTTPError
from testtools import TestCase

import responses

from cert_manager.acme import ACMEAccount, ACMEAccountCreationResponseError

from .lib.testbase import ClientFixture


class TestACMEAccount(TestCase):  # pylint: disable=too-few-public-methods
    """Serve as a Base class for all tests of the ACMEAccount class."""

    @property
    def api_url(self):
        """Return the base ACME Account URL for the default API version"""
        return self.get_api_url()

    def get_api_url(self, api_version="v1"):
        """Return the base ACME Account URL for a particular API version"""
        return "{}/acme/{}/account".format(
            self.cfixt.base_url,
            api_version
        )

    def get_acme_account_url(self, acme_id, **kwargs):
        """Return the ACME Account URL for the specified acme_id"""
        return "{}/{}".format(
            self.get_api_url(**kwargs),
            acme_id
        )

    def get_valid_response_entry(self, acme_id):
        """Return the first entry in valid_response with a matching acme_id"""
        for entry in self.valid_response:
            if entry["id"] == acme_id:
                return entry
        raise KeyError("id {} not found in valid_response".format(acme_id))

    def get_acme_account_data(self, acme_id, domains=None):
        """Return a matching entry from valid_response as ACME account data,
        i.e. with SCM domains (empty by default)"""
        valid_response = self.get_valid_response_entry(acme_id).copy()
        valid_response.setdefault("domains", domains or [])
        return valid_response

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.org_id = 1234

        self.base_params = {
            "organizationId": str(self.org_id)
        }

        # Setup a test response one would expect normally
        self.valid_response = [
            {
                "id": 1234,
                "name": "api_account1",
                "status": "pending",
                "macKey": "wtHoOUf8lyPFryvee2vFD8YsMLlhxQVOtNz2hwmTIJLfXauERXqYqzzxcA7b2Dpah84wjchbR8N1FhbFyrBAot",
                "macId": "1SiwNov7jxsUQf3osQD2R4",
                "acmeServer": "https://acme.sectigo.com/v2/OV",
                "organizationId": self.org_id,
                "certValidationType": "OV",
                "accountId": "1SiwNov7jxsUQf3osQD2R4",
                "ovOrderNumber": 387134123,
                "contacts": "",
                "evDetails": {}
            },
            {
                "id": 4321,
                "name": "api_account2",
                "status": "valid",
                "macKey": "Xk9R79FfbdtNzUVRPDvX161NMSgG4WSjgni6grcaYAYUpRrAXfW69acFrajud03nSMONzIvbAGHiVxULSnmWgv",
                "macId": "mZLT4rsopz1veRo9S6IWhQ",
                "acmeServer": "https://acme.sectigo.com/v2/OV",
                "organizationId": self.org_id,
                "certValidationType": "OV",
                "accountId": "mZLT4rsopz1veRo9S6IWhQ",
                "ovOrderNumber": 387134123,
                "contacts": "",
                "evDetails": {}
            },
            {
                "id": 4322,
                "name": "api_account3",
                "status": "pending",
                "macKey": "nupONsz5B8Nvl8eccd3yFiiVPvPCWXUWMBo0oCcT2gPYAs07yGDhF7UXN8esFHd9kt5I5pMgdR3s443V1EAvsA",
                "macId": "n4QsTzHBKSIFu3D7nTxzY8",
                "acmeServer": "https://acme.sectigo.com/v2/EV",
                "organizationId": self.org_id,
                "certValidationType": "EV",
                "accountId": "n4QsTzHBKSIFu3D7nTxzY8",
                "ovOrderNumber": 0,
                "contacts": "",
                "evDetails": {
                    "orgName": "Example Org",
                    "orgCountry": "EX",
                    "postOfficeBox": "",
                    "orgAddress1": "Example Address",
                    "orgAddress2": "",
                    "orgAddress3": "",
                    "orgLocality": "Example Locality",
                    "orgStateOrProvince": "Example State",
                    "orgPostalCode": "12345",
                    "orgJoiState": "",
                    "orgJoiLocality": "",
                    "assumedName": "",
                    "dateOfIncorporation": "",
                    "companyNumber": ""
                }
            }
        ]

        # Setup JSON to return in an error
        self.error_response = {"description": "acme error"}

    def match_url_with_qs(self, url, extra_params=None, api_url=None):
        """Check that a URL containing a query string matches
        the base self.api_url and the query params contain self.base_params
        and extra_params

        :param string url: The URL to check
        :param dict extra_params: The params the query string must contain, in addition to self.base_params
        :param string api_url: Override self.api_url
        """
        api_url = api_url or self.api_url
        (scheme, netloc, path, query_string, _) = responses.urlsplit(url)
        url_plain = responses.urlunsplit((scheme, netloc, path, None, None))
        self.assertEqual(url_plain, api_url)
        params = dict(responses.parse_qsl(query_string))
        match_params = self.base_params.copy()
        match_params.update(extra_params or {})
        self.assertGreaterEqual(params.items(), match_params.items())


class TestInit(TestACMEAccount):
    """Test the class initializer."""

    def test_need_client(self):
        """The class should raise an exception without a client parameter."""
        self.assertRaises(TypeError, ACMEAccount)


class TestAll(TestACMEAccount):
    """Test the .all method."""

    @responses.activate
    def test_init_param(self):
        """The URL should change if api_version is passed as a parameter to
        class initialization."""
        # Set a new version
        version = "v3"
        api_url = self.get_api_url(api_version=version)

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.valid_response,
                      status=200, match_querystring=False)

        acme = ACMEAccount(client=self.client, api_version=version)
        data = acme.all(self.org_id)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.match_url_with_qs(responses.calls[0].request.url, api_url=api_url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_bad_http(self):
        """The function should raise an HTTPError exception if acme accounts cannot be retrieved from the API."""
        # Setup the mocked response
        responses.add(responses.GET, self.api_url, json=self.error_response,
                      status=404, match_querystring=False)

        acme = ACMEAccount(client=self.client)
        self.assertRaises(HTTPError, acme.all, self.org_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.match_url_with_qs(responses.calls[0].request.url)

    @responses.activate
    def test_cached(self):
        """The function should return all the data, but should not query the API twice."""
        # Setup the mocked response, refrain from matching the query string
        responses.add(responses.GET, self.api_url, json=self.valid_response,
                      status=200, match_querystring=False)

        acme = ACMEAccount(client=self.client)
        acme.all(self.org_id)
        data = acme.all(self.org_id)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.match_url_with_qs(responses.calls[0].request.url)
        self.assertEqual(data, self.valid_response)

    @responses.activate
    def test_forced(self):
        """The function should return all the data, but should query the API twice."""
        # Setup the mocked response, refrain from matching the query string
        responses.add(responses.GET, self.api_url, json=self.valid_response,
                      status=200, match_querystring=False)

        acme = ACMEAccount(client=self.client)
        acme.all(self.org_id, force=True)
        data = acme.all(self.org_id, force=True)

        # Verify all the query information
        # There should only be one call the first time "all" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 2)
        self.match_url_with_qs(responses.calls[0].request.url)
        self.match_url_with_qs(responses.calls[1].request.url)
        self.assertEqual(data, self.valid_response)

    def test_need_org_id(self):
        """The function should raise an exception without an org_id parameter."""
        acme = ACMEAccount(client=self.client)
        self.assertRaises(TypeError, acme.all)


def _test_find_test_factory(params=None):
    params = params or {}
    params_to_api = ACMEAccount._find_params_to_api
    api_params = {
        params_to_api[k]: params[k]
        for k in params
    }

    @responses.activate
    def generic_test(self):
        """Generic test for .find request parameters/response fields"""
        api_params[params_to_api["org_id"]] = str(self.org_id)
        valid_response = [
            entry for entry in self.valid_response
            if all(
                str(entry[k]).lower().find(str(api_params[k]).lower()) != -1
                for k in api_params
            )
        ]
        # Setup the mocked response
        responses.add(
            responses.GET, self.api_url, json=valid_response, status=200, match_querystring=False
        )
        acme = ACMEAccount(client=self.client)
        data = list(acme.find(self.org_id, **params))

        # Verify all the query information
        # There should only be one call when "find" is called.
        # Due to pagination, this is only guaranteed as long as the number of
        # entries returned is less than the page size
        self.assertEqual(len(responses.calls), 1)
        self.match_url_with_qs(responses.calls[0].request.url, api_params)
        self.assertEqual(data, valid_response)
    return generic_test


class TestFind(TestACMEAccount):
    """Test the .find method."""

    test_name = _test_find_test_factory({"name": "api_account1"})
    test_name.__doc__ = """The function should return all the data about the
    matched acme account name(s)."""

    test_acme_server = _test_find_test_factory(
        {"acme_server": "https://acme.sectigo.com/v2/OV"})
    test_acme_server.__doc__ = """The function should return all the data about
    the matched acme account server(s)."""

    test_cert_validation_type = _test_find_test_factory(
        {"cert_validation_type": "EV"})
    test_cert_validation_type.__doc__ = """The function should return all the
    data about the matched acme account validation type(s)."""

    test_cert_status = _test_find_test_factory({"status": "Valid"})
    test_cert_status.__doc__ = """The function should return all the data about
    the matched acme account status(es)."""

    test_ne_server_and_cert_validation_type = _test_find_test_factory({
        "acme_server": "https://acme.sectigo.com/v2/OV",
        "cert_validation_type": "EV"
    })
    test_ne_server_and_cert_validation_type.__doc__ = """The function should
    return an empty list if the acme account server and vaildation type do not
    match."""

    test_ne_name = _test_find_test_factory({"name": "no such account"})
    test_ne_name.__doc__ = """The function should return an empty list if the
    acme account name does not match."""

    test_ne_server = _test_find_test_factory(
        {"acme_server": "https://acme.sectigo.com/v2/XYZ"})
    test_ne_server.__doc__ = """The function should return an empty list if the
    acme account server does not match."""

    test_no_params = _test_find_test_factory()
    test_no_params.__doc__ = """The function should return the entire list of
    acme accounts if no parameters are passed."""

    def test_need_org_id(self):
        """The function should raise an exception without an org_id parameter."""
        acme = ACMEAccount(client=self.client)
        # We need to wrap this all crazy because it now returns an iterator
        result = acme.find()  # pylint:disable=no-value-for-parameter
        self.assertRaises(TypeError, result.__next__)


class TestGet(TestACMEAccount):
    """Test the .get method."""

    def test_need_acme_id(self):
        """The function should raise an exception without an acme_id parameter."""
        acme = ACMEAccount(client=self.client)
        self.assertRaises(TypeError, acme.get)

    @responses.activate
    def test_acme_id(self):
        """The function should return all the data about the specified ACME ID."""
        acme_id = 1234
        api_url = self.get_acme_account_url(acme_id)
        valid_response = self.get_acme_account_data(acme_id)

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=valid_response, status=200)

        acme = ACMEAccount(client=self.client)
        data = acme.get(acme_id)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, valid_response)

    @responses.activate
    def test_ne_acme_id(self):
        """The function should raise an HTTPError exception if the specified ACME ID does not exist."""
        acme_id = 2345
        api_url = self.get_acme_account_url(acme_id)

        # Setup the mocked response
        responses.add(responses.GET, api_url, json=self.error_response,
                      status=404)

        acme = ACMEAccount(client=self.client)
        self.assertRaises(HTTPError, acme.get, acme_id)


def _test_create_test_factory(acme_id=1234, header="location", **kwargs):
    params = ["name", "acmeServer", "organizationId", "evDetails"]

    def wrapper(func):
        @wraps(func)
        def wrapped_func(self):
            location = kwargs.get("location",
                                  self.get_acme_account_url(acme_id))
            response_headers = {
                header: location
            }
            acme_entry = self.get_valid_response_entry(acme_id)
            args = [
                acme_entry[param]
                for param in params
            ]
            request_params = {
                param: acme_entry[param]
                for param in acme_entry
                if param in params
            }
            return func(self, acme_id, response_headers, args, request_params)
        return wrapped_func
    return wrapper


class TestCreate(TestACMEAccount):
    """Test the .create method."""

    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters.
        """

        acme = ACMEAccount(client=self.client)
        # missing name, acme_server, org_id
        self.assertRaises(TypeError, acme.create)
        # missing acme_server, org_id
        self.assertRaises(TypeError, acme.create, "name")
        # missing org_id
        self.assertRaises(TypeError, acme.create, "name", "acme_server")

    @responses.activate
    @_test_create_test_factory()
    def test_create_success(self, acme_id, response_headers, args, request_params):
        """The function should return the created ACME ID."""

        # Setup the mocked response
        responses.add(responses.POST, self.api_url, headers=response_headers,
                      match=[responses.json_params_matcher(request_params)],
                      status=201)

        acme = ACMEAccount(client=self.client)
        response = acme.create(*args)

        self.assertEqual(response, {"id": acme_id})

    @responses.activate
    @_test_create_test_factory()
    def test_create_failure_http_error(self, _, __, args, request_params):
        """
        The function should return an error code and description if the ACME
        Account creation failed.
        """

        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      match=[responses.json_params_matcher(request_params)],
                      status=400)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(HTTPError, acme.create, *args)

    @responses.activate
    @_test_create_test_factory()
    def test_create_failure_http_status_unexpected(self, _, __, args,
                                                   request_params):
        """
        The function should return an error code and description if the ACME
        Account creation failed with ACMEAccountCreationResponseError
        (unexpected HTTP status code).
        """

        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      match=[responses.json_params_matcher(request_params)],
                      status=200)  # unexpected status

        acme = ACMEAccount(client=self.client)

        self.assertRaises(ACMEAccountCreationResponseError, acme.create,
                          *args)

    @responses.activate
    @_test_create_test_factory(header="NotYourHeader")
    def test_create_failure_missing_location_header(self, _, response_headers,
                                                    args, request_params):
        """
        The function should return an error code and description if the ACME
        Account creation failed with ACMEAccountCreationResponseError
        (no Location header in response).
        """

        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      headers=response_headers,
                      match=[responses.json_params_matcher(request_params)],
                      status=201)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(ACMEAccountCreationResponseError, acme.create,
                          *args)

    @responses.activate
    @_test_create_test_factory(location="not_an_ACME_account_URL")
    def test_create_failure_acme_id_not_found(self, _, response_headers, args,
                                              request_params):
        """
        The function should return an error code and description if the ACME
        Account creation failed with ACMEAccountCreationResponseError
        (ACME ID not found in response).
        """

        # Setup the mocked response
        responses.add(responses.POST, self.api_url, json=self.error_response,
                      headers=response_headers,
                      match=[responses.json_params_matcher(request_params)],
                      status=201)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(ACMEAccountCreationResponseError, acme.create,
                          *args)


def _test_update_delete_test_factory(func):
    acme_id = 1234
    new_name = "api_account1_new_name"
    if func.__name__.find("test_update") == 0:
        args = (acme_id, new_name)
    else:
        args = (acme_id,)

    @wraps(func)
    def wrapped_func(self):
        return func(self, *args)
    return wrapped_func


class TestUpdate(TestACMEAccount):
    """Test the .update method."""

    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters.
        """

        acme = ACMEAccount(client=self.client)
        # missing acme_id, name
        self.assertRaises(TypeError, acme.create)
        # missing name
        self.assertRaises(TypeError, acme.create, 1234)

    @responses.activate
    @_test_update_delete_test_factory
    def test_update_success(self, acme_id, new_name):
        """The function should return True if the update succeeded."""

        api_url = self.get_acme_account_url(acme_id)

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=200)

        acme = ACMEAccount(client=self.client)
        response = acme.update(acme_id, new_name)

        self.assertEqual(True, response)

    @responses.activate
    @_test_update_delete_test_factory
    def test_update_failure_http_error(self, acme_id, new_name):
        """
        The function should raise an HTTPError exception if the update failed.
        """

        api_url = self.get_acme_account_url(acme_id)

        # Setup the mocked response
        responses.add(responses.PUT, api_url, status=400)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(HTTPError, acme.update, acme_id, new_name)


class TestDelete(TestACMEAccount):
    """Test the .delete method."""

    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters.
        """

        acme = ACMEAccount(client=self.client)
        # missing acme_id
        self.assertRaises(TypeError, acme.delete)

    @responses.activate
    @_test_update_delete_test_factory
    def test_delete_success(self, acme_id):
        """The function should return True if the deletion succeeded."""

        api_url = self.get_acme_account_url(acme_id)

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=204)

        acme = ACMEAccount(client=self.client)
        response = acme.delete(acme_id)

        self.assertEqual(True, response)

    @responses.activate
    @_test_update_delete_test_factory
    def test_delete_failure_http_error(self, acme_id):
        """
        The function should raise an HTTPError exception if the deletion
        failed.
        """

        api_url = self.get_acme_account_url(acme_id)

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=400)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(HTTPError, acme.delete, acme_id)


def _test_add_remove_domains_test_factory(func):
    acme_id = 1234

    @wraps(func)
    def wrapped_func(self):
        acme_data = self.get_acme_account_data(acme_id, domains=[
            "example.com",
            "example.org"
        ])
        request_domains = acme_data["domains"]
        response_domains = ["example.com"]
        api_url = "{}/domains".format(self.get_acme_account_url(acme_id))
        if func.__name__.find("test_add") == 0:
            resp_key = "notAddedDomains"
        else:
            resp_key = "notRemovedDomains"
        args = (acme_id, api_url, request_domains,
                {resp_key: response_domains})
        return func(self, *args)
    return wrapped_func


class TestAddDomains(TestACMEAccount):
    """Test the .add_domains method."""

    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters or domains argument is not a list
        """

        acme = ACMEAccount(client=self.client)
        # missing acme_id, domains
        self.assertRaises(TypeError, acme.add_domains)
        # missing domains
        self.assertRaises(TypeError, acme.add_domains, 1234)
        # domains is not iterable
        self.assertRaises(TypeError, acme.add_domains, 1234, None)

    @responses.activate
    @_test_add_remove_domains_test_factory
    def test_add_domains_success(self, acme_id, api_url, req_domains, resp):
        """
        The function should return a dictionary containing a list of domains
        not added.
        """

        # Setup the mocked response
        responses.add(responses.POST, api_url, json=resp, status=200)

        acme = ACMEAccount(client=self.client)
        response = acme.add_domains(acme_id, req_domains)

        self.assertEqual(response, resp)

    @responses.activate
    @_test_add_remove_domains_test_factory
    def test_add_domains_failure_http_error(self, acme_id, api_url,
                                            req_domains, _):
        """
        The function should raise an HTTPError exception if the domain addition
        failed.
        """

        # Setup the mocked response
        responses.add(responses.POST, api_url, status=400)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(HTTPError, acme.add_domains, acme_id, req_domains)


class TestRemoveDomains(TestACMEAccount):
    """Test the .remove_domains method."""

    def test_need_params(self):
        """
        The function should raise an exception when called without required
        parameters or domains argument is not a list
        """

        acme = ACMEAccount(client=self.client)
        # missing acme_id, domains
        self.assertRaises(TypeError, acme.remove_domains)
        # missing domains
        self.assertRaises(TypeError, acme.remove_domains, 1234)
        # domains is not iterable
        self.assertRaises(TypeError, acme.remove_domains, 1234, None)

    @responses.activate
    @_test_add_remove_domains_test_factory
    def test_remove_domains_success(self, acme_id, api_url, req_domains, resp):
        """
        The function should return a dictionary containing a list of domains
        not removed.
        """

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, json=resp, status=200)

        acme = ACMEAccount(client=self.client)
        response = acme.remove_domains(acme_id, req_domains)

        self.assertEqual(response, resp)

    @responses.activate
    @_test_add_remove_domains_test_factory
    def test_remove_domains_failure_http_error(self, acme_id, api_url,
                                               req_domains, _):
        """
        The function should raise an HTTPError exception if the domain removal
        failed.
        """

        # Setup the mocked response
        responses.add(responses.DELETE, api_url, status=400)

        acme = ACMEAccount(client=self.client)

        self.assertRaises(HTTPError, acme.remove_domains, acme_id, req_domains)
