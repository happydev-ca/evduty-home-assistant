import asyncio
from datetime import timedelta
from http import HTTPStatus

from evdutyapi import EVDutyApi, Terminal, EVDutyApiInvalidCredentialsError, EVDutyApiError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class EVDutyCoordinator(DataUpdateCoordinator):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, api: EVDutyApi) -> None:
        super().__init__(hass=hass, logger=LOGGER, name=DOMAIN, update_interval=timedelta(seconds=60))
        self.api = api

    async def _async_update_data(self) -> dict[str, Terminal]:
        try:
            async with asyncio.timeout(10):
                stations = await self.api.async_get_stations()
                return {terminal.id: terminal for station in stations for terminal in station.terminals}
        except EVDutyApiInvalidCredentialsError as error:
            raise ConfigEntryAuthFailed from error
        except EVDutyApiError as error:
            if error.status == HTTPStatus.UNAUTHORIZED:
                LOGGER.debug(f'Simultaneous EVduty account usage. Returning last data: {self.data}')
                return self.data
            else:
                raise ConnectionError from error

    async def async_set_terminal_max_charging_current(self, terminal: Terminal, current: int):
        try:
            async with asyncio.timeout(10):
                await self.api.async_set_terminal_max_charging_current(terminal, current)
                await self.async_request_refresh()
        except EVDutyApiInvalidCredentialsError as error:
            raise ConfigEntryAuthFailed from error
        except EVDutyApiError as error:
            raise ConnectionError from error
