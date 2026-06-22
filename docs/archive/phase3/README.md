# Phase 3 Documentation

**Sprint:** Phase 3 - Complete Core Functionality  
**Date:** April 18, 2026  
**Status:** 🟡 Ready to Start

---

## Overview

Phase 3 completes the FMS core functionality by implementing missing company creation and asset registration features, adding real-time notifications (WebSocket + Email), enhancing work order tracking, and supporting multi-currency invoices (EGP, SAR, USD, EUR).

---

## Documentation Structure

### 📋 [PHASE3_PLAN.md](PHASE3_PLAN.md)
**Main Sprint Plan** - Start here for overview

- Executive summary
- Sprint goals
- Feature specifications (F1-F4)
- Testing tasks (T1-T4)
- Execution sequence
- Success metrics
- Risk assessment

---

### 🔧 [prompt_backend.md](prompt_backend.md)
**Backend Engineer Instructions**

**Agent:** Senior Backend Engineer  
**Tasks:**
- P3-F2-BE: Asset registration endpoint
- P3-F3-BE: Work order creator/assignee response enhancement
- P3-F4-BE: Multi-currency invoice support
- P3-T3-BE: WebSocket notification endpoint
- P3-T3-BE: Email notification service

**Framework:** RCCF (Role-Context-Constraints-Format)  
**Key Focus:** FastAPI, SQLAlchemy, WebSocket, SendGrid, tenant isolation

---

### 🎨 [prompt_frontend.md](prompt_frontend.md)
**Frontend Engineer Instructions**

**Agent:** Senior Frontend Engineer  
**Tasks:**
- P3-F1-FE: ClockWidget component
- P3-F2-FE: Company creation + Asset registration forms
- P3-F3-FE: Creator/Assignee display in WO detail
- P3-F4-FE: Currency selector + formatCurrency utility
- P3-T3-FE: NotificationProvider + NotificationBell + Toast UI

**Framework:** RCCF (Role-Context-Constraints-Format)  
**Key Focus:** React, TypeScript, i18n (AR/EN), RTL support, WebSocket client

---

### 🎨 [prompt_uiux.md](prompt_uiux.md)
**UI/UX Designer Instructions**

**Agent:** Senior UI/UX Designer  
**Tasks:**
- P3-F2-UX: Company creation + Asset registration wireframes
- P3-T3-UX: Notification bell + dropdown design
- P3-T4-UX: Invoice print layout refinement (multi-currency)

**Framework:** RCCF (Role-Context-Constraints-Format)  
**Key Focus:** Arabic-first RTL design, accessibility (WCAG 2.1 AA), responsive design

---

### 🧪 [prompt_qa.md](prompt_qa.md)
**QA Engineer Instructions**

**Agent:** Senior QA Engineer  
**Tasks:**
- P3-T1: Full user lifecycle testing (all 6 roles)
- P3-T2: Multi-browser notification testing
- P3-T3: Notification delivery verification (WebSocket + Email)
- P3-T4: Invoice print layout verification (4 currencies)

**Framework:** Test scenarios with expected/actual results  
**Key Focus:** RBAC validation, tenant isolation, regression testing

---

### 📊 [prompt_pm.md](prompt_pm.md)
**Project Manager Instructions**

**Agent:** Project Manager  
**Responsibilities:**
- Sprint planning and task breakdown
- Progress tracking and status reporting
- Risk management and mitigation
- Quality gate enforcement
- Agent coordination

**Framework:** Coordination checklist, status reports, decision log  
**Key Focus:** On-time delivery, zero regressions, quality assurance

---

## Quick Start

### For Agents

1. **Read the overview:** [PHASE3_PLAN.md](PHASE3_PLAN.md)
2. **Read your role-specific prompt:**
   - Backend: [prompt_backend.md](prompt_backend.md)
   - Frontend: [prompt_frontend.md](prompt_frontend.md)
   - UI/UX: [prompt_uiux.md](prompt_uiux.md)
   - QA: [prompt_qa.md](prompt_qa.md)
   - PM: [prompt_pm.md](prompt_pm.md)
3. **Start with your first task** (check task breakdown section)
4. **Report progress** in standard output format

### For Stakeholders

- **Sprint Overview:** Read [PHASE3_PLAN.md](PHASE3_PLAN.md) Executive Summary
- **Progress Updates:** Check with PM for weekly status reports
- **Feature Details:** See individual feature specs in [PHASE3_PLAN.md](PHASE3_PLAN.md)

