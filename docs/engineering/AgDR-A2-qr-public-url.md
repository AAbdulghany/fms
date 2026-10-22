# AgDR-A2 — Public asset QR URL scheme

**Status:** Accepted  
**Date:** 2026-10-22  
**Program:** A2

## Decision

Printed asset QR codes encode:

```text
{PUBLIC_APP_URL}/a/{token}
```

- `token` is a 12-character Crockford base32 string (no UUID, no tenant id).
- `PUBLIC_APP_URL` is the stable public origin (pilot/production). Changing it after labels are printed breaks scans — treat as irreversible without a reprint campaign.
- Legacy `qr_payload` values that still contain `/assets/{uuid}` remain resolvable until backfill regenerates tags.

## Alternatives rejected

| Option | Why not |
|--------|---------|
| `/assets/{uuid}` in the QR | Leaks internal ids; hard to rotate; couples print to DB PK |
| Short domain + UUID | Still identifier leakage |
| Signed JWT in QR | Too long for small labels; clock skew |

## Consequences

- New table `asset_tags` (one active tag per asset in A2).
- Resolver route `GET /a/{token}` (SPA) + `GET /api/v1/public/asset-tags/{token}` (API).
- Label PDF must embed a QR **image**, not the URL as text alone.
