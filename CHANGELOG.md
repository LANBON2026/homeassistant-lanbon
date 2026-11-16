# Changelog

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
