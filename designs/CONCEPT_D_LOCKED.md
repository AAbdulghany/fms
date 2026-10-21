# Concept D locked — field shell

**Date:** 2026-10-21  
**Decision:** Ship Concept D for on-site technicians / engineers / customers.  
**Menu contents under More:** deferred (discuss later).

## Shell

| Tab | Route (v1) | Job |
|-----|------------|-----|
| Queue | `/work-orders` | Start next, create WO, change status |
| Scan | `/assets` | Find/open asset (QR later) |
| Time | `/labor` | Log time |
| More | opens sidebar | Overflow — TBD |

Desktop (`lg+`): full sidebar unchanged.

## Palette comparison (Pencil board)

| ID | Name | Status |
|----|------|--------|
| P0 | Current Industrial Teal | retired for D |
| P1 | Harbor Navy | alternate |
| P2 | Field Olive | alternate |
| P3 | Midnight Steel | alternate |
| **P4** | **Copper Signal** | **Applied in `tokens.css`** |

## Pattern comparison

| ID | Name | Status |
|----|------|--------|
| Pat1 | Blueprint grid | alternate |
| **Pat2** | **Dot grid** | **Applied via `.orbit-app-shell`** |
| Pat3 | Diagonal hatch | alternate |
| Pat4 | Soft waves | alternate |

To switch palette or pattern: say the ID (e.g. “use P2 + Pat3”) and we retoken.

## Full pages (Pencil)

Board **“D FINAL — full pages (locked)”** in `orbit-mobile-first-layouts.pen`:  
Queue · Active WO · Create WO · Scan · Time · Asset · More · Desktop companion.
