# A2 sprint cycle — Asset QR labels

**Program:** Orbit Program A, slice A2  
**Date opened:** 2026-10-22  
**Status:** In progress  
**Depends on:** A1 landed on `feature/a1-verticals-asset-types` / PR #31  
**Tickets:** [#32](https://github.com/AAbdulghany/fms/issues/32) BE · [#33](https://github.com/AAbdulghany/fms/issues/33) FE · [#34](https://github.com/AAbdulghany/fms/issues/34) QA  
**AgDR:** [AgDR-A2-qr-public-url.md](../AgDR-A2-qr-public-url.md)  
**Design:** [A2_ASSET_QR_TECH_DESIGN.md](../designs/A2_ASSET_QR_TECH_DESIGN.md)  
**PRD:** [PRD_A2_ASSET_QR.md](../../product/PRD_A2_ASSET_QR.md)

---

## 1. Description

Replace UUID deep links on asset labels with opaque `/a/{token}` tags. Printable PDF includes company (client) name + QR image. Authenticated scanners see asset detail + WO history; anonymous scanners get a rate-limited “report a problem” form only.

### A1 carry-over (this sprint)

| ID | Item | Done means |
|----|------|------------|
| A1-C1 | Delete unused `asset_type_adopt.py` (canonical adopt is `asset_types_service.adopt_templates`) | Done |
| A1-C2 | U-X-04: `/asset-types` denied when package lacks `assets` | Done (`test_a1_c2_…` in test_asset_qr_tags) |
| A1-C3 | #30 E2E A1 scenarios | Tracked on #34; defer skeleton to QA ticket |
| A1-C4 | Postgres Alembic up/down for A1 migration | Manual checklist on pilot |

### Done means (A2)

- [x] `asset_tags` table + ensure-on-create; backfill CLI for existing assets
- [x] `qr_payload` uses `/a/{token}` when `PUBLIC_APP_URL` set
- [x] Label PDF shows client legal name + QR image
- [x] Public resolve API + SPA `/a/:token` (auth vs anon)
- [x] Unit + API tests for tag mint, resolve, cross-tenant 404, rate limit

---

## 2. Unit / API tests

| ID | Test |
|----|------|
| U-QR-01 | Creating an asset mints an active `AssetTag` and sets `qr_payload` to `{PUBLIC}/a/{token}` |
| U-QR-02 | Token is unique; regenerate rotates old tag to `revoked` |
| U-QR-03 | `GET /api/v1/public/asset-tags/{token}` anon returns name, site, client name — **no** WO history |
| U-QR-04 | Authenticated same-tenant resolve returns `asset_id` + history summary flag |
| U-QR-05 | Cross-tenant token → 404 |
| U-QR-06 | Label PDF bytes contain PNG/JPEG marker for QR (not text-only) |
| U-QR-07 | Anon report-problem endpoint rate-limits after N posts per IP+token |
| A1-C2 | Feature gate: no `assets` feature → `/asset-types` 403 |

---

## 3. E2E (Playwright)

| ID | Scenario | Spec |
|----|----------|------|
| E-CO-01 | Create company (client) + first site | `a2-company-asset-qr.spec.ts` |
| E-CO-02 | Add second site on company | same |
| E-AT-01 | Create asset type with defaults | same |
| E-AS-01 | Register asset — inherits type criticality / max age | same |
| E-AS-02 | Second asset same type — same inherited defaults | same |
| E-QR-01 | Each asset shows unique opaque `/a/{token}` QR | same |
| E-QR-02 | Open `/a/{token}` logged in → asset page | `a2-asset-qr.spec.ts` (skipped until seed token) |
| E-QR-03 | Open `/a/{token}` logged out → report form only | skipped until seed token |

---

## 4. GitHub issues

1. [#32](https://github.com/AAbdulghany/fms/issues/32) `[A2][BE] AssetTag model, public resolve, QR PDF, A1 carry tests`
2. [#33](https://github.com/AAbdulghany/fms/issues/33) `[A2][FE] Asset QR modal, /a/:token landing (auth + anon)`
3. [#34](https://github.com/AAbdulghany/fms/issues/34) `[A2][QA] E2E QR + finish A1 #30 scenarios`

---

## 5. PR review checklist

- [ ] No UUID in new printed payloads
- [ ] Anon response never includes WO list / serial / warranty
- [ ] Tenant filter on every tag lookup
- [ ] A1 carry items closed or explicitly deferred in PR body
