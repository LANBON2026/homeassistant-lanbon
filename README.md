# LANBON Home Assistant Integration

Local integration for **LANBON Mesh root** panels (HTTP + WebSocket, no cloud required for control).

| | |
|---|---|
| Domain | `lanbon` |
| Version | **0.2.0** |
| Discovery | mDNS `_lanbon._tcp` |
| API port | **8765** |
| IoT class | `local_push` |

## Install

### A. Manual (fastest)

1. Copy `custom_components/lanbon` → `/config/custom_components/lanbon`
2. Restart Home Assistant
3. **Settings → Devices & services → Add Integration → LANBON**
4. Enter host IP, port `8765`, and Bearer token

Token appears in firmware log:

```text
W (...) haLocal: HA local API up (mesh root). token=xxxxxxxx
```

### B. HACS

> Publish this `homeassistant/` folder as its **own** git repository (recommended), then:

1. HACS → Integrations → ⋮ → Custom repositories  
2. URL = your HA repo, Category = **Integration**  
3. Download **LANBON**, restart HA  
4. Add Integration / accept discovery

If you keep this tree inside the firmware monorepo, HACS must point at a repo whose root contains `custom_components/lanbon` (this folder’s layout).

## Prerequisites

- Panel is **Mesh root** (level 1) — only root runs the local API / mDNS
- HA and panel on the same LAN (Docker/WSL2 often break mDNS → use manual IP)
- Firmware with HA local API (`HA_LOCAL_PROTO_VER = 1`)

## Verify before HA

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://DEVICE_IP:8765/api/v1/info
curl -H "Authorization: Bearer YOUR_TOKEN" http://DEVICE_IP:8765/api/v1/devices
```

## Features

- Host + Mesh children as devices (`via_device` for children)
- Platforms: **switch**, **light**, **cover**
- State push over WebSocket; HTTP poll every 30s as fallback
- Channel rename: service `lanbon.set_channel_name` or rename entity in HA UI

## Docs

- [Local API contract (frozen)](docs/API.md) — **do not break without bumping `proto`**
- [Changelog](CHANGELOG.md)
- [Bronze checklist (path to Core)](BRONZE_CHECKLIST.md)

## Roadmap to official Core

1. Stabilize on HACS (this package)
2. Keep `docs/API.md` as the public contract
3. Fill [BRONZE_CHECKLIST.md](BRONZE_CHECKLIST.md)
4. Open PR against `home-assistant/core` + brands + docs

## License

Same as product / company policy. Replace with SPDX when publishing a public repo.
