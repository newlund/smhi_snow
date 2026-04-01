"""Constants in smhi_snow component."""

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "smhi_snow"

HOME_LOCATION_NAME: Final = "Home"
DEFAULT_NAME: Final = "Weather"

LOGGER = logging.getLogger(__package__)

DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=31)
TIMEOUT: Final = 10
