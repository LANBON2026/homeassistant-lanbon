"""Fan entities for fan / fan+light panels (esdtFan / esdtFanEx)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN, MANUFACTURER, device_name_from_payload
from .coordinator import LanbonCoordinator

# Firmware enumDevFanGear: 0=stop, 1=first, 2=second, 3=third
_ORDERED_GEARS = [1, 2, 3]


def _gear_from_dev(dev: dict[str, Any] | None) -> int:
    if not dev:
        return 0
    try:
        return max(0, min(3, int(dev.get("gear") or 0)))
    except (TypeError, ValueError):
        return 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data.coordinator
    api = entry.runtime_data.api
    entities = []
    for dev in (coordinator.data or {}).get("devices") or []:
        if dev.get("kind") != "fan":
            continue
        mac = str(dev.get("mac") or "").upper()
        entities.append(LanbonFan(coordinator, api, mac, bool(dev.get("is_host"))))
    async_add_entities(entities)


class LanbonFan(CoordinatorEntity[LanbonCoordinator], FanEntity):
    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_translation_key = "fan"
    # HA has no SET_PERCENTAGE flag — percentage API is gated by SET_SPEED.
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = len(_ORDERED_GEARS)
    # Migrated: declare TURN_ON/TURN_OFF explicitly (HA ≥ 2024.8).
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator, api, mac: str, is_host: bool) -> None:
        super().__init__(coordinator)
        self._api = api
        self._mac = mac
        self._attr_unique_id = f"{mac}_fan"
        dev_row = None
        for d in (coordinator.data or {}).get("devices") or []:
            if str(d.get("mac") or "").upper() == mac:
                dev_row = d
                break
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            manufacturer=MANUFACTURER,
            name=device_name_from_payload(dev_row, mac=mac, is_host=is_host),
        )

    def _dev(self) -> dict[str, Any] | None:
        for d in (self.coordinator.data or {}).get("devices") or []:
            if str(d.get("mac") or "").upper() == self._mac:
                return d
        return None

    @property
    def available(self) -> bool:
        # Hub reachable (coordinator) AND device.available (child keepalive).
        if not super().available:
            return False
        dev = self._dev()
        return bool(dev and dev.get("available", True))

    @property
    def is_on(self) -> bool | None:
        return _gear_from_dev(self._dev()) != 0

    @property
    def percentage(self) -> int | None:
        gear = _gear_from_dev(self._dev())
        if gear == 0:
            return 0
        return ordered_list_item_to_percentage(_ORDERED_GEARS, gear)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            gear = 0
        else:
            gear = int(percentage_to_ordered_list_item(_ORDERED_GEARS, percentage))
        await self._api.async_command(
            {"mac": self._mac, "op": "fan_set", "gear": gear}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        await self._api.async_command({"mac": self._mac, "op": "fan_set", "on": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.async_command(
            {"mac": self._mac, "op": "fan_set", "on": False, "gear": 0}
        )
        await self.coordinator.async_request_refresh()
