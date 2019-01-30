"""Initialize the cert_manager module."""

from .client import Client
from ._helpers import HttpError, Pending
from .organization import Organization
from .person import Person
from .smime import SMIME
from .ssl import SSL

APP_VERSION = "0.1.0"

__all__ = ["Client", "HttpError", "Organization", "Pending", "Person", "SMIME", "SSL"]

__version__ = APP_VERSION
