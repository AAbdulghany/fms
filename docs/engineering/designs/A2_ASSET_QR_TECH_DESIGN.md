# A2 — Asset QR labels: Technical Design

**Status:** Draft for build  
**Date:** 2026-10-22  
**AgDR:** [AgDR-A2-qr-public-url.md](../AgDR-A2-qr-public-url.md)

## 1. Model

`asset_tags`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | FK tenants | |
| asset_id | FK assets | |
| token | String(16) unique | Crockford base32, 12 chars |
| status | String(16) | `active` \| `revoked` |
| created_at | timestamptz | |
| revoked_at | timestamptz nullable | |

Index: `(asset_id, status)` unique partial for one active tag per asset (SQLite: enforce in service).

## 2. Services

- `services/asset_tags.py`: `ensure_active_tag(db, asset) -> AssetTag`, `resolve_token(db, token)`, `revoke_and_mint`
- Update `qr_payload_for_asset` to prefer tag URL: `{PUBLIC_APP_URL}/a/{token}`
- `pdf.render_asset_label_pdf(asset, *, client_name, size_mm, design)` → sticker PDF:
  - **A** Docked Square (default): navy frame, copper corner, Orbit in QR center; `size_mm` = side (default 50)
  - **C** Field Tag: landscape 12:7, copper spine + hang hole; `size_mm` = width (default 60)
  - Query: `?design=a|c&size_mm=30..100` · env defaults `ASSET_LABEL_DESIGN` / `ASSET_LABEL_SIZE_MM`

## 3. API

| Method | Path | Auth | Behaviour |
|--------|------|------|-----------|
| GET | `/api/v1/public/asset-tags/{token}` | Optional | Anon: `{token, name, client_name, site_name, can_report: true}`. Authed same tenant: + `asset_id`, `has_history` |
| POST | `/api/v1/public/asset-tags/{token}/report` | Anon | Body: `{title, description, contact?}`. Creates WO `source=request` or ServiceRequest stub. Rate limit 5/hour/IP+token |
| GET | `/assets/{id}/label-sheet` | Existing | Uses tag URL + client name |
| POST | `/assets/{id}/qr/rotate` | company_admin | Revoke + mint |

## 4. Frontend

- `AssetQrModal` (like SiteQrModal) — show QR for `/a/{token}`, print opens label-sheet PDF
- Route `/a/:token` → `AssetTagLandingPage`: if session + in-tenant → navigate to `/assets/:id`; else report form
- i18n EN/AR

## 5. Migration

Alembic expand: create `asset_tags`. Backfill CLI `python -m app.cli.backfill_a2_tags` mints tags for assets missing active tags and rewrites `qr_payload`.

## 6. Security

- Opaque tokens; no sequential ids
- Anon payload redaction
- Rate limit (in-process dict keyed by IP+token; document upgrade to Redis in B0)
- Always filter `tenant_id` when authed
