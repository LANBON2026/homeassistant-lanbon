"""Light entities from LOIP components with type=light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanbonConfigEntry
from .entity import LanbonEntity, async_send_loip
from .entity_map import (
    _as_int,
    brightness_levels,
    device_brightness_to_ha,
    ha_brightness_to_device,
    iter_light_components,
    light_is_on,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanbonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [
        LanbonLight(coordinator, device.id, component.id)
        for device, component in iter_light_components(coordinator.data)
    ]
    async_add_entities(entities)


def _requested_brightness(kwargs: dict[str, Any]) -> int | None:
    if ATTR_BRIGHTNESS in kwargs:
        return _as_int(kwargs.get(ATTR_BRIGHTNESS))
    pct = _as_int(kwargs.get(ATTR_BRIGHTNESS_PCT))
    if pct is None:
        return None
    if pct <= 0:
        return 0
    if pct >= 100:
        return 255
    return round(pct * 255 / 100)


class LanbonLight(LanbonEntity, LightEntity):
    def _levels(self) -> list[int] | None:
        _device, component = self._pair()
        return brightness_levels(component)

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        if self._levels():
            return {ColorMode.BRIGHTNESS}
        return {ColorMode.ONOFF}

    @property
    def color_mode(self) -> ColorMode:
        if self._levels():
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    @property
    def is_on(self) -> bool | None:
        _device, component = self._pair()
        if component is None:
            return None
        return light_is_on(component)

    @property
    def brightness(self) -> int | None:
        _device, component = self._pair()
        levels = brightness_levels(component)
        if component is None or not levels:
            return None
        raw = _as_int(component.state.get("brightness"))
        if raw is None or raw <= 0:
            return None
        return device_brightness_to_ha(raw, levels)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS not in kwargs and ATTR_BRIGHTNESS_PCT not in kwargs:
            await self._send("set_on", {"on": True})
            return
        brightness = _requested_brightness(kwargs)
        if brightness is None:
            raise HomeAssistantError("brightness must be an integer")
        if brightness <= 0:
            await self.async_turn_off()
            return
        levels = self._levels()
        if not levels:
            raise HomeAssistantError("brightness is not declared")
        device_value = ha_brightness_to_device(brightness, levels)
        if device_value not in levels:
            raise HomeAssistantError("brightness out of range")
        await self._send("set_brightness", {"brightness": device_value})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._send("set_on", {"on": False})

    async def _send(self, command: str, params: dict) -> None:
        await async_send_loip(
            self.coordinator, self._device_id, self._component_id, command, params
        )
