"""Switch entities from LOIP components with type=switch."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanbonConfigEntry
from .entity import LanbonEntity, async_send_loip
from .entity_map import iter_switch_components


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanbonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [
        LanbonSwitch(coordinator, device.id, component.id)
        for device, component in iter_switch_components(coordinator.data)
    ]
    async_add_entities(entities)


class LanbonSwitch(LanbonEntity, SwitchEntity):
    @property
    def is_on(self) -> bool | None:
        _device, component = self._pair()
        if component is None:
            return None
        return bool(component.state.get("on"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_on(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_on(False)

    async def _set_on(self, on: bool) -> None:
        await async_send_loip(
            self.coordinator,
            self._device_id,
            self._component_id,
            "set_on",
            {"on": on},
        )
