# LANBON Home Assistant (HACS)

Local control for LANBON Mesh root panels over the LOIP HTTP/WebSocket API.

## Install

1. HACS → Integrations → Custom repositories
2. URL: https://github.com/LANBON2026/homeassistant-lanbon
3. Category: Integration
4. Download **LANBON** → Restart Home Assistant → Add Integration

## Requirements

- Home Assistant 2026.3.0+
- PyPI dependency: iolanbon==0.2.0 (installed automatically from manifest.json)
- Panel firmware that exposes the LOIP local API (port 8765 by default)

## Platforms (0.3.0)

- switch
- light
- fan

## Legacy

Release **v0.2.12** is the last pre-LOIP HACS package (built-in HTTP/WS client, no iolanbon). Keep using that tag if your panels are still on the older local API.

## Links

- Releases: https://github.com/LANBON2026/homeassistant-lanbon/releases
- Client library: https://github.com/LANBON2026/aiolanbon
