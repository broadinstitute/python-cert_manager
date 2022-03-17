# -*- coding: utf-8 -*-
"""Define the cert_manager._certificates.Certificates unit tests."""
# responses is too tricky for pylint, so ignore the false-positive errors generated.
# pylint: disable=no-member

import json

from requests.exceptions import HTTPError
import responses
from testtools import TestCase

from cert_manager._certificates import Certificates
from cert_manager._helpers import Pending

from .lib.testbase import ClientFixture


# pylint: disable=too-few-public-methods
class TestCertificates(TestCase):
    """Serve as a Base class for all tests of the Certificates class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        # Set some default values
        self.ep_path = "/test"
        self.api_version = "v1"
        self.api_url = f"{self.cfixt.base_url}{self.ep_path}/{self.api_version}"

        # Create a Certificate object to use in any tests that need one
        self.certobj = Certificates(client=self.client, endpoint=self.ep_path, api_version=self.api_version)

    @staticmethod
    def fake_csr():
        """Build a fake certificate signing request to use with tests"""
        data = "-----BEGIN CERTIFICATE REQUEST-----\n"
        for row in range(1, 18):
            char = chr(row + 64)
            data += f"{char * 64}\n"
        data += "-----END CERTIFICATE REQUEST-----\n"

        return data

    @staticmethod
    def fake_cert():
        """Build a fake certificate to use with tests"""
        data = "-----BEGIN CERTIFICATE-----\n"
        for row in range(1, 33):
            char = chr(row + 64)
            if row > 26:
                char = chr(row + 70)
            data += f"{char * 64}\n"
        data += "-----END CERTIFICATE-----\n"

        return data


class TestInit(TestCertificates):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        end = Certificates(client=self.client, endpoint=self.ep_path)

        # Check all the internal values
        self.assertEqual(end._client, self.client)  # pylint: disable=protected-access
        self.assertEqual(end._api_version, self.api_version)  # pylint: disable=protected-access
        self.assertEqual(end._api_url, self.api_url)  # pylint: disable=protected-access

    def test_version(self):
        """Parameters should be set correctly inside the class with a custom version."""
        version = "v2"
        api_url = f"{self.cfixt.base_url}{self.ep_path}/{version}"

        end = Certificates(client=self.client, endpoint=self.ep_path, api_version=version)

        # Check all the internal values
        self.assertEqual(end._client, self.client)  # pylint: disable=protected-access
        self.assertEqual(end._api_version, version)  # pylint: disable=protected-access
        self.assertEqual(end._api_url, api_url)  # pylint: disable=protected-access


class TestTypes(TestCertificates):
    """Test the types property."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_url = f"{self.api_url}/types"

        self.types_data = [
            {'id': 224, 'name': 'InCommon SSL (SHA-2)', 'terms': [365, 730]},
            {'id': 225, 'name': 'InCommon Intranet SSL (SHA-2)', 'terms': [365]},
            {'id': 227, 'name': 'InCommon Wildcard SSL Certificate (SHA-2)', 'terms': [365, 730]},
            {'id': 226, 'name': 'InCommon Multi Domain SSL (SHA-2)', 'terms': [365, 730]},
            {'id': 228, 'name': 'InCommon Unified Communications Certificate (SHA-2)', 'terms': [365, 730]},
            {'id': 98, 'name': 'Comodo EV Multi Domain SSL', 'terms': [365]},
            {'id': 229, 'name': 'Comodo EV Multi Domain SSL (SHA-2)', 'terms': [365, 730]},
            {'id': 215, 'name': 'IGTF Server Cert', 'terms': [365]},
            {'id': 283, 'name': 'IGTF Multi Domain', 'terms': [365]},
            {'id': 243, 'name': 'Comodo Elite SSL Certificate (FileMaker) (SHA-2)', 'terms': [365, 730]},
            {'id': 284, 'name': 'InCommon ECC', 'terms': [365, 730]},
            {'id': 286, 'name': 'InCommon ECC Multi Domain', 'terms': [365, 730]},
            {'id': 285, 'name': 'InCommon ECC Wildcard', 'terms': [365, 730]}
        ]

        self.types = {
            "InCommon SSL (SHA-2)": {"id": 224, "terms": [365, 730]},
            "InCommon Intranet SSL (SHA-2)": {"id": 225, "terms": [365]},
            "InCommon Wildcard SSL Certificate (SHA-2)": {"id": 227, "terms": [365, 730]},
            "InCommon Multi Domain SSL (SHA-2)": {"id": 226, "terms": [365, 730]},
            "InCommon Unified Communications Certificate (SHA-2)": {"id": 228, "terms": [365, 730]},
            "Comodo EV Multi Domain SSL": {"id": 98, "terms": [365]},
            "Comodo EV Multi Domain SSL (SHA-2)": {"id": 229, "terms": [365, 730]},
            "IGTF Server Cert": {"id": 215, "terms": [365]},
            "IGTF Multi Domain": {"id": 283, "terms": [365]},
            "Comodo Elite SSL Certificate (FileMaker) (SHA-2)": {"id": 243, "terms": [365, 730]},
            "InCommon ECC": {"id": 284, "terms": [365, 730]},
            "InCommon ECC Multi Domain": {"id": 286, "terms": [365, 730]},
            "InCommon ECC Wildcard": {"id": 285, "terms": [365, 730]}
        }

    @responses.activate
    def test_success(self):
        """It should return data correctly if a 200-level status code is returned with data."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json=self.types_data, status=200)

        # Call the function
        resp = self.certobj.types

        # Verify all the query information
        self.assertEqual(resp, self.types)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_caching(self):
        """The second call to types returns a cached copy and doesn't make another API call."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json=self.types_data, status=200)

        # Call the function
        resp = self.certobj.types
        resp2 = self.certobj.types

        # Verify all the query information
        self.assertEqual(resp, self.types)
        self.assertEqual(resp2, self.types)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json={"description": "some error"}, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, getattr, self.certobj, "types")

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestCustomFields(TestCertificates):
    """Test the custom_fields properties."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_url = f"{self.api_url}/customFields"

        self.cf_data = [
            [{"id": 57, "name": "testName", "mandatory": True}]
        ]

    @responses.activate
    def test_success(self):
        """It should return data correctly if a 200-level status code is returned with data."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json=self.cf_data, status=200)

        # Call the function
        resp = self.certobj.custom_fields

        # Verify all the query information
        self.assertEqual(resp, self.cf_data)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_empty(self):
        """It should return an empty list if no custom fields were found."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json=[], status=200)

        # Call the function
        resp = self.certobj.custom_fields

        # Verify all the query information
        self.assertEqual(resp, [])
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json={"description": "some error"}, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, getattr, self.certobj, "custom_fields")

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestCollect(TestCertificates):
    """Test the collect method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_id = 121212
        self.test_type = "x509CO"
        self.test_url = f"{self.api_url}/collect/{self.test_id}/{self.test_type}"

        self.test_cert = TestCollect.fake_cert()

    @responses.activate
    def test_success(self):
        """It should return a certificate if a 200-level status code is returned with data."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, body=self.test_cert, status=200)

        # Call the function
        resp = self.certobj.collect(cert_id=self.test_id, cert_format=self.test_type)

        # Verify all the query information
        self.assertEqual(resp, self.test_cert)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_pending(self):
        """It should raise a Pending exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, body="", status=404)

        # Call the function, expecting an exception
        self.assertRaises(Pending, self.certobj.collect, self.test_id, self.test_type)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_no_params(self):
        """It should raise an Exception if no parameters are used."""
        # Call the function, expecting an exception
        self.assertRaises(Exception, self.certobj.collect)

    def test_no_type(self):
        """It should raise an Exception if no cert_format is provided."""
        # Call the function, expecting an exception
        self.assertRaises(Exception, self.certobj.collect, self.test_id)

    def test_no_id(self):
        """It should raise an Exception if no cert_id is provided."""
        # Call the function, expecting an exception
        self.assertRaises(Exception, self.certobj.collect, cert_format=self.test_type)

    def test_blank_params(self):
        """It should raise an Exception if both parameters are blank."""
        # Call the function, expecting an exception
        self.assertRaises(Exception, self.certobj.collect, cert_id=None, cert_format=None)

    def test_bad_type(self):
        """It should raise an Exception if the cert_format is not recognized."""
        # Call the function, expecting an exception
        self.assertRaises(Exception, self.certobj.collect, cert_id=self.test_id, cert_format="x509OC")


