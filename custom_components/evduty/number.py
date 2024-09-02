"""
EVduty charging stations terminal max changing map
"""

from evdutyapi import Terminal
from homeassistant.components.number import NumberEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import EVDutyCoordinator
from .const import DOMAIN, MANUFACTURER


async def async_setup_entry(hass, entry, async_add_devices) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = []
    for terminal in coordinator.data.values():
        numbers.append(MaxAmpNumber(coordinator, terminal))

    async_add_devices(numbers)


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


class MaxAmpNumber(EVDutyTerminalDevice, NumberEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator: EVDutyCoordinator, terminal: Terminal) -> None:
        super().__init__(coordinator, terminal, 'Max Amp')

    @property
    def native_max_value(self) -> int:
        return self._terminal.charging_profile.current_max

    @property
    def native_min_value(self) -> int:
        return 0

    @property
    def native_step(self) -> int:
        return 1

    @property
    def native_value(self):
        return self._terminal.charging_profile.current_limit

    async def async_set_native_value(self, value: int) -> None:
        await self.coordinator.async_set_terminal_max_charging_current(self._terminal, value)