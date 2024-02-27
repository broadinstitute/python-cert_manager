# -*- coding: utf-8 -*-
"""Define the cert_manager.dcv.DomainControlValidation class."""

from requests.exceptions import HTTPError

from ._endpoint import Endpoint


class DomainControlValidation(Endpoint):
    """Query the Sectigo Cert Manager REST API for Domain Control Validation (DCV) data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/dcv", api_version=api_version)

    def search(self, **kwargs):
        """Search the DCV statuses of domains.

        :param dict kwargs the following search keys are supported:
            position, size, domain, org, department, dcvStatus, orderStatus, expiresIn

        See
        https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-statuses

        :return list: a list of DCV statuses
        """
        url = self._url("validation")
        result = self._client.get(url, params=kwargs)

        return result.json()

    def get_validation_status(self, domain: str):
        """Get the DCV statuses of a domain.

        :param dict kwargs the following search keys are supported:
            position, size, domain, org, department, dcvStatus, orderStatus, expiresIn

        See
        https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-status

        :return list: the DCV status for the domain
        """
        url = self._url("validation", "status")
        data = {"domain": domain}

        try:
            result = self._client.post(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == 400:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()

    def start_validation_cname(self, domain: str):
        """Start Domain Control Validation using the CNAME method.

        See
        https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-start-http

        :param string domain: The domain to validate

        :return response: a dictionary containing
            host: Where the validation will expect the CNAME to live on the server
            point: Where the CNAME should point to
        """
        url = self._url("validation", "start", "domain", "cname")
        data = {"domain": domain}

        try:
            result = self._client.post(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == 400:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()

    def submit_validation_cname(self, domain: str):
        """Finish Domain Control Validation using the CNAME method.

        See
        https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-submit-cname

        :param string domain: The domain to validate

        :return response: a dictionary containing
            status: The status of the validation
            orderStatus: The status of the validation request
            message: An optional message to help with debugging
        """
        url = self._url("validation", "submit", "domain", "cname")
        data = {"domain": domain}

        try:
            result = self._client.post(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == 400:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()
