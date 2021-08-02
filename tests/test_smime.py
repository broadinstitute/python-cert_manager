# -*- coding: utf-8 -*-
"""Define the cert_manager.ssl.SMIME unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=invalid-name

import json
import responses
from requests import HTTPError
from testtools import TestCase

from cert_manager.smime import SMIME
from cert_manager._helpers import Pending, Revoked

from .lib.testbase import ClientFixture
from .test_certificates import TestCertificates

# pylint: disable=too-few-public-methods
class TestSMIME(TestCase):
    """Serve as a Base class for all tests of the Certificates class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        # Set some default values
        self.ep_path = "/smime"
        self.api_version = "v1"
        self.api_url = self.cfixt.base_url + self.ep_path + "/" + self.api_version


class TestInit(TestSMIME):
    """Test the class initializer."""

    def test_defaults(self):
        """Parameters should be set correctly inside the class using defaults."""
        end = SMIME(client=self.client)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, self.api_version)
        self.assertEqual(end._api_url, self.api_url)

    def test_version(self):
        """Parameters should be set correctly inside the class with a custom version."""
        version = "v2"
        api_url = self.cfixt.base_url + self.ep_path + "/" + version

        end = SMIME(client=self.client, api_version=version)

        # Check all the internal values
        self.assertEqual(end._client, self.client)
        self.assertEqual(end._api_version, version)
        self.assertEqual(end._api_url, api_url)


class TestList(TestSMIME):
    """Test the class list method."""

    @responses.activate
    def test_defaults(self):
        """The function should return all client certificate records"""
        # Setup the mocked response
        test_url = f"{self.api_url}?size=200&position=0"
        test_result = [
            {"subject": "fry@example.org"}, {"subject": "leila@example.org"},
            {"subject": "farnsworth@example.org"}, {"subject": "bender@example.org"}
        ]
        responses.add(responses.GET, test_url, json=test_result, status=200)

        smime = SMIME(client=self.client)
        result = smime.list()

        # Verify all the query information
        data = []
        for res in result:
            data.append(res)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, test_url)
        self.assertEqual(data, test_result)


