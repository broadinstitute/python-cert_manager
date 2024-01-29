"""Define the cert_manager.report.Report class."""

import logging

from requests.exceptions import HTTPError

from ._endpoint import Endpoint

LOGGER = logging.getLogger(__name__)


class Report(Endpoint):
    """Query the Sectigo Cert Manager REST API for Report data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/report", api_version=api_version)

    def get(self, report_name, **kwargs):
        """Get any available reports provided in the REST Sctigo API.

        :param str report_name: Name of report based on the api url suffix
        :param dict kwargs: Additional fields that will be passed to the API

        Search fields for reports can be found in the Sectigo API Documentation.
        Additional request fields are documented in Sectigo API Documentation
        https://sectigo.com/faqs/detail/Sectigo-Certificate-Manager-SCM-REST-API/kA01N000000XDkE

        return dict: The report data
        """
        data = {}
        for key, value in kwargs.items():
            data[key] = value

        # split report name where path includes sub paths, ie: "discovery/log"
        report_name_list = report_name.split('/')
        url = self._url(*report_name_list)
        for key, value in kwargs.items():
            data[key] = value

        try:
            result = self._client.post(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == self._capture_err_code:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()

    # Commonly used re
    def get_ssl_certs(self, **kwargs):
        """Get the specific SSL Certificate report.

        The API provides several search fields commonly used available through kwargs:
            "from": ISO date of start of date range
            "to": ISO date of start of date range
            "certificateDateAttribute": Date type(number) to search on: 2=revocation,3=expiration,4=requested,5=issuance
            "certificateStatus": Cert status(number): 0=Any,1=Requested,2=Issued,3=Revoked,4=Expired
            "organizationIds": Array of unique Org IDs to fiter search
           Other fields:  certificateRequestSource, serialNumberFormat, externalRequester

        return dict: The report data
        """
        report_url = "ssl-certificates"

        result = self.get(report_url, **kwargs)

        return result

    def get_client_certs(self, **kwargs):
        """Get the specific Client Certificate report.

        The API provides several search fields commonly used available through kwargs:
            "from": ISO date of start of date range
            "to": ISO date of start of date range
            "certificateDateAttribute": Date type(number) to search on: 0=entrolled, 1=downloaded,2=revocation,3=expired
            "certificateStatus": Cert status(number): 0=Any,2=Enrolled-downloaded,3=Revoked,4=Expired,
                                              5=Enrolled-Pending_download,6=not_enrolled
            "organizationIds": Array of unique Org IDs to fiter search

        return dict: The report data
        """
        report_url = "client-certificates"

        return self.get(report_url, **kwargs)

    def get_device_certs(self, **kwargs):
        """Get the specific Device Certificate report.

        The API provides several search fields commonly used available through kwargs:
            "from": ISO date of start of date range
            "to": ISO date of start of date range
            "certificateDateAttribute": Date type(number) to search on: 2=revocation,3=expired,4=requested,5=issuance
            "certificateStatus": Cert status(number): 0=Any,2=Enrolled-downloaded,,3=Revoked,4=Expired,
                                   5=Enrolled-Pending_download, 6=not_enrolled
            "organizationIds": Array of unique Org IDs to fiter search

        return dict: The report data
        """
        report_url = "device-certificates"

        return self.get(report_url, **kwargs)

    def get_activity(self, **kwargs):
        """Get the specific Activity report.

        The API provides 2 search fields to filter date range through kwargs:
            "from": ISO date of start of date range
            "to": ISO date of start of date range

        return dict: The report data
        """
        report_url = "activity"

        return self.get(report_url, **kwargs)

    def get_domains(self):
        """Get the specific Domains report.

        return dict: The report data
        """
        report_url = "domains"

        return self.get(report_url)
