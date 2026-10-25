# UAT — WO + Report layout (#3 + #7)

**Status:** **Accepted for UAT** (editable later) · HTML is source of truth until Pencil port  
**HTML board:** [uat-wo-report-flow.html](./uat-wo-report-flow.html)  
**Decisions locked:** #2 No · #5 Hide Labor · #6 Hide Locations · #3+#7 proceed with tweaks below

## Tweaks (vs first verbal proposal)

1. **Complete** disabled until report submitted (admin may waive later — not in UAT).
2. **Parts** = accordion under Report (not a separate top-level maze).
3. **Codes / downtime** = short strip on Job tab; echoed in History.
4. **Documents** → Evidence under History (report photos + PDFs).

## Frames to put in `.pen`

| ID | Frame | Purpose |
|----|-------|---------|
| M1 | Mobile · Job | Sticky next-status CTAs + context |
| M2 | Mobile · Report | Checklist + inspector note + photo |
| M3 | Mobile · History | Structured diagnosis timeline |
| M4 | Mobile · AR RTL | Same as M1 mirrored |
| D1 | Desktop · Split | Left stepper / Right diagnosis |
| T1 | Admin template | Slots for note + photo |
| T2 | Field attach | Note/photo write into report |

## Ship order (remaining)

`1 Clients → 9 Orbit-Tenant → 4 Commercial CRUD → 8 Asset types → 3+7 (this) → 5/6 hide nav`