class TestListByEmail(TestSMIME):
    """Test the class list_by_email method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_email = "zoidberg@example.org"
        self.api_version = "v2"     # this endpoint is in v2
        self.api_url = self.cfixt.base_url + self.ep_path + "/" + self.api_version
        self.test_url = f"{self.api_url}/byPersonEmail/{self.test_email}"
        
        self.test_result = [
            {"subject": "fry@example.org"}, {"subject": "leila@example.org"},
            {"subject": "farnsworth@example.org"}, {"subject": "bender@example.org"}
        ]

    @responses.activate
    def test_defaults(self):
        """The function should raise an exception when no email is passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(Exception, smime.list_by_email)

    @responses.activate
    def test_success(self):
        """The function should return the list of certificates of an email"""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json=self.test_result, status=200)

        smime = SMIME(client=self.client)
        result = smime.list_by_email(email=self.test_email)

        # Verify all the query information
        data = []
        for res in result:
            data.append(res)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
        self.assertEqual(data, self.test_result)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json={}, status=404)

        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(HTTPError, smime.list_by_email, email=self.test_email)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestEnroll(TestSMIME):
    """Test the enroll method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_email = "zoidberg.example.org"
        self.test_first_name = "Dr."
        self.test_last_name = "Zoidberg"

        self.test_org = 1234
        self.test_term = 365

        # This also needs to get types, so we'll need to mock that call too
        self.test_types_url = f"{self.api_url}/types"
        self.types_data = [
            {
                "id":15702,"name":"Sectigo SMIME","description":"","terms":[365],
                "keyTypes":{"RSA":["2048","3072","4096","8192"]},"useSecondaryOrgName":False
            },
        ]
        self.test_ct_name = "Sectigo SMIME"

        # This also needs to get custom fields, so we'll mock out that call too
        self.test_customfields_url = self.api_url + "/customFields"
        self.cf_data = [
            {"id": 57, "name": "testName", "mandatory": False},
            {"id": 59, "name": "testName2", "mandatory": False},
        ]
        self.cf_data_mandatory = [
            {"id": 57, "name": "testName", "mandatory": True},
            {"id": 59, "name": "testName2", "mandatory": False},
        ]
        self.test_cf = [{"name": "testName", "value": "testValue"}]

        self.test_url = f"{self.api_url}/enroll"
        self.test_csr = TestCertificates.fake_csr()

        self.test_result = json.dumps({"orderNumber":123456,"backendCertId":"123456"})

    def test_defaults(self):
        """The function should raise an exception when no params are passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(Exception, smime.enroll)

    @responses.activate
    def test_success(self):
        """It should return a JSON if a 200-level status code is returned with data."""
        # Setup the mocked response
        # We need to mock the /types and /customFields URLs as well
        # since SMIME.types and SMIME.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)

        responses.add(responses.POST, self.test_url, body=self.test_result, status=200)

        # Call the function
        smime = SMIME(client=self.client)
        resp = smime.enroll(
            cert_type_name=self.test_ct_name, csr=self.test_csr, term=self.test_term, org_id=self.test_org,
            email=self.test_email, first_name=self.test_first_name, last_name=self.test_last_name,
        )

        # Verify all the query information
        self.assertEqual(json.dumps(resp), self.test_result)
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)
        self.assertEqual(responses.calls[2].request.url, self.test_url)

    @responses.activate
    def test_bad_cert_type_name(self):
        """It should raise an Exception if the cert_type_name was not found."""
        # Setup the mocked responses
        # We need to mock the /types and /customFields URLs as well
        # since Certificates.types and Certificate.custom_fields are called from enroll
        responses.add(responses.GET, self.test_types_url, json=self.types_data, status=200)
        responses.add(responses.GET, self.test_customfields_url, json=self.cf_data, status=200)
        responses.add(responses.POST, self.test_url, json=self.test_result, status=200)

        ct_name = "BadCert(SSL)"
        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(
            Exception, smime.enroll, cert_type_name=ct_name, csr=self.test_csr,
            term=self.test_term, org_id=self.test_org, email=self.test_email,
            first_name=self.test_first_name, last_name=self.test_last_name,
        )

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
        smime = SMIME(client=self.client)
        self.assertRaises(
            Exception, smime.enroll, cert_type_name=self.test_ct_name, csr=self.test_csr,
            term=term, org_id=self.test_org, email=self.test_email,
            first_name=self.test_first_name, last_name=self.test_last_name,
        )
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
        smime = SMIME(client=self.client)
        resp = smime.enroll(
            cert_type_name=self.test_ct_name, csr=self.test_csr,
            term=self.test_term, org_id=self.test_org, email=self.test_email,
            first_name=self.test_first_name, last_name=self.test_last_name, custom_fields=self.test_cf,
        )

        # Verify all the query information
        self.assertEqual(resp, self.test_result)
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(responses.calls[0].request.url, self.test_types_url)
        self.assertEqual(responses.calls[1].request.url, self.test_customfields_url)
        self.assertEqual(responses.calls[2].request.url, self.test_url)

