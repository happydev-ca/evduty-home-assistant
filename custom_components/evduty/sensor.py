"""
EVduty charging stations terminal device and sensors
"""
from datetime import datetime

from evdutyapi import Terminal, ChargingStatus
from homeassistant.const import UnitOfPower, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfTime, EntityCategory, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import EVDutyCoordinator
from .const import DOMAIN, MANUFACTURER, LOGGER


async def async_setup_entry(hass, entry, async_add_devices) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for terminal in coordinator.data.values():
        LOGGER.debug(terminal)
        sensors.append(PowerSensor(coordinator, terminal))
        sensors.append(AmpSensor(coordinator, terminal))
        sensors.append(VoltSensor(coordinator, terminal))
        sensors.append(EnergyConsumedSensor(coordinator, terminal))
        sensors.append(ChargingStateSensor(coordinator, terminal))
        sensors.append(ChargingSessionStartDateSensor(coordinator, terminal))
        sensors.append(ChargingSessionDurationSensor(coordinator, terminal))
        sensors.append(ChargingSessionEstimatedCostSensor(coordinator, terminal))
        sensors.append(WifiIpSensor(coordinator, terminal))
        sensors.append(WifiSsidSensor(coordinator, terminal))
        sensors.append(WifiRssiSensor(coordinator, terminal))

    async_add_devices(sensors)


class EVDutyTerminalDevice(CoordinatorEntity):
    _attr_attribution = f'Data provided by {MANUFACTURER}'

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal, sensor_name: str) -> None:
        super().__init__(coordinator)
        device_name = f'{MANUFACTURER} {terminal.name}'
        self._attr_name = f'{device_name} {sensor_name}'
        self._attr_unique_id = slugify(self._attr_name)
        self._terminal = terminal
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, terminal.id)},
            manufacturer=MANUFACTURER,
            model=terminal.charge_box_identity,
            sw_version=terminal.firmware_version,
            connections={(CONNECTION_NETWORK_MAC, terminal.network_info.mac_address)},
            name=device_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._terminal = self.coordinator.data[self._terminal.id]
        self.async_write_ha_state()


class PowerSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Power')

    @property
    def native_value(self):
        return self._terminal.session.power


class AmpSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Amp')

    @property
    def native_value(self):
        return self._terminal.session.amp


class VoltSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Volt')

    @property
    def native_value(self):
        return self._terminal.session.volt


class EnergyConsumedSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Energy Consumed')

    @property
    def native_value(self):
        return self._terminal.session.energy_consumed / 1000


class ChargingStateSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ['Available', 'Charging', 'Offline']

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'State')

    @property
    def native_value(self):
        if self._terminal.status == ChargingStatus.in_use:
            return 'Charging'
	elif self._terminal.status == ChargingStatus.out_of_service:
            return 'Offline'
        return 'Available'


class ChargingSessionStartDateSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Session Start Date')

    @property
    def native_value(self):
        if self._terminal.session.start_date == datetime.min:
            return None
        return self._terminal.session.start_date


class ChargingSessionDurationSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Session Duration')

    @property
    def native_value(self):
        return self._terminal.session.duration.total_seconds()


class ChargingSessionEstimatedCostSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = '$'
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Session Estimated Cost')

    @property
    def native_value(self):
        return self._terminal.session.cost


class WifiIpSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        LOGGER.info('Wi-Fi IP')
        super().__init__(coordinator, terminal, 'Wi-Fi IP')

    @property
    def native_value(self):
        return self._terminal.network_info.ip_address


class WifiSsidSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Wi-Fi SSID')

    @property
    def native_value(self):
        return self._terminal.network_info.wifi_ssid


class WifiRssiSensor(EVDutyTerminalDevice, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Wi-Fi Signal Strength')

    @property
    def native_value(self):
        return self._terminal.network_info.wifi_rssi
