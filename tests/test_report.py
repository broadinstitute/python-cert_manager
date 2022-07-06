# -*- coding: utf-8 -*-
"""Define the cert_manager.report.Report unit tests."""
# Don't warn about things that happen as that is part of unit testing
# pylint: disable=protected-access
# pylint: disable=no-member

import json

from testtools import TestCase

import responses

from cert_manager.report import Report
from .lib.testbase import ClientFixture


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class TestReport(TestCase):
    """Serve as a Base class for all tests of the Domain class."""

    def setUp(self):  # pylint: disable=invalid-name
        """Initialize the class."""
        # Call the inherited setUp method
        super().setUp()

        # Make sure the Client fixture is created and setup
        self.cfixt = self.useFixture(ClientFixture())
        self.client = self.cfixt.client

        self.api_url = f"{self.cfixt.base_url}/report/v1"

        # Setup a test response one would expect normally
        self.valid_activity_report_response = {
            "statusCode": 0,
            "reports": [
                {
                    "id": 100500,
                    "action": {
                        "id": 42,
                        "actionName": "admin: login success"
                    },
                    "admin": {
                        "login": "admin",
                        "fullName": "MRAO admin",
                        "email": "admin@somecompany.com"
                    },
                    "accessMethod": "UI access",
                    "date": "2022-03-11T00:00:00.000+02:00",
                    "address": "37.214.176.150"
                }
            ]
        }

        self.valid_ssl_cert_report_response = {
            "statusCode": 0,
            "reports": [
                {
                    "id": 42,
                    "type": "Extended Wildcard Premium Customized",
                    "typeId": 1046,
                    "orgId": 51,
                    "commonName": "gov.bb",
                    "subjAltNames": "dNSName=www.gov.bb",
                    "status": "Requested",
                    "requester": "admin@somecompany.com",
                    "organizationName": "Office of Strategic Influence",
                    "serverType": "OTHER",
                    "requestedVia": "API",
                    "term": 365,
                    "comments": "Enrolled by urgent request",
                    "requested": "2019-01-02T00:00:00.000+02:00",
                    "serialNumber": "",
                    "city": "Bridgetown",
                    "state": "St. Michael",
                    "country": "BB",
                    "publicKeyAlg": "RSA",
                    "publicKeySize": "2048",
                    "publicKeyType": "RSA - 2048",
                    "customFields": [
                        {
                            "name": "Priority",
                            "value": "Medium"
                        }
                    ]
                }
            ]
        }

        self.valid_client_cert_report_response = {
            "statusCode": 0,
            "reports": [
                {
                    "id": 42,
                    "person": {
                        "name": "MRAO admin",
                        "email": "admin@somecompany.com",
                        "guid": "b89499c0-6329-359e-8a9f-1a42a7afa0c3"
                    },
                    "organization": {
                        "name": "Office of Strategic Influence",
                        "address1": "8780 Elvis Alive Drive",
                        "address2": "Las Vegas, NV 89166, USA",
                        "address3": ""
                    },
                    "subject": "MRAO admin<admin@somecompany.com>",
                    "email": "admin@somecompany.com",
                    "orderNumber": 100500,
                    "backendCertId": "100500",
                    "enrolled": "2021-03-12T00:00:00.000+02:00",
                    "expire": "2022-03-12T00:00:00.000+02:00",
                    "enrollType": "Self Enroll"
                }
            ]
        }

        self.valid_device_cert_report_response = {
            "statusCode": 0,
            "reports": [
                {
                    "id": 439,
                    "commonName": "34356576543tnl54hgnu49u90g",
                    "organization": {
                        "name": "org4Test",
                        "address1": "Deribasovskaya 1",
                        "address2": "Street 2",
                        "address3": "Street 3"
                    },
                    "deviceCertStatus": "Issued",
                    "subject": "C=UA,ST=Odessa,L=Odessa,O=Test,OU=Test,CN=Test,E=test@test.test",
                    "email": "Someone@nobody.comodo.od.ua",
                    "city": "",
                    "state": "",
                    "country": "",
                    "orderNumber": 100500,
                    "backendCertId": "100500",
                    "serialNumber": "",
                    "certTypeName": "Device cert SASP -1986260034",
                    "expire": "2023-01-21T20:55:18.572+02:00",
                    "enrollType": "API",
                    "keyAlgorithm": "RSA",
                    "keySize": 2048,
                    "keyType": "RSA - 2048",
                    "signatureAlgorithm": ""
                }
            ]
        }

        self.valid_domain_response = {
            "statusCode": 0,
            "reports": [
                {
                    "id": 42,
                    "name": "gov.bb",
                    "status": "ACTIVE",
                    "requested": "2019-01-02T00:00:00.000+02:00",
                    "dcvStatus": "Validated",
                    "stickyUntil": "2019-01-03T00:00:00.000+02:00"
                }
            ]
        }

        # Setup JSON to return in an error
        self.error_response = {"description": "report error"}


