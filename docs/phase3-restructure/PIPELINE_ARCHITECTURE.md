# Pipeline Architecture — Agile Delivery for Phase 3

**Goal:** Short feedback loops, parallel wave lanes, clear quality gates — aligned with Scrum/Agile (small batches, Definition of Done, continuous integration).

**Governance:** [WAVE_GOVERNANCE.md](WAVE_GOVERNANCE.md)

---

## Principles (Agile mapping)

| Agile principle | Pipeline expression |
|-----------------|---------------------|
| **Small batches** | One PR per NT ticket → wave branch (not monolithic phase PR) |
| **Fast feedback** | CI on every PR in &lt;10 min (unit + build) |
| **Definition of Done** | Ticket DoD = tests + Rex review + tracker updated |
| **Sprint / wave goal** | Wave sign-off = E2E + merge to `dev` |
| **Working software** | `demo/live` deploy from tagged `dev` after wave 2+ sign-off |
| **Inspect & adapt** | Nightly E2E on wave branch; retro notes in sign-off doc |

---

## Architecture overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Developer workflow                               │
├─────────────────────────────────────────────────────────────────────────┤
│  NT ticket branch  ──PR──►  feature/phase-3-restructure/wave{N}         │
│                                      │                                   │
│                                      ├── CI (unit + build)  ◄── every PR │
│                                      ├── E2E (Playwright)   ◄── wave PR  │
│                                      └── Rex + human review              │
│                                      │                                   │
│                                      ▼                                   │
│                              PR ──► dev ──► main                         │
│                                      │                                   │
│                                      ▼ (tag)                             │
│                              demo/live ──► Render (optional CD)          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline stages

### Stage 1 — **Verify** (every ticket PR, ~8 min)

| Job | Command | Fail fast |
|-----|---------|-----------|
| Backend unit | `cd backend && pytest -q --tb=no` | Yes |
| Frontend build | `npm ci && npm run build` | Yes |
| Lint (optional) | `ruff check backend` / ESLint | Warn → fail in Wave 4 |

**Trigger:** PR to `feature/phase-3-restructure/wave*` or `dev`  
**Workflow:** `.github/workflows/ci.yml`

### Stage 2 — **Integrate** (wave branch, nightly + pre-merge)

| Job | Command | Purpose |
|-----|---------|---------|
| Full regression | `pytest` + coverage threshold (future) | Catch cross-ticket breaks |
| E2E smoke | `playwright test tests/e2e/wave{N}-*.spec.ts` | User journeys per wave |
| Docker demo smoke | `compose up` + `/health` + login API | Infra regressions (weekly) |

**Trigger:** push to wave branch, schedule cron, manual  
**Workflow:** `.github/workflows/playwright-e2e-pilot.yml`

### Stage 3 — **Review** (human + agent gates)

| Gate | When | Who |
|------|------|-----|
| Automated code review | Ticket PR | code-reviewer (Rex) |
| Security review | Auth/RBAC/tenant PRs | security-reviewer |
| Architecture | Schema / AgDR changes | solution-architect |
| Product sign-off | Wave merge PR | Abdullah |

**Not in CI** — process gates documented in [WAVE_GOVERNANCE.md](WAVE_GOVERNANCE.md).

### Stage 4 — **Release** (post sign-off)

| Target | Trigger | Action |
|--------|---------|--------|
| `dev` | Wave merge PR merged | Auto CI on `dev` |
| `demo/live` | Manual / tag `demo-live-v*` | Render deploy or Docker |
| `main` | Phase 3 complete (Wave 5 sign-off) | Release PR + changelog |

**Workflow (future):** `.github/workflows/deploy-demo.yml` — Render deploy hook on tag.

---

## Branch ↔ CI matrix

| Branch pattern | CI verify | E2E | Deploy |
|----------------|-----------|-----|--------|
| `feature/phase-3-restructure/wave3/**` | ✅ | wave3 specs | — |
| `feature/phase-3-restructure/wave4/**` | ✅ | wave4 specs | — |
| `dev` | ✅ | all e2e | — |
| `demo/live` | ✅ | smoke | Render (manual/auto) |
| `main` | ✅ | full | production (future) |

---

## Parallel delivery lanes (CI-friendly)

Run **in parallel** within a wave (matches [SPRINT_BACKLOG_NT.md](SPRINT_BACKLOG_NT.md)):

```
Wave 3:  [NT-116, NT-120]  ∥  [NT-117 → NT-118 → NT-119]  →  NT-121
Wave 4:  [NT-122 → NT-123 → NT-124 → NT-125]  ∥  NT-126  →  NT-127
```

**CI implication:** Path filters optional later — e.g. frontend-only PRs skip full pytest if no backend diff (speed vs safety tradeoff; start with full suite).

---

## Environment strategy

| Env | Branch / tag | APP_ENV | Purpose |
|-----|--------------|---------|---------|
| Local dev | — | development | Engineer daily work |
| Local demo | compose demo | demo | Pitch rehearsal |
| CI | ephemeral Postgres service | development | pytest |
| CI E2E | compose demo in Actions | demo | Playwright |
| Public demo | `demo/live` on Render | demo | Evaluators |
| Production | `main` | production | Future |

See [ENV_MATRIX.md](ENV_MATRIX.md).

---

## Implementation roadmap (pipelines)

| Phase | Deliverable | Wave |
|-------|-------------|------|
| **P0** | `ci.yml` — pytest + npm build on PR | Wave 3 start ✅ scaffold |
| **P1** | Playwright + `wave-e2e.yml` + AST-01–03 | Wave 3 (NT-121) |
| **P2** | Postgres service container in CI | Wave 3 |
| **P3** | Coverage gate (≥ baseline) | Wave 4 |
| **P4** | `deploy-demo.yml` on tag → Render | After demo stable |
| **P5** | PR path filters + monorepo cache | Wave 5 hardening |

---

## Secrets (GitHub)

| Secret | Used by |
|--------|---------|
| `RENDER_DEPLOY_HOOK` | deploy-demo (optional) |
| `CODECOV_TOKEN` | coverage (future) |

No secrets required for P0 CI.

---

## Definition of Done (ticket)

- [ ] Acceptance criteria in GitHub Issue met  
- [ ] Unit/integration tests added (test IDs in PR)  
- [ ] `npm run build` pass if UI touched  
- [ ] Rex review approved  
- [ ] Tracker row updated in `WAVE{N}_TICKETS.md`  
- [ ] No P0/P1 bugs open on ticket  

## Definition of Done (wave)

- [ ] All wave tickets closed  
- [ ] `WAVE{N}_SIGNOFF.md` complete  
- [ ] E2E plan scenarios green or waived  
- [ ] Wave merge PR to `dev` approved by Abdullah  

---

## Related

- [WAVE3_E2E.md](WAVE3_E2E.md) — first E2E suite  
- [DEMO_RENDER_ONE_URL.md](DEMO_RENDER_ONE_URL.md) — demo CD target  
- `.github/workflows/ci.yml` — verify pipeline  
- `.github/workflows/wave-e2e.yml` — integrate pipeline  
