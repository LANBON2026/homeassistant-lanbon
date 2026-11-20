# Changelog

## 0.3.4 - 2026-11-20

### Fixed
- Fix scene platform import for HA 2026.x: SceneEntity was replaced by Scene in homeassistant.components.scene. The failed import crashed the whole LANBON config entry setup, which also blocked switch/light/fan.

## 0.3.3 - 2026-11-20

### Added
- New LOIP platforms: **cover** and **scene**.
- `cover` supports open/close/stop (+ set_position when the gateway declares `position`; L10 2749 reports motion only).
- `scene` maps L8 scene switches (`scene:1/2/3`, `1G2S`, `2G1S`) to HA scene activation via `set_on`.
- Entity mapping helpers `is_cover_component`, `is_scene_component`, `iter_cover_components`, `iter_scene_components`, `cover_position_range`.

### Changed
- `PLATFORMS` extended from `[switch, light, fan]` to `[switch, light, fan, cover, scene]`.

## 0.3.2 - 2026-11-16

### Fixed
- Restore local `brand/` icons and logos from 0.2.12 so HA 2026.3+ shows the LANBON mark (HACS-only; does not touch Core PR).

## 0.3.0 - 2026-11-16

### Changed
- Switch the HACS integration to the LOIP client path via PyPI package iolanbon==0.2.0.
- Local polling/push model: HTTP snapshot + WebSocket events through aiolanbon.
- Platforms in this release: switch, light, fan (cover deferred vs older 0.2.x package).
- Add diagnostics, entity mapping helpers, and mDNS helpers used by the LOIP adapter.

### Notes
- Requires panels speaking LOIP local API. Legacy 0.2.12 Mesh HTTP/WS package remains available as GitHub release 0.2.12 if you still run older firmware.
- Home Assistant Core PR is separate; this HACS release does not change that review.

## 0.2.12 - 2026-08-07

### Fixed
- Stop WebSocket reconnect storms on HTTP-only panels (e.g. L8). After product detection or 3 consecutive WS-reject handshakes, disable WS for that config entry and use 30s HTTP poll only. L10 unchanged; transient offline does not disable WS.

## 0.2.11 - 2026-08-06

### Fixed
- Entity availability now follows hub reachability.

## 0.2.10 - 2026-08-04

### Changed
- Device registry names no longer hardcode LANBON-L10. Display name comes from firmware 
ame / 	ype_name.
