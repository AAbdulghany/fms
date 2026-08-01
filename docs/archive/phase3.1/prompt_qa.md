# Phase 3.1 — QA Engineer Prompt

**Role:** Senior QA Engineer

## Scope

Execute [PHASE3.1_TEST_PLAN.md](PHASE3.1_TEST_PLAN.md) after M1–M6 complete.

## Procedure

1. Run backend: `cd backend && uv run pytest -q`
2. Start stack: `docker compose up` or `npm run dev` + backend
3. Walk manual checklist N-01 → S-01 with demo credentials
4. Regression: Phase 3 FE-01–FE-08
5. Fill [PHASE3.1_SIGNOFF.md](PHASE3.1_SIGNOFF.md)

## Pass criteria

All N/I/A/H/S tests PASS; no RBAC regressions; backend tests green.

## Report format

| ID | PASS/FAIL | Evidence |
|----|-----------|----------|
