"""Define the cert_manager.dcv.DomainControlValidation class."""

from http import HTTPStatus

from requests.exceptions import HTTPError

from ._endpoint import Endpoint


class DomainControlValidation(Endpoint):
    """Query the Sectigo Cert Manager REST API for Domain Control Validation (DCV) data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        Args:
            client: An instantiated cert_manager.Client object
            api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/dcv", api_version=api_version)

    def search(self, **kwargs):
        """Search the DCV statuses of domains.

        See https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-statuses

        Args:
            kwargs: The following search keys are supported:
                position, size, domain, org, department, dcvStatus, orderStatus, expiresIn

        Returns:
            A list of DCV statuses
        """
        url = self._url("validation")
        result = self._client.get(url, params=kwargs)

        return result.json()

    def get_validation_status(self, domain: str):
        """Get the DCV statuses of a domain.

        Args:
            domain: The domain to query

        Returns:
            A list of DCV statuses for the domain
        """
        url = self._url("validation", "status")
        data = {"domain": domain}

        try:
            result = self._client.post(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == HTTPStatus.BAD_REQUEST:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()

    def start_validation_cname(self, domain: str):
        """Start Domain Control Validation using the CNAME method.

        See
        https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-start-http

        Args:
            domain: The domain to validate

        Returns:
            A dictionary containing:
                host: Where the validation will expect the CNAME to live on the server
                point: Where the CNAME should point to
        """
        url = self._url("validation", "start", "domain", "cname")
        data = {"domain": domain}

        try:
            result = self._client.post(url, data=data)
        except HTTPError as exc:
            status_code = exc.response.status_code
            if status_code == HTTPStatus.BAD_REQUEST:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()

    def submit_validation_cname(self, domain: str):
        """Finish Domain Control Validation using the CNAME method.

        See
        https://www.sectigo.com/uploads/audio/Certificate-Manager-20.1-Rest-API.html#resources-dcv-submit-cname

        Args:
            domain: The domain to validate

        Returns:
            A dictionary containing:
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
            if status_code == HTTPStatus.BAD_REQUEST:
                err_response = exc.response.json()
                raise ValueError(err_response["description"]) from exc
            raise exc

        return result.json()