class TestInit(TestReport):
    """Test the class initializer."""

    @responses.activate
    def test_param(self):
        """The URL should change if api_version is passed as a parameter."""
        # Set a new version
        version = "v3"
        api_url = f"{self.cfixt.base_url}/report/{version}/activity"

        # Setup the mocked response
        responses.add(responses.POST, api_url, json=self.valid_activity_report_response, status=200)

        report = Report(client=self.client, api_version=version)
        data = report.get("activity")
        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)

        self.assertEqual(data, self.valid_activity_report_response)

    def test_need_client(self):
        """The class should raise an exception without a client parameter."""
        self.assertRaises(TypeError, Report)


class TestGet(TestReport):
    """Test the .get method."""

    @responses.activate
    def test_need_report_name(self):
        """The function should raise an exception without an report_name parameter."""

        report = Report(client=self.client)
        self.assertRaises(TypeError, report.get)

    @responses.activate
    def test_bad_http(self):
        """
        The function should raise an HTTPError exception,
            if domains cannot be retrieved from the API.
        """
        # Setup the mocked response
        api_url = f"{self.api_url}/ssl-cert"

        responses.add(responses.POST, api_url, json=self.error_response, status=400)

        report = Report(client=self.client)
        report_args = {
            "report_name": "ssl-cert"
        }
        self.assertRaises(ValueError, report.get, **report_args)

        # Verify all the query information
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)

    @responses.activate
    def test_report_parm_ssl_cert(self):
        """The function should return data for the chosen report."""

        api_url = f"{self.api_url}/ssl-certificates"

        # Setup the mocked response
        responses.add(responses.POST, api_url, json=self.valid_ssl_cert_report_response, status=200)

        report = Report(client=self.client)

        data = report.get("ssl-certificates")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_ssl_cert_report_response)

    @responses.activate
    def test_report_parm_ssl_cert_filter(self):
        """The function should return data for chosen report with organization filter."""

        api_url = f"{self.api_url}/ssl-certificates"
        organization_array = ['51', '52']
        filter_data = {"organizationIds": organization_array}

        # Setup the mocked response
        responses.add(
            responses.POST,
            api_url,
            json=self.valid_ssl_cert_report_response,
            match=[responses.matchers.json_params_matcher(filter_data)],
            status=200
        )

        report = Report(client=self.client)
        # run test using keyword parameters
        data = report.get("ssl-certificates", organizationIds=organization_array)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_ssl_cert_report_response)
        self.assertEqual(json.loads(responses.calls[0].request.body.decode('utf-8')), filter_data)


