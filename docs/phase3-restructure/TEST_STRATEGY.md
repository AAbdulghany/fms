# Test Strategy — Phase 3 (Four-Tier Model)

**Owner:** qa-engineer + tech-lead  
**Applies to:** All waves from Wave 3 onward  
**Related:** [WAVE_GOVERNANCE.md](WAVE_GOVERNANCE.md) · [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)

Every wave ticket and PR must map work to **one or more** of the tiers below. Do not mix tiers in a single test file without labeling.

---

## Tier definitions

| Tier | Question it answers | Tool | When it runs | Example artifact |
|------|---------------------|------|--------------|------------------|
| **Acceptance** | Does this ticket meet its signed acceptance criteria? | pytest (focused) + manual checklist | Ticket PR + sign-off | `test_report_in_progress.py::test_completed_blocked_without_report` |
| **Regression** | Did we break anything that already worked? | Full `pytest -q` + `npm run build` | Every PR (CI Stage 1) | `.github/workflows/ci.yml` |
| **E2E scenarios** | Can a real user complete the journey in the browser? | Playwright | Wave branch nightly + pre-merge | `tests/e2e/wave4-golden-path.spec.ts` |
| **Full test cases** | Complete traceability matrix (AC × role × route × edge) | Spreadsheet + linked automated IDs | Wave sign-off audit | [WAVE4_FULL_TEST_MATRIX.md](WAVE4_FULL_TEST_MATRIX.md) |

### Acceptance test cases

- **Scope:** One ticket's acceptance criteria only (NT-XXX AC bullets).
- **Format:** Given / When / Then in ticket tracker; automated where cheap (API-level pytest).
- **Pass rule:** All AC boxes checked in `WAVE{N}_TICKETS.md` with test ID reference.
- **Not for:** Cross-module journeys (those are E2E).

### Regression test cases

- **Scope:** Entire backend suite + frontend build; wave-scoped files `test_wave{N}_*.py`.
- **Format:** pytest module docstring lists ticket IDs covered.
- **Pass rule:** 0 failures on PR; no skipped tests without documented reason.
- **Not for:** UI-only flows without API equivalent (use E2E).

### E2E scenarios

- **Scope:** Multi-step user journeys visible in the SPA (login → action → assert DOM/network).
- **Format:** Scenario ID (`GP-01`, `INV-03`, `AST-01`) in `WAVE{N}_E2E.md` + matching `test()` in Playwright.
- **Pass rule:** Green in `playwright-e2e-demo.yml` or explicitly skipped with backend substitute + sign-off note.
- **Not for:** Unit-level validation logic (use Acceptance pytest).

### Full test cases

- **Scope:** Master matrix: every scenario × role × environment × expected result.
- **Format:** Markdown table linking scenario ID → acceptance / regression / E2E automation ID.
- **Pass rule:** Wave sign-off requires matrix reviewed; gaps marked `manual` or `deferred` with owner.
- **Purpose:** Audit trail for UAT, Rex review, and release notes — not a fourth test runner.

---

## Mapping workflow (per ticket)

When closing a ticket in `WAVE{N}_TICKETS.md`:

```markdown
| Ticket | Acceptance tests | Regression | E2E | Full matrix rows |
|--------|------------------|------------|-----|------------------|
| NT-122 | test_report_in_progress (5) | pytest full | GP-05..GP-08 | W4-AC-122-01..05 |
```

### PR Test plan template (required)

```markdown
## Test plan
### Acceptance
- [ ] NT-XXX AC-1 — `test_foo.py::test_bar`
### Regression
- [ ] `pytest -q` green
- [ ] `npm run build` green
### E2E
- [ ] GP-XX / INV-XX — `tests/e2e/...spec.ts` (or N/A + reason)
### Full matrix
- [ ] Rows W4-AC-XXX-* updated in WAVE4_FULL_TEST_MATRIX.md
```

---

## Wave 4 test inventory (current)

| Suite | Tier | Location | Count | Status |
|-------|------|----------|-------|--------|
| WO FSM + report | Acceptance | `test_report_in_progress.py` | 5 | ✅ |
| Schedule anchor | Acceptance | `test_wave4_schedule_anchor.py` | 9 | ✅ |
| Invoice computation | Acceptance | `test_invoice_computation.py` | 3 | ✅ |
| Billing setup | Acceptance | `test_invoice_computation.py` | 2 | ✅ |
| PDF smoke | Acceptance | `test_maintenance_report_pdf.py` | 3 | ✅ |
| Invoices feature gate | Acceptance | `test_wave4_invoices.py` | 3 | ✅ |
| Full backend | Regression | `pytest -q` (~212+) | all | CI |
| Frontend build | Regression | `npm run build` | 1 | CI |
| Assets module | E2E | `wave3-assets.spec.ts` | 5+1 skip | ✅ |
| Invoice module | E2E | `wave4-invoices.spec.ts` | 0/6 | ⬜ NT-127 |
| Golden path | E2E | `wave4-golden-path.spec.ts` | 0/12 | ⬜ NT-132 |
| Master matrix | Full | `WAVE4_FULL_TEST_MATRIX.md` | — | ⬜ NT-133 |

---

## Friendly errors (NT-131)

API may keep machine-readable `detail` codes for logs and tests. **Users must never see raw codes** in the UI.

| Layer | Responsibility |
|-------|----------------|
| Backend | Stable `detail` code (e.g. `REPORT_REQUIRED`) + optional structured `{ code, fields }` |
| Frontend | Central `resolveApiError(code, t)` in `src/lib/errors.ts` → i18n AR/EN |
| i18n | All codes under `error_<code_lowercase>` in `src/i18n/index.ts` |
| Tests | Acceptance: assert API code; E2E: assert **translated** message visible |

---

## CI alignment

| Stage | Tiers executed |
|-------|----------------|
| Stage 1 Verify (every PR) | Regression + Acceptance (via full pytest) |
| Stage 2 Integrate (wave branch) | Regression + E2E scenarios |
| Stage 3 Sign-off | Full test matrix audit + manual UAT rows |

See [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) for job commands.
