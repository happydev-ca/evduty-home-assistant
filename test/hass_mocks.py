from unittest.mock import AsyncMock

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant


def config_entry_mock(username='u', password='p', id='e'):
    entry = AsyncMock(ConfigEntry)
    entry.entry_id = id
    entry.data = {CONF_USERNAME: username, CONF_PASSWORD: password}
    entry.state = config_entries.ConfigEntryState.SETUP_IN_PROGRESS
    return entry


def hass_mock():
    hass = AsyncMock(HomeAssistant)
    hass.data = {}
    hass.config_entries = AsyncMock(ConfigEntries)
    return hass