class TestEnroll(TestCertificates):
    """Test the enroll method."""
    # pylint: disable=too-many-instance-attributes

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_ct_name = "InCommon SSL (SHA-2)"
        self.test_term = 365
        self.test_org = 1234
        self.test_san = "blah.foo,baz.com"
        self.test_url = f"{self.api_url}/enroll"
        self.test_external_requester = "email@domain.com"
        self.test_cf = [{"name": "testName", "value": "testValue"}]

        self.test_csr = TestEnroll.fake_csr()
        self.test_result = {"renewId": "xwL9Mux8-eLNTsweYYv86Z7r", "sslId": 999}

        # This also needs to get types, so we'll need to mock that call too
        self.test_types_url = f"{self.api_url}/types"
        self.types_data = [
            {'id': 224, 'name': 'InCommon SSL (SHA-2)', 'terms': [365, 730]},
        ]

        # This also needs to get custom fields, so we'll mock out that call too
        self.test_customfields_url = f"{self.api_url}/customFields"
        self.cf_data = [
            {"id": 57, "name": "testName", "mandatory": False},
            {"id": 59, "name": "testName2", "mandatory": False},
        ]
        self.cf_data_mandatory = [
            {"id": 57, "name": "testName", "mandatory": True},
            {"id": 59, "name": "testName2", "mandatory": False},
        ]

    @staticmethod
    def fake_csr():
        """Build a fake certificate signing request to use with tests"""
        data = "-----BEGIN CERTIFICATE REQUEST-----\n"
        for row in range(1, 18):
            char = chr(row + 64)
            data += f"{char * 64}\n"
        data += "-----END CERTIFICATE REQUEST-----\n"

        return data

    @responses.activate
    def test_success(self):
        """It should return JSON if a 200-level status code is returned with data."""
        # Setup the mocked responses
        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)

        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function
        resp = self.certobj.enroll(cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
                                   org_id=self.test_org, external_requester=self.test_external_requester)

        # Mock up the data that should be sent with the post
        post_data = {
            "orgId": self.test_org, "csr": self.test_csr.rstrip(), "subjAltNames": None, "certType": 224,
            "numberServers": 1, "serverType": -1, "term": self.test_term,
            "comments": f"Enrolled by {self.client.user_agent}", "externalRequester": self.test_external_requester
        }
        post_json = json.dumps(post_data)

        # Verify all the query information
        self.assertEqual(resp, self.test_result)
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)
        self.assertEqual(responses.calls[2].request.url, self.test_url)
        self.assertEqual(responses.calls[2].request.body, post_json.encode("utf-8"))

    @responses.activate
    def test_san_list(self):
        """It should correctly handle a list of SANs."""
        # Setup the mocked responses
        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)

        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        san_list = self.test_san.split(",")

        # Call the function
        resp = self.certobj.enroll(cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
                                   org_id=self.test_org, external_requester=self.test_external_requester,
                                   subject_alt_names=san_list)

        # Mock up the data that should be sent with the post
        post_data = {
            "orgId": self.test_org, "csr": self.test_csr.rstrip(), "subjAltNames": self.test_san, "certType": 224,
            "numberServers": 1, "serverType": -1, "term": self.test_term,
            "comments": f"Enrolled by {self.client.user_agent}", "externalRequester": self.test_external_requester
        }
        post_json = json.dumps(post_data)

        # Verify all the query information
        self.assertEqual(resp, self.test_result)
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)
        self.assertEqual(responses.calls[2].request.url, self.test_url)
        self.assertEqual(responses.calls[2].request.body, post_json.encode("utf-8"))

    @responses.activate
    def test_bad_cert_name(self):
        """It should raise an Exception if the cert_type_name was not found."""
        # Setup the mocked responses
        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        ct_name = "BadCert(SSL)"
        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=ct_name, csr=self.test_csr, term=self.test_term,
            org_id=self.test_org)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)

    @responses.activate
    def test_bad_term(self):
        """It should raise an Exception if the term was not valid."""
        # Setup the mocked responses
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        term = 1095
        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr, term=term,
            org_id=self.test_org)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)

    @responses.activate
    def test_mandatory_custom_fields_success(self):
        """It should return a 200-level status code if a mandatory custom field is included."""
        # Setup the mocked responses
        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data_mandatory, status=200)

        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function
        resp = self.certobj.enroll(cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
                                   org_id=self.test_org, external_requester=self.test_external_requester,
                                   custom_fields=self.test_cf)

        # Mock up the data that should be sent with the post
        post_data = {
            "orgId": self.test_org, "csr": self.test_csr.rstrip(), "subjAltNames": None, "certType": 224,
            "numberServers": 1, "serverType": -1, "term": self.test_term,
            "comments": f"Enrolled by {self.client.user_agent}", "externalRequester": self.test_external_requester,
            "customFields": self.test_cf
        }
        post_json = json.dumps(post_data)

        # Verify all the query information
        self.assertEqual(resp, self.test_result)
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)
        self.assertEqual(responses.calls[2].request.url, self.test_url)
        self.assertEqual(responses.calls[2].request.body, post_json.encode("utf-8"))

    @responses.activate
    def test_mandatory_custom_fields_missing(self):
        """It should raise an Exception if mandatory custom fields are missing """
        # Setup the mocked responses
        test_cf_missing_mandatory_field = [{"name": "testName2", "value": "testValue"}]

        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data_mandatory, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
            org_id=self.test_org, external_requester=self.test_external_requester,
            custom_fields=test_cf_missing_mandatory_field
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)

    @responses.activate
    def test_custom_fields_duplicate_keys(self):
        """It should raise an Exception if mandatory custom fields are missing """
        # Setup the mocked responses
        test_cf_duplicate_fields = [
            {"name": "testName", "value": "testValue"},
            {"name": "testName", "value": "testValue2"}
        ]

        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data_mandatory, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
            org_id=self.test_org, external_requester=self.test_external_requester,
            custom_fields=test_cf_duplicate_fields
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)

    @responses.activate
    def test_custom_fields_invalid(self):
        """It should raise an Exception if elements of the custom_fields list are anything other than dicts """
        # Setup the mocked responses
        test_cf_invalid = ["I'm not a dict, I'm a string!"]

        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)

        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
            org_id=self.test_org, external_requester=self.test_external_requester, custom_fields=test_cf_invalid
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)

    @responses.activate
    def test_custom_fields_keys_missing(self):
        """It should raise an Exception if a dict in the custom fields list is missing keys """
        # Setup the mocked responses
        test_cf_missing_keys = [{"name": "testName", "missingValue": True}]

        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
            org_id=self.test_org, external_requester=self.test_external_requester, custom_fields=test_cf_missing_keys
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)

    @responses.activate
    def test_custom_fields_key_invalid(self):
        """It should raise an Exception if a supplied custom field name doesn't exist """
        # Setup the mocked responses
        test_cf_invalid_name = [{"name": "someOtherName", "value": "testValue"}]

        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        # Call the function, expecting an exception
        self.assertRaises(
            Exception, self.certobj.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term,
            org_id=self.test_org, external_requester=self.test_external_requester, custom_fields=test_cf_invalid_name
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)


