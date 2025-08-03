from datetime import timedelta
from http import HTTPStatus
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from evdutyapi import EVDutyApi, Station, Terminal, EVDutyApiInvalidCredentialsError, EVDutyApiError
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.evduty import EVDutyCoordinator, DOMAIN
from test import hass_mocks


class TestEVDutyCoordinator(IsolatedAsyncioTestCase):

    async def test_set_coordinator_name_to_domain(self):
        hass = hass_mocks.hass_mock()
        config_entry = hass_mocks.config_entry_mock()
        api = Mock(EVDutyApi)

        coordinator = EVDutyCoordinator(hass=hass, config_entry=config_entry, api=api)

        self.assertEqual(coordinator.name, DOMAIN)

    async def test_refresh_data_every_60_seconds(self):
        hass = hass_mocks.hass_mock()
        config_entry = hass_mocks.config_entry_mock()
        api = Mock(EVDutyApi)
        coordinator = EVDutyCoordinator(hass=hass, config_entry=config_entry, api=api)

        self.assertEqual(coordinator.update_interval, timedelta(seconds=60))

    async def test_get_charging_stations(self):
        hass = hass_mocks.hass_mock()
        config_entry = hass_mocks.config_entry_mock()
        api = Mock(EVDutyApi)
        coordinator = EVDutyCoordinator(hass=hass, config_entry=config_entry, api=api)

        station = Mock(Station)
        terminal = Mock(Terminal)
        terminal.id = "123"
        station.terminals = [terminal]
        api.async_get_stations = AsyncMock(return_value=[station])

        terminals = await coordinator._async_update_data()

        self.assertEqual(terminals, {"123": terminal})

    async def test_triggers_a_reauth_on_invalid_credentials_error(self):
        hass = hass_mocks.hass_mock()
        config_entry = hass_mocks.config_entry_mock()
        api = Mock(EVDutyApi)
        coordinator = EVDutyCoordinator(hass=hass, config_entry=config_entry, api=api)

        response = AsyncMock()
        response.status = HTTPStatus.BAD_REQUEST
        api.async_get_stations.side_effect = EVDutyApiInvalidCredentialsError(AsyncMock())

        with self.assertRaises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_returns_last_data_on_simultaneous_evduty_account_usage(self):
        hass = hass_mocks.hass_mock()
        config_entry = hass_mocks.config_entry_mock()
        api = Mock(EVDutyApi)
        coordinator = EVDutyCoordinator(hass=hass, config_entry=config_entry, api=api)
        previous_data = {"123": 'anything'}
        coordinator.data = previous_data

        response = AsyncMock()
        response.status = HTTPStatus.UNAUTHORIZED
        api.async_get_stations.side_effect = EVDutyApiError(response)

        terminals = await coordinator._async_update_data()

        self.assertEqual(terminals, previous_data)

    async def test_raise_on_other_api_error(self):
        hass = hass_mocks.hass_mock()
        config_entry = hass_mocks.config_entry_mock()
        api = Mock(EVDutyApi)
        coordinator = EVDutyCoordinator(hass=hass, config_entry=config_entry, api=api)

        response = AsyncMock()
        response.status = HTTPStatus.BAD_REQUEST
        api.async_get_stations.side_effect = EVDutyApiError(AsyncMock())

        with self.assertRaises(ConnectionError):
            await coordinator._async_update_data()
