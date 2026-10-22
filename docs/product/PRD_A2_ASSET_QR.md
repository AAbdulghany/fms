# PRD — A2 Asset QR labels

**Product:** Orbit AM  
**Date:** 2026-10-22

## Problem

Technicians and clients need a physical mark on each asset. Today the label PDF prints a raw URL (often with a UUID). Scanning should open the right asset without exposing internal ids, and unauthenticated scanners must not see maintenance history.

## Personas

- **Farida (company admin)** — prints labels after register
- **Ahmed (technician)** — scans on site while logged in
- **Guest / client staff** — scans with phone camera, not logged in; reports a problem

## Stories (MVP)

1. As Farida, I print a label with **client company name** + QR so installers can stick it on the asset.
2. As Ahmed (logged in), I scan the QR and land on asset detail with maintenance history.
3. As a guest, I scan and only see asset name / site / company and a **Report a problem** form.
4. As Farida, I can rotate a tag if a label is compromised (old QR stops resolving).

## Out of scope

Inventory (A3), VAT (A4), WhatsApp, offline scan cache, custom label templates.

## Sprint companions (A1 leftovers)

- Finish / track E2E #30 for asset types
- Feature-gate test for `/asset-types`
- Remove dead adopt duplicate module