class TestRenew(TestCertificates):
    """Test the renew method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_id = 1234
        self.test_url = f"{self.api_url}/renewById/{self.test_id}"

    @responses.activate
    def test_success(self):
        """It should return JSON if a 200-level status code is returned with data."""
        # Setup the mocked responses
        responses.add(responses.POST, self.test_url, json={}, status=204)

        # Call the function
        resp = self.certobj.renew(cert_id=self.test_id)

        # Verify all the query information
        self.assertEqual(resp, {})
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, json={}, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.certobj.renew, self.test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestRevoke(TestCertificates):
    """Test the revoke method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_id = 1234
        self.test_url = f"{self.api_url}/revoke/{self.test_id}"

    @responses.activate
    def test_success(self):
        """It should return an empty dict if a 204 No Content response is returned."""
        # Setup the mocked responses
        responses.add(responses.POST, self.test_url, body='', status=204)

        # Call the function
        resp = self.certobj.revoke(cert_id=self.test_id, reason="Because")

        post_json = json.dumps({"reason": "Because"})

        # Verify all the query information
        self.assertEqual(resp, {})
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(responses.calls[0].request.body, post_json.encode("utf-8"))

    @responses.activate
    def test_no_reason(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Call the function, expecting an exception
        self.assertRaises(Exception, self.certobj.revoke, self.test_id)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, json={}, status=404)

        # Call the function, expecting an exception
        self.assertRaises(HTTPError, self.certobj.revoke, cert_id=self.test_id, reason="Because")

        post_json = json.dumps({"reason": "Because"})

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(responses.calls[0].request.body, post_json.encode("utf-8"))