class TestCollect(TestSMIME):
    """Test the collect method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_id = 121212
        self.test_url = f"{self.api_url}/collect/{self.test_id}"

        self.test_cert = TestCertificates.fake_cert()

    def test_defaults(self):
        """The function should raise an exception when no certificate id is passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(Exception, smime.collect)

    @responses.activate
    def test_success(self):
        """It should return a certificate if a 200-level status code is returned with data."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, body=self.test_cert, status=200)

        # Call the function
        smime = SMIME(client=self.client)
        resp = smime.collect(cert_id=self.test_id)

        # Verify all the query information
        self.assertEqual(resp, self.test_cert)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    def test_no_cert_id(self):
        """The function should raise a ValueError exception if no cert_id is passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(ValueError, smime.collect, None)  

    @responses.activate
    def test_pending(self):
        """It should raise a Pending exception if an Http error with the pending code in the body is returned."""
        # Setup the mocked response
        body = json.dumps({"code": Pending.CODE, "description": "Certificate is not collectable."})
        responses.add(responses.GET, self.test_url, body=body, status=400)

        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(Pending, smime.collect, self.test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_revoked(self):
        """It should raise a Revoked exception if an Http error with the pending code in the body is returned."""
        # Setup the mocked response
        body = json.dumps({"code": Revoked.CODE, "description": "The Certificate has been revoked!"})
        responses.add(responses.GET, self.test_url, body=body, status=400)

        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(Pending, smime.collect, self.test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.GET, self.test_url, json={}, status=400)

        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(HTTPError, smime.collect, self.test_id)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestReplace(TestSMIME):
    """Test the replace method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_cert_id = 1234
        self.api_version = "v2"     # this endpoint is in v2
        self.api_url = self.cfixt.base_url + self.ep_path + "/" + self.api_version
        self.test_url = f"{self.api_url}/replace/order/{self.test_cert_id}"
        self.test_csr = TestCertificates.fake_csr()

    def test_defaults(self):
        """The function should raise an exception when no params are passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(Exception, smime.replace)

    @responses.activate
    def test_success(self):
        """It should return nothing if a 200-level status code is returned"""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, body='', status=204)

        # Call the function
        smime = SMIME(client=self.client)
        smime.replace(
            cert_id=self.test_cert_id, csr=self.test_csr,
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestRevoke(TestSMIME):
    """Test the revoke by cert_id method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_cert_id = 1234
        self.test_url = f"{self.api_url}/revoke/order/{self.test_cert_id}"

    def test_defaults(self):
        """The function should raise an exception when no params are passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(Exception, smime.revoke)

    @responses.activate
    def test_success(self):
        """It should return nothing if a 200-level status code is returned"""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, body='', status=204)

        # Call the function
        smime = SMIME(client=self.client)
        smime.revoke(
            cert_id=self.test_cert_id, reason="Beacause",
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    def test_no_cert_id(self):
        """The function should raise a ValueError exception if no cert_id is passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(ValueError, smime.revoke, None)

    def test_no_reason(self):
        """It should raise a ValueError exception if the reason is left empty."""
        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(ValueError, smime.revoke, self.test_cert_id)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, json={}, status=404)

        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(HTTPError, smime.revoke, cert_id=self.test_cert_id, reason="Because")

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)


class TestRevokeByEmail(TestSMIME):
    """Test the revoke by email method."""

    def setUp(self):
        """Initialize the class."""
        super().setUp()

        self.test_email = "mom@example.org"
        self.test_url = f"{self.api_url}/revoke"

    def test_defaults(self):
        """The function should raise an exception when no params are passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(Exception, smime.revoke_by_email)

    @responses.activate
    def test_success(self):
        """It should return nothing if a 200-level status code is returned"""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, body='', status=204)

        # Call the function
        smime = SMIME(client=self.client)
        smime.revoke_by_email(
            email=self.test_email, reason="Beacause",
        )

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)

    def test_no_email(self):
        """The function should raise a ValueError exception if no email is passed"""
        smime = SMIME(client=self.client)
        self.assertRaises(ValueError, smime.revoke_by_email, "")

    def test_no_reason(self):
        """It should raise a ValueError exception if the reason is left empty"""
        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(ValueError, smime.revoke_by_email, self.test_email)

    @responses.activate
    def test_failure(self):
        """It should raise an HTTPError exception if an error status code is returned."""
        # Setup the mocked response
        responses.add(responses.POST, self.test_url, json={}, status=404)

        # Call the function, expecting an exception
        smime = SMIME(client=self.client)
        self.assertRaises(HTTPError, smime.revoke_by_email, email=self.test_email, reason="Because")

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, self.test_url)
