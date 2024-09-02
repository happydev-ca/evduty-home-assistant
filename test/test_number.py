from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from evdutyapi import Terminal, ChargingStatus, ChargingSession, NetworkInfo
from evdutyapi.charging_profile import ChargingProfile
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from custom_components.evduty import DOMAIN
from custom_components.evduty.const import MANUFACTURER
from custom_components.evduty.number import MaxAmpNumber, async_setup_entry


class TestNumberCreation(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        entry = Mock()
        entry.entry_id = 'id'
        self.coordinator = Mock(DataUpdateCoordinator)
        self.terminal = Terminal(id='123',
                                 station_id='456',
                                 name='Test',
                                 status=ChargingStatus.in_use,
                                 charge_box_identity='A',
                                 firmware_version='1.2.3',
                                 session=ChargingSession(is_active=True,
                                                         is_charging=True,
                                                         volt=120,
                                                         amp=8,
                                                         power=960,
                                                         energy_consumed=2000,
                                                         start_date=datetime.now(),
                                                         duration=timedelta(seconds=55),
                                                         cost=0.32),
                                 network_info=NetworkInfo(wifi_ssid="ssid", wifi_rssi=-72, ip_address="ip", mac_address="mac"),
                                 charging_profile=ChargingProfile(power_limitation=True, current_limit=15, current_max=50))
        self.coordinator.data = {'123': self.terminal}
        hass = Mock(HomeAssistant)
        hass.data = {DOMAIN: {entry.entry_id: self.coordinator}}

        async_add_devices = Mock()

        await async_setup_entry(hass, entry, async_add_devices)

        async_add_devices.assert_called_once()

        self.numbers = async_add_devices.call_args.args[0]

    async def test_add_sensors_on_setup(self):
        self.assertEqual(len(self.numbers), 1)

    def test_max_amp_number_created(self):
        self.assert_sensor_created(type=MaxAmpNumber,
                                   name='Max Amp',
                                   state_class=SensorStateClass.MEASUREMENT,
                                   device_class=SensorDeviceClass.CURRENT,
                                   unit=UnitOfElectricCurrent.AMPERE,
                                   value=15,
                                   native_step=1,
                                   native_min_value=0,
                                   native_max_value=50)

    async def test_set_max_amp_number(self):
        self.coordinator.async_set_terminal_max_charging_current = AsyncMock(return_value=None)

        max_amp_number = next(s for s in self.numbers if isinstance(s, MaxAmpNumber))
        await max_amp_number.async_set_native_value(22)

        self.coordinator.async_set_terminal_max_charging_current.assert_called_with(self.terminal, 22)

    def assert_sensor_created(self, type, name, state_class=None, device_class=None, unit=None, value=None, native_step=1, native_min_value=None, native_max_value=None):
        number = next(s for s in self.numbers if isinstance(s, type))
        self.assertEqual(number.coordinator, self.coordinator)
        self.assertEqual(number._terminal, self.terminal)
        self.assertEqual(number.device_info, DeviceInfo(identifiers={(DOMAIN, self.terminal.id)},
                                                        manufacturer=MANUFACTURER,
                                                        model=self.terminal.charge_box_identity,
                                                        sw_version=self.terminal.firmware_version,
                                                        connections={('mac', 'mac')},
                                                        name='EVduty Test'))
        if state_class is not None:
            self.assertEqual(number._attr_state_class, state_class)
        if device_class is not None:
            self.assertEqual(number._attr_device_class, device_class)
        if unit is not None:
            self.assertEqual(number._attr_native_unit_of_measurement, unit)

        self.assertEqual(number._attr_name, f'EVduty Test {name}')
        self.assertEqual(number._attr_unique_id, f'evduty_test_{slugify(name)}')

        self.assertEqual(number.native_value, value)
        self.assertEqual(number.native_step, native_step)
        self.assertEqual(number.native_min_value, native_min_value)
        self.assertEqual(number.native_max_value, native_max_value)
