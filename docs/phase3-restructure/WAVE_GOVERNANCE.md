# Wave Governance — Phase 3 Restructure

**Epic:** Phase 3 Multi-Tenant Restructure  
**PRD:** [PRD_PHASE3_MULTI_TENANT.md](PRD_PHASE3_MULTI_TENANT.md)  
**Backlog:** [SPRINT_BACKLOG_NT.md](SPRINT_BACKLOG_NT.md)  
**Pipelines:** [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)

---

## Branch model

```
main                          ← production releases (protected)
dev                           ← integration trunk (optional; or use main)
demo/live                     ← frozen pitch demo (tag: demo-live-vX.Y.Z)
feature/phase3                ← legacy integration (merge → dev)
feature/phase-3-restructure/
  wave3                       ← Wave 3 integration (assets)
  wave4                       ← Wave 4 integration (invoices)
  wave5                       ← Wave 5 integration (hardening)
  wave3/NT-117-asset-calendar  ← ticket branches (short-lived)
```

### Rules

| Rule | Detail |
|------|--------|
| **Wave branch** | One long-lived integration branch per wave: `feature/phase-3-restructure/wave{N}` |
| **Ticket branch** | `feature/phase-3-restructure/wave{N}/NT-{id}-{slug}` → PR targets **wave{N}**, not `main` |
| **Demo branch** | `demo/live` only receives merges after wave sign-off + Abdullah approval; tag each release |
| **No direct to main** | Wave work merges: ticket → wave{N} → `dev` → `main` at phase milestone |
| **AgDR / schema** | Required in PR if migration or tenant boundary changes |

### Creating a wave branch

```powershell
git fetch origin
git checkout dev   # or feature/phase3 until dev exists
git pull
git checkout -b feature/phase-3-restructure/wave3
git push -u origin feature/phase-3-restructure/wave3
```

### Closing a wave

1. All tickets **Done** in wave tracker + GitHub Issues closed  
2. [WAVE{N}_SIGNOFF.md](WAVE3_SIGNOFF.md) checklist green  
3. E2E suite for wave green in CI  
4. Code review: Rex (code-reviewer) + human (Abdullah) on **wave merge PR** → `dev`  
5. Open next wave branch from updated `dev`

---

## Wave artifacts (required per wave)

| Artifact | Path pattern | Owner |
|----------|--------------|-------|
| Ticket tracker | `WAVE{N}_TICKETS.md` | tech-lead |
| Sign-off gate | `WAVE{N}_SIGNOFF.md` | qa-engineer + Abdullah |
| E2E test plan | `WAVE{N}_E2E.md` | qa-engineer |
| Full test matrix | `WAVE{N}_FULL_TEST_MATRIX.md` | qa-engineer |
| Test strategy (once) | [TEST_STRATEGY.md](TEST_STRATEGY.md) | qa-engineer + tech-lead |
| UAT observations | `WAVE{N}_OBSERVATIONS.md` (when UAT run) | qa-engineer + product |
| Backend tests | `backend/tests/test_wave{N}_*.py` | qa-engineer / feature dev |
| CI scope | `.github/workflows/ci.yml` (wave label or path filter) | platform-engineer |

---

## PR & code review process

### Ticket PR (into wave branch)

**Title:** `feat(NT-XXX): short description`  
**Target branch:** `feature/phase-3-restructure/wave{N}`

**Required PR sections:**

```markdown
## Summary
- What changed and why (1–3 bullets)

## Ticket
- NT-XXX — link to GitHub Issue

## Test plan
- [ ] pytest cases added/updated (IDs)
- [ ] npm run build
- [ ] Manual smoke (role + route)

### Acceptance (ticket AC)
- [ ] AC bullets mapped to test IDs (see TEST_STRATEGY.md)

### Regression
- [ ] Full `pytest -q` + build green

### E2E
- [ ] Scenario IDs (GP-xx / INV-xx) — spec file or N/A + reason

### Full matrix
- [ ] Rows updated in `WAVE{N}_FULL_TEST_MATRIX.md`

## AgDR / schema
- [ ] N/A  OR  link to AgDR / migration ticket

## Review markers
- [ ] Rex (code-reviewer) approved
- [ ] Security (if auth/RBAC/tenant): security-reviewer
```

### Wave merge PR (into `dev`)

**Title:** `release(phase3): Wave {N} — {theme}`  
**Target:** `dev`

**Gates (all must pass):**

| Gate | Tool / role |
|------|-------------|
| CI green | GitHub Actions `ci.yml` |
| E2E green | `wave-e2e.yml` (Playwright) |
| Sign-off doc | `WAVE{N}_SIGNOFF.md` all boxes checked |
| Rex review | code-reviewer on wave PR |
| Human approval | Abdullah |
| No open P0 on wave tickets | GitHub Issues |

---

## Parallel execution (Agile lanes)

Each wave runs **2–4 parallel lanes** (see per-wave ticket doc). Daily flow:

1. **Plan** — tech-lead assigns tickets to lanes in `WAVE{N}_TICKETS.md`  
2. **Build** — ticket branches → PR → wave branch (continuous integration)  
3. **Verify** — QA adds/extends tests; E2E runs on wave branch nightly  
4. **Review** — Rex on each ticket PR; architect on schema PRs  
5. **Sign-off** — QA + Abdullah; merge wave → `dev`  
6. **Retro** — optional memo in sign-off doc Notes section  

---

## Wave status (2026-06-06)

| Wave | Theme | Branch | Status |
|------|-------|--------|--------|
| 0 | Architecture & migration | — | ✅ Closed |
| 1 | Platform & licensing | — | ✅ Closed |
| 2 | Demo environment | `demo/live` | ✅ Closed (tagged) |
| 2+ | RBAC + Render one-URL (ahead of schedule) | on `feature/phase3` | ✅ Done (undocumented in NT; see Wave 5 delta) |
| **3** | Assets module | `feature/phase-3-restructure/wave3` | 🟡 **START** |
| 4 | Invoices & workflows | `feature/phase-3-restructure/wave4` | ⬜ Blocked on Wave 3 sign-off |
| 5 | Role hardening & phase sign-off | `feature/phase-3-restructure/wave5` | ⬜ Partial (RBAC landed early) |

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [WAVE3_TICKETS.md](WAVE3_TICKETS.md) | Wave 3 tracker |
| [WAVE3_SIGNOFF.md](WAVE3_SIGNOFF.md) | Wave 3 gate |
| [WAVE3_E2E.md](WAVE3_E2E.md) | Wave 3 Playwright plan |
| [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) | CI/CD design |
| [DEMO_RENDER_ONE_URL.md](DEMO_RENDER_ONE_URL.md) | Demo deploy (Wave 2+) |
