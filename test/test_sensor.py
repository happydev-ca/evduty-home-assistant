from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from evdutyapi import Terminal, ChargingStatus, ChargingSession, NetworkInfo
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfPower, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfTime, EntityCategory, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from custom_components.evduty import DOMAIN
from custom_components.evduty.const import MANUFACTURER
from custom_components.evduty.sensor import async_setup_entry, PowerSensor, AmpSensor, VoltSensor, EnergyConsumedSensor, ChargingStateSensor, ChargingSessionStartDateSensor, \
    ChargingSessionDurationSensor, ChargingSessionEstimatedCostSensor, WifiSsidSensor, WifiRssiSensor, WifiIpSensor


class TestSensorCreation(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        entry = Mock()
        entry.entry_id = 'id'
        self.coordinator = Mock(DataUpdateCoordinator)
        self.terminal = Terminal(id='123',
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
                                 network_info=NetworkInfo(wifi_ssid="ssid", wifi_rssi=-72, ip_address="ip", mac_address="mac"))
        self.coordinator.data = {'123': self.terminal}
        hass = Mock(HomeAssistant)
        hass.data = {DOMAIN: {entry.entry_id: self.coordinator}}

        async_add_devices = Mock()

        await async_setup_entry(hass, entry, async_add_devices)

        async_add_devices.assert_called_once()

        self.sensors = async_add_devices.call_args.args[0]

    async def test_add_sensors_on_setup(self):
        self.assertEqual(len(self.sensors), 11)

    def test_power_sensor_created(self):
        self.assert_sensor_created(type=PowerSensor,
                                   name='Power',
                                   state_class=SensorStateClass.MEASUREMENT,
                                   device_class=SensorDeviceClass.POWER,
                                   unit=UnitOfPower.WATT,
                                   value=960)

    def test_amp_sensor_created(self):
        self.assert_sensor_created(type=AmpSensor,
                                   name='Amp',
                                   state_class=SensorStateClass.MEASUREMENT,
                                   device_class=SensorDeviceClass.CURRENT,
                                   unit=UnitOfElectricCurrent.AMPERE,
                                   value=8)

    def test_volt_sensor_created(self):
        self.assert_sensor_created(type=VoltSensor,
                                   name='Volt',
                                   state_class=SensorStateClass.MEASUREMENT,
                                   device_class=SensorDeviceClass.VOLTAGE,
                                   unit=UnitOfElectricPotential.VOLT,
                                   value=120)

    def test_energy_consumed_sensor_created(self):
        self.assert_sensor_created(type=EnergyConsumedSensor,
                                   name='Energy Consumed',
                                   state_class=SensorStateClass.TOTAL_INCREASING,
                                   device_class=SensorDeviceClass.ENERGY,
                                   unit=UnitOfEnergy.KILO_WATT_HOUR,
                                   precision=1,
                                   value=2)

    def test_charging_state_sensor_created(self):
        self.assert_sensor_created(type=ChargingStateSensor,
                                   name='State',
                                   device_class=SensorDeviceClass.ENUM,
                                   options=['Available', 'Charging', 'Offline'],
                                   value='Charging')

    def test_charging_session_start_date_sensor_created(self):
        self.assert_sensor_created(type=ChargingSessionStartDateSensor,
                                   name='Session Start Date',
                                   device_class=SensorDeviceClass.TIMESTAMP,
                                   value=self.terminal.session.start_date)

    def test_charging_session_duration_sensor_created(self):
        self.assert_sensor_created(type=ChargingSessionDurationSensor,
                                   name='Session Duration',
                                   device_class=SensorDeviceClass.DURATION,
                                   unit=UnitOfTime.SECONDS,
                                   value=55)

    def test_estimated_cost_sensor_created(self):
        self.assert_sensor_created(type=ChargingSessionEstimatedCostSensor,
                                   name='Session Estimated Cost',
                                   state_class=SensorStateClass.TOTAL_INCREASING,
                                   device_class=SensorDeviceClass.MONETARY,
                                   unit='$',
                                   precision=2,
                                   value=0.32)

    def test_wifi_ip_sensor_created(self):
        self.assert_sensor_created(type=WifiIpSensor,
                                   name='Wi-Fi IP',
                                   entity_category=EntityCategory.DIAGNOSTIC,
                                   value="ip")

    def test_wifi_ssid_sensor_created(self):
        self.assert_sensor_created(type=WifiSsidSensor,
                                   name='Wi-Fi SSID',
                                   entity_category=EntityCategory.DIAGNOSTIC,
                                   value="ssid")

    def test_wifi_rssi_sensor_created(self):
        self.assert_sensor_created(type=WifiRssiSensor,
                                   name='Wi-Fi Signal Strength',
                                   entity_category=EntityCategory.DIAGNOSTIC,
                                   state_class=SensorStateClass.MEASUREMENT,
                                   device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                                   unit=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                                   value=-72)

    def assert_sensor_created(self, type, name, state_class=None, device_class=None, unit=None, precision=None, options=None, value=None, entity_category=None):
        sensor = next(s for s in self.sensors if isinstance(s, type))
        self.assertEqual(sensor.coordinator, self.coordinator)
        self.assertEqual(sensor._terminal, self.terminal)
        self.assertEqual(sensor.device_info, DeviceInfo(identifiers={(DOMAIN, self.terminal.id)},
                                                        manufacturer=MANUFACTURER,
                                                        model=self.terminal.charge_box_identity,
                                                        sw_version=self.terminal.firmware_version,
                                                        connections={('mac', 'mac')},
                                                        name='EVduty Test'))
        if state_class is not None:
            self.assertEqual(sensor._attr_state_class, state_class)
        if device_class is not None:
            self.assertEqual(sensor._attr_device_class, device_class)
        if unit is not None:
            self.assertEqual(sensor._attr_native_unit_of_measurement, unit)
        if precision is not None:
            self.assertEqual(sensor._attr_suggested_display_precision, precision)
        if options is not None:
            self.assertEqual(sensor._attr_options, options)
        if entity_category is not None:
            self.assertEqual(sensor._attr_entity_category, entity_category)

        self.assertEqual(sensor._attr_name, f'EVduty Test {name}')
        self.assertEqual(sensor._attr_unique_id, f'evduty_test_{slugify(name)}')

        self.assertEqual(sensor.native_value, value)