---

## Phase 3 Features Summary

| ID | Feature | Priority | Status |
|----|---------|----------|--------|
| P3-F1 | Clock/Date in Header | Low | Pending |
| P3-F2 | Create Company + Register Asset | High | Pending |
| P3-F3 | Work Order Creator/Assignee Display | Medium | Pending |
| P3-F4 | Multi-Currency Invoices (EGP, SAR, USD, EUR) | Medium | Pending |

## Phase 3 Testing Tasks

| ID | Test Scenario | Priority | Status |
|----|---------------|----------|--------|
| P3-T1 | Full User Lifecycle Testing (6 roles) | Critical | Pending |
| P3-T2 | Multi-browser Notification Testing | High | Pending |
| P3-T3 | Real-time Notifications (WebSocket + Email) | High | Pending |
| P3-T4 | Invoice Print Layout Verification | Medium | Pending |

---

## Execution Sequence

```
P3-F1 (Clock)
  ↓
P3-F2 (Company/Asset)
  ↓
P3-F3 (Creator/Assignee)
  ↓
P3-F4 (Multi-Currency) ──┐
  ↓                       ├── (Parallel)
P3-T3 (Notifications) ────┘
  ↓
P3-T1 (Lifecycle Tests)
  ↓
P3-T2 (Multi-browser) ──┐
  ↓                      ├── (Parallel)
P3-T4 (Invoice Print) ───┘
  ↓
✅ Phase 3 Complete
```

---

## Key Deliverables

**Backend:**
- POST /assets endpoint
- Enhanced work order response (creator/assignee)
- Currency enum + migration
- WebSocket notification endpoint
- Email notification service

**Frontend:**
- ClockWidget component
- Company/Asset creation modals
- Creator/Assignee display
- CurrencySelector component
- NotificationProvider + Bell + Toast

**UI/UX:**
- Wireframes for forms
- Notification bell design
- Invoice print layout

**QA:**
- User lifecycle test results (6 roles)
- Multi-browser notification test results
- Invoice print verification (4 currencies)
- Zero RBAC/tenant isolation regressions

---

## Success Criteria

Phase 3 is complete when:

1. ✅ All 4 features implemented and tested
2. ✅ Super User can complete full lifecycle (create company → create WO → close)
3. ✅ Notifications delivered within 2 seconds
4. ✅ Invoice prints correctly in all 4 currencies
5. ✅ Zero RBAC/tenant isolation regressions
6. ✅ All 76 Phase 2 tests still pass
7. ✅ Documentation complete

---

## Reference Documentation

### Phase 2 (Completed)
- **[Phase 2 Complete](../phase2/PHASE2_COMPLETE.md)** - Phase 2 summary
- **[RBAC Matrix](../phase2/RBAC_Matrix.md)** - Role permission matrix
- **[QA Quick Start](../phase2/QA_Quick_Start_Guide.md)** - Testing guide
- **[UI/UX Summary](../phase2/UI_UX_Phase2_Summary.md)** - Design specs

### Agent Skills
- **Backend:** `.claude/skills/senior-backend.md`
- **Frontend:** `.claude/skills/senior-frontend.md`
- **UI/UX:** `.claude/skills/senior-uiux.md`
- **QA:** `.claude/skills/senior-qa.md`
- **PM:** `.claude/skills/pm.md`

### Project Setup
- **[USER_GUIDE.md](../USER_GUIDE.md)** - Setup and usage
- **[CLAUDE.md](../../CLAUDE.md)** - Codebase architecture

---

## Prompt Engineering Framework

All agent prompts follow the **RCCF Framework** (from prompt engineering best practices):

1. **Role:** Clear agent identity and expertise
2. **Context:** Project background, current state, goals
3. **Constraints:** Technical requirements, security, quality standards
4. **Format:** Expected output structure, deliverables, verification checklist

This ensures consistent, high-quality outputs across all agents.

---

## Contact & Coordination

- **PM Agent:** Coordinates all agents, tracks progress
- **Daily Updates:** Agents report progress in standard format
- **Weekly Reviews:** Sprint progress, risks, quality metrics
- **Escalation:** Critical blockers → PM → Tech Lead

---

**Last Updated:** April 18, 2026  
**Version:** 3.0  
**Status:** 🟡 Ready to Start
