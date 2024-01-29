"""Define helper functions used by classes in this module."""

import logging
import re
from functools import wraps

from requests.exceptions import HTTPError


def traffic_log(traffic_logger=None):
    """Log traffic for the wrapped function.

    This will wrap any function with a call to `logger.debug()` displaying useful before and after information from
    API calls.  This obeys the log level set in logging, so if the level is not set to "DEBUG", no messages will be
    logged.

    Note: The "DEBUG" level should *never* be used in production.

    :param obj traffic_logger: a logging.Logger to use for logging messages.
    """
    def decorator(func):
        """Wrap the actual decorator so a reference to the function can be returned."""
        @wraps(func)
        def log_traffic(*args, **kwargs):
            """Decorate the wrapped function."""
            # Make sure traffic_logger was set correctly
            if not isinstance(traffic_logger, logging.Logger):
                raise Exception("traffic_log: No logging.Logger instance provided")

            # Try to get rid of surrounding underscores and then upcase function name
            func_name = func.__name__
            match = re.search(r"^_*(\w+?)_*$", func_name)
            if match:
                func_name = match.group(1).upper()

            # Check if the URL or headers exist in the parameters
            # Note: *self* will be the first argument, so actual arguments start after that.
            params = ["url", "headers", "data"]
            values = {}
            for index, param in enumerate(params, start=1):
                values[param] = kwargs.get(param, "")
                if not values[param]:
                    if len(args) > index:
                        values[param] = args[index]

            # Print out before messages with URL and header data
            traffic_logger.debug(f"Performing a {func_name} on url: {values['url']}")
            traffic_logger.debug(f"Extra request headers: {values['headers']}")
            traffic_logger.debug(f"Data: {values['data']}")

            # Run the wrapped function
            try:
                result = func(*args, **kwargs)
            except HTTPError as herr:
                # If it's of type HTTPError, we can still usually get the result data
                traffic_logger.debug(f"Result code: {herr.response.status_code}")
                traffic_logger.debug(f"Result headers: {herr.response.headers}")
                traffic_logger.debug(f"Text result: {herr.response.text}")

                # Re-raise the original exception
                raise herr
            except Exception as exc:
                # Re-raise the original exception
                raise exc

            # If everything went fine, more logging
            if result:
                traffic_logger.debug(f"Result code: {result.status_code}")
                traffic_logger.debug(f"Result headers: {result.headers}")
                traffic_logger.debug(f"Text result: {result.text}")
            return result
        return log_traffic
    return decorator


def version_hack(service, version="v1"):
    """Hack around a hard-coded API version.

    For the most part, the Sectigo Certificate Manager API uses the same version (v1) for all API calls. However,
    there are a few calls spread throughout the API spec that use "v2" currently.  This wrapper is designed to
    temporarily change the version to something other than what the object was initialized with so that the internal
    *self.api_url* will be correct.

    :param version: API version string to use. If None, 'v1'
    """
    def decorator(func):
        """Wrap the actual decorator so a reference to the function can be returned."""
        @wraps(func)
        def api_version(self, *args, **kwargs):
            """Decorate the wrapped function."""
            if not service:
                raise Exception("version_hack: No service provided")
            if not version:
                raise Exception("version_hack: No version provided")

            api = self.create_api_url(self._client.base_url, service, version)  # pylint: disable=protected-access
            save_url = self.api_url
            self._api_url = api  # pylint: disable=protected-access

            try:
                retval = func(self, *args, **kwargs)

                # Reset the api_url back to the original
                self._api_url = save_url    # pylint: disable=protected-access

                return retval
            except Exception as exc:
                # Reset the api_url back to the original
                self._api_url = save_url    # pylint: disable=protected-access
                raise exc

        return api_version  # true decorator

    return decorator


def paginate(func):
    """Iterate through pages in API calls to retrieve all data from an endpoint."""

    @wraps(func)
    def decorator(*args, **kwargs):
        """Decorate the wrapped function.

        Iterate through pages in API calls to retrieve all data from an endpoint.
        The `size` and `position` parameters passed through `kwargs` to this function will be used
        by the pagination wrapper to page through results.

        :param list args: Positional parameters to pass to the wrapped function
        :param dict kwargs: A dictionary with any parameters to add to the request URL

        :return obj: Yield results from the wrapped function's response for each request
        """
        size = kwargs.pop("size", 200)  # max seems to be 200 by default
        position = kwargs.pop("position", 0)  # 0-..

        lastsize = size
        while lastsize == size:
            retval = func(*args, size=size, position=position, **kwargs)
            lastsize = len(retval)
            position += size
            yield from retval

    return decorator


class PendingError(Exception):
    """Serve as a generic Exception indicating a certificate is in a pending state."""
    CODE = -183


class RevokedError(Exception):
    """Serve as a generic Exception indicating a certificate has been revoked."""
    CODE = -192


class CustomFieldsError(Exception):
    """Exception when custom fields do not have correct data."""
