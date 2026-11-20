"""Scene entities from LOIP components with type=scene.

L8 scene switches are exposed via `set_on {on:true}`; HA `scene` has no
durable state, so activation is fire-and-forget: flip the target scene on,
then poll /devices to learn which scene the gateway currently holds.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanbonConfigEntry
from .entity import LanbonEntity, async_send_loip
from .entity_map import iter_scene_components


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanbonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [
        LanbonScene(coordinator, device.id, component.id)
        for device, component in iter_scene_components(coordinator.data)
    ]
    async_add_entities(entities)


class LanbonScene(LanbonEntity, Scene):
    async def async_activate(self, **kwargs: Any) -> None:
        await async_send_loip(
            self.coordinator,
            self._device_id,
            self._component_id,
            "set_on",
            {"on": True},
        )