class TestReplace(TestCertificates):
    """Test the replace method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_id = 1234
        self.test_cn = "test.foo.bar"
        self.test_reason = "Because"
        self.test_san = "test.blah.foo,test.baz.com"
        self.test_csr = TestReplace.fake_csr()

        self.test_url = f"{self.api_url}/replace/{self.test_id}"

    @responses.activate
    def test_success(self):
        """It should return an empty dict if a 204 No Content response is returned."""
        # Setup the mocked responses
        responses.add(responses.POST, self.test_url, body='', status=200)

        # Call the function
        resp = self.certobj.replace(cert_id=self.test_id, csr=self.test_csr, common_name=self.test_cn,
                                    reason=self.test_reason)

        # Mock up the data that should be sent with the post
        post_data = {"csr": self.test_csr, "commonName": self.test_cn, "subjectAlternativeNames": None,
                     "reason": self.test_reason}
        post_json = json.dumps(post_data)

        # Verify all the query information
        self.assertEqual(resp, {})
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(responses.calls[0].request.body, post_json.encode("utf-8"))

    @responses.activate
    def test_san_string(self):
        """It should correctly handle a list of SANs."""
        # Setup the mocked responses
        responses.add(responses.POST, self.test_url, body='', status=200)

        san_list = self.test_san.split(",")

        # Call the function
        resp = self.certobj.replace(cert_id=self.test_id, csr=self.test_csr, common_name=self.test_cn,
                                    reason=self.test_reason, subject_alt_names=self.test_san)

        # Mock up the data that should be sent with the post
        post_data = {"csr": self.test_csr, "commonName": self.test_cn, "subjectAlternativeNames": san_list,
                     "reason": self.test_reason}
        post_json = json.dumps(post_data)

        # Verify all the query information
        self.assertEqual(resp, {})
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(responses.calls[0].request.body, post_json.encode("utf-8"))

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked responses
        responses.add(responses.POST, self.test_url, json={}, status=404)

        # Call the function
        self.assertRaises(HTTPError, self.certobj.replace, cert_id=self.test_id, csr=self.test_csr,
                          common_name=self.test_cn, reason=self.test_reason)

        # Mock up the data that should be sent with the post
        post_data = {"csr": self.test_csr, "commonName": self.test_cn, "subjectAlternativeNames": None,
                     "reason": self.test_reason}
        post_json = json.dumps(post_data)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(responses.calls[0].request.body, post_json.encode("utf-8"))
