"""Fan entities from LOIP components with type=fan."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanbonConfigEntry
from .entity import LanbonEntity, async_send_loip
from .entity_map import (
    _as_int,
    fan_is_on,
    iter_fan_components,
    percentage_to_speed,
    speed_levels,
    speed_to_percentage,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanbonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [
        LanbonFan(coordinator, device.id, component.id)
        for device, component in iter_fan_components(coordinator.data)
    ]
    async_add_entities(entities)


def _supported_features(has_speed: bool) -> FanEntityFeature:
    features = FanEntityFeature(0)
    for name in ("TURN_ON", "TURN_OFF"):
        flag = getattr(FanEntityFeature, name, 0)
        if flag:
            features |= flag
    if has_speed:
        features |= FanEntityFeature.SET_SPEED
    return features


class LanbonFan(LanbonEntity, FanEntity):
    def _levels(self) -> list[int] | None:
        _device, component = self._pair()
        return speed_levels(component)

    @property
    def supported_features(self) -> FanEntityFeature:
        return _supported_features(bool(self._levels()))

    @property
    def speed_count(self) -> int:
        levels = self._levels()
        return len(levels) if levels else 0

    @property
    def is_on(self) -> bool | None:
        _device, component = self._pair()
        if component is None:
            return None
        return fan_is_on(component)

    @property
    def percentage(self) -> int | None:
        levels = self._levels()
        if not levels:
            return None
        _device, component = self._pair()
        if component is None:
            return None
        raw = _as_int(component.state.get("speed_level"))
        if raw is None or raw <= 0:
            return 0
        return speed_to_percentage(raw, levels)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        del preset_mode, kwargs
        if percentage is None:
            await self._send("set_on", {"on": True})
            return
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        del kwargs
        await self._send("set_on", {"on": False})

    async def async_set_percentage(self, percentage: int) -> None:
        parsed = _as_int(percentage)
        if parsed is None:
            raise HomeAssistantError("percentage must be an integer")
        if parsed <= 0:
            await self._send("set_on", {"on": False})
            return
        levels = self._levels()
        if not levels:
            raise HomeAssistantError("speed_level is not declared")
        level = percentage_to_speed(parsed, levels)
        if level not in levels:
            raise HomeAssistantError("speed_level out of range")
        await self._send("set_speed_level", {"speed_level": level})

    async def _send(self, command: str, params: dict) -> None:
        await async_send_loip(
            self.coordinator, self._device_id, self._component_id, command, params
        )
