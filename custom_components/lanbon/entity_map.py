"""Map LOIP components to HA entities. Decisions use capabilities only."""

from __future__ import annotations

import math

from aiolanbon.models import Component, Device, DeviceSnapshot

# ponytail: refuse a level grid bigger than a dimmer 0..100. A wider range needs
# an explicit command (speed_percent / set_brightness still uses this grid only
# when the declared step count stays within the cap).
_MAX_LEVELS = 256


def _as_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    return int(value)


def _on_levels(constraints: dict, key: str) -> list[int] | None:
    """Positive steps from constraints. 0 stays off and is not a level."""
    raw = constraints.get(key)
    if not isinstance(raw, dict):
        return None
    lo = _as_int(raw.get("min"))
    hi = _as_int(raw.get("max"))
    step = _as_int(raw.get("step", 1))
    if lo is None or hi is None or step is None or step <= 0 or hi < lo:
        return None
    start = lo if lo > 0 else lo + step
    if start > hi:
        return None
    count = (hi - start) // step + 1
    if count > _MAX_LEVELS:
        return None
    top = start + (count - 1) * step
    return list(range(start, top + 1, step))


def is_switch_component(component: Component) -> bool:
    """True when LOIP declares type=switch and commands include set_on."""
    return component.type == "switch" and "set_on" in component.commands


def is_light_component(component: Component) -> bool:
    """True when LOIP declares type=light and commands include set_on."""
    return component.type == "light" and "set_on" in component.commands


def is_fan_component(component: Component) -> bool:
    """True when LOIP declares type=fan and commands include set_on."""
    return component.type == "fan" and "set_on" in component.commands


def is_cover_component(component: Component) -> bool:
    """True when LOIP declares type=cover and can open/close/stop."""
    return component.type == "cover" and any(
        cmd in component.commands for cmd in ("open", "close", "stop")
    )


def is_scene_component(component: Component) -> bool:
    """True when LOIP declares type=scene and can be activated via set_on."""
    return component.type == "scene" and "set_on" in component.commands


def cover_position_range(component: Component | None) -> tuple[int, int] | None:
    """Declared position min/max, or None when the cover cannot report position."""
    if component is None:
        return None
    if "position" not in component.features:
        return None
    if "set_position" not in component.commands:
        return None
    raw = component.constraints.get("position")
    if not isinstance(raw, dict):
        return None
    lo = _as_int(raw.get("min", 0))
    hi = _as_int(raw.get("max", 100))
    if lo is None or hi is None or hi < lo:
        return None
    return lo, hi


def brightness_levels(component: Component | None) -> list[int] | None:
    """Declared non-zero brightness steps, or None when brightness is absent."""
    if component is None:
        return None
    if "set_brightness" not in component.commands or "brightness" not in component.features:
        return None
    return _on_levels(component.constraints, "brightness")


def speed_levels(component: Component | None) -> list[int] | None:
    """Declared non-zero speed steps, or None when speed levels are absent."""
    if component is None:
        return None
    if "set_speed_level" not in component.commands or "speed_levels" not in component.features:
        return None
    return _on_levels(component.constraints, "speed_level")


def ha_brightness_to_device(brightness: int, levels: list[int]) -> int:
    """Map HA brightness 0..255 onto a declared level. 0 is off."""
    if brightness <= 0 or not levels:
        return 0
    if len(levels) == 1:
        return levels[0]
    lo = levels[0]
    hi = levels[-1]
    raw = (brightness - 1) / 254 * (hi - lo) + lo
    return min(levels, key=lambda level: (abs(level - raw), level))


def device_brightness_to_ha(value: int, levels: list[int]) -> int | None:
    """Map a device brightness back to HA 1..255. Off stays None."""
    if value <= 0 or not levels:
        return None
    lo = levels[0]
    hi = levels[-1]
    snapped = min(levels, key=lambda level: (abs(level - value), level))
    if hi == lo:
        return 255
    return round((snapped - lo) / (hi - lo) * 254 + 1)


def percentage_to_speed(percentage: int, levels: list[int]) -> int | None:
    """Map HA 1..100 onto a declared speed. 0 is off and returns None."""
    if percentage <= 0 or not levels:
        return None
    count = len(levels)
    index = math.ceil(percentage * count / 100) - 1
    if index < 0:
        index = 0
    if index >= count:
        index = count - 1
    return levels[index]


def speed_to_percentage(level: int, levels: list[int]) -> int:
    """Map a device speed back to HA 0..100. 0 and unknown low values are off."""
    if level <= 0 or not levels:
        return 0
    if level not in levels:
        level = min(levels, key=lambda item: (abs(item - level), item))
    return (levels.index(level) + 1) * 100 // len(levels)


def light_is_on(component: Component) -> bool | None:
    levels = brightness_levels(component)
    if levels is not None:
        raw = _as_int(component.state.get("brightness"))
        if raw is not None:
            return raw != 0
    if "on" not in component.state:
        return None
    return bool(component.state.get("on"))


def fan_is_on(component: Component) -> bool | None:
    levels = speed_levels(component)
    if levels is not None:
        raw = _as_int(component.state.get("speed_level"))
        if raw is not None:
            return raw != 0
    if "on" not in component.state:
        return None
    return bool(component.state.get("on"))


def _iter_components(snapshot: DeviceSnapshot | None, predicate) -> list[tuple[Device, Component]]:
    if snapshot is None:
        return []
    rows: list[tuple[Device, Component]] = []
    for device in snapshot.devices:
        for component in device.components:
            if predicate(component):
                rows.append((device, component))
    return rows


def iter_switch_components(snapshot: DeviceSnapshot | None) -> list[tuple[Device, Component]]:
    return _iter_components(snapshot, is_switch_component)


def iter_light_components(snapshot: DeviceSnapshot | None) -> list[tuple[Device, Component]]:
    return _iter_components(snapshot, is_light_component)


def iter_fan_components(snapshot: DeviceSnapshot | None) -> list[tuple[Device, Component]]:
    return _iter_components(snapshot, is_fan_component)


def iter_cover_components(snapshot: DeviceSnapshot | None) -> list[tuple[Device, Component]]:
    return _iter_components(snapshot, is_cover_component)


def iter_scene_components(snapshot: DeviceSnapshot | None) -> list[tuple[Device, Component]]:
    return _iter_components(snapshot, is_scene_component)