class TestGetSSLCert(TestReport):
    """Test the .get_ssl_certs method."""

    @responses.activate
    def test_report_ssl_cert(self):
        """The function should return data for the SSL Cert report."""

        api_url = f"{self.api_url}/ssl-certificates"

        # Setup the mocked response
        responses.add(responses.POST, api_url, json=self.valid_ssl_cert_report_response, status=200)

        report = Report(client=self.client)
        data = report.get_ssl_certs()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_ssl_cert_report_response)

    @responses.activate
    def test_report_ssl_cert_filter(self):
        """The function should return data for the SSL Cert report."""

        api_url = f"{self.api_url}/ssl-certificates"
        organization_array = ['51', '52']
        filter_data = {"organizationIds": organization_array}

        # Setup the mocked response
        responses.add(
            responses.POST,
            api_url,
            json=self.valid_ssl_cert_report_response,
            match=[responses.matchers.json_params_matcher(filter_data)],
            status=200
        )

        report = Report(client=self.client)
        data = report.get_ssl_certs(**filter_data)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_ssl_cert_report_response)
        self.assertEqual(json.loads(responses.calls[0].request.body.decode('utf-8')), filter_data)


class TestGetActivity(TestReport):
    """Test the .get_activity method."""

    @responses.activate
    def test_report_activity(self):
        """The function should return data for the Activity report."""

        api_url = f"{self.api_url}/activity"

        # Setup the mocked response
        responses.add(responses.POST, api_url, json=self.valid_activity_report_response, status=200)

        report = Report(client=self.client)
        data = report.get_activity()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_activity_report_response)

    @responses.activate
    def test_report_activity_filter(self):
        """The function should return data for the Activity report with search filter."""

        api_url = f"{self.api_url}/activity"
        filter_data = {"from": "2022-03-07T00:00:00.000Z", "to": "2022-03-16T00:00:00.000Z"}

        # Setup the mocked response
        responses.add(
            responses.POST,
            api_url,
            json=self.valid_activity_report_response,
            match=[responses.matchers.json_params_matcher(filter_data)],
            status=200
        )

        report = Report(client=self.client)
        data = report.get_activity(**filter_data)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_activity_report_response)
        self.assertEqual(json.loads(responses.calls[0].request.body.decode('utf-8')), filter_data)


class TestGetDomains(TestReport):
    """Test the .get_domains method."""

    @responses.activate
    def test_report_domains(self):
        """The function should return data for the Domains report."""

        api_url = f"{self.api_url}/domains"

        # Setup the mocked response
        responses.add(responses.POST, api_url, json=self.valid_domain_response, status=200)

        report = Report(client=self.client)
        data = report.get_domains()

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_domain_response)


class TestGetClientCert(TestReport):
    """Test the .get_client_certs method."""

    @responses.activate
    def test_report_client_certs_filter(self):
        """The function should return data for the Client Certs report with search filter."""

        api_url = f"{self.api_url}/client-certificates"
        filter_data = {
            "from": "2022-03-07T00:00:00.000Z",
            "to": "2022-03-16T00:00:00.000Z",
            "certificateDateAttribute": 3
        }

        # Setup the mocked response
        responses.add(
            responses.POST,
            api_url,
            json=self.valid_client_cert_report_response,
            match=[responses.matchers.json_params_matcher(filter_data)],
            status=200
        )

        report = Report(client=self.client)
        # test this using keyword format
        data = report.get_client_certs(**filter_data)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_client_cert_report_response)
        self.assertEqual(json.loads(responses.calls[0].request.body.decode('utf-8')), filter_data)


class TestGetDeviceCert(TestReport):
    """Test the .get_device_certs method."""

    @responses.activate
    def test_report_device_certs_filter(self):
        """The function should return data for the Device Certs report with search filter."""

        api_url = f"{self.api_url}/device-certificates"
        filter_data = {"certificateStatus": 2}

        # Setup the mocked response
        responses.add(
            responses.POST,
            api_url,
            json=self.valid_device_cert_report_response,
            match=[responses.matchers.json_params_matcher(filter_data)],
            status=200
        )

        report = Report(client=self.client)
        # test passing using keyword format
        data = report.get_device_certs(certificateStatus=2)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, api_url)
        self.assertEqual(data, self.valid_device_cert_report_response)
        self.assertEqual(json.loads(responses.calls[0].request.body.decode('utf-8')), filter_data)
