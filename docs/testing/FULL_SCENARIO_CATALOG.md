# Orbit — Full scenario catalog (multi-user)

**Purpose:** Real case scenarios with seed personas, handoffs, and corner cases.  
**Regression subset:** [REGRESSION_SUITE.md](./REGRESSION_SUITE.md)  
**Strategy:** [TEST_STRATEGY.md](../phase3-restructure/TEST_STRATEGY.md)

Password pattern: `{local-part}` + `SEED_PASSWORD_SUFFIX` (default `123`), e.g. `admin123`.

---

## 1. Personas

| ID | Email | Role | After login (home) | Primary powers |
|----|-------|------|--------------------|----------------|
| P-SUPER | super@demo.com | super_user | Platform area | Companies, packages, subscription, pilot reset |
| P-SWDEV | swdev@demo.com | sw_dev | Platform area | Platform tooling |
| P-ADMIN | admin@demo.com | company_admin | `/dashboard` | Clients, sites, assets, assign WO, approve, invoice, billing, users |
| P-CLIENT | client@demo.com | client_admin | `/dashboard` | Client-scoped assets/WO/invoices |
| P-CLIENT2 | client2@demo.com | client_admin | `/dashboard` | Second client (pilot) — isolation |
| P-SITE | site@demo.com | site_manager | `/work-orders` | Site-scoped assets/WO |
| P-TECH | tech@demo.com | technician | `/work-orders` | Assigned WO, report, scan |
| P-MGR | manager@demo.com | manager | `/work-orders` | Limited ops / labor (local seed) |

### Access matrix (chrome nav)

| Route | P-ADMIN | P-CLIENT | P-SITE | P-TECH | P-SUPER |
|-------|---------|----------|--------|--------|---------|
| `/dashboard` | Y | Y | Y* | Y* | via platform |
| `/companies` | Y | N | N | N | N† |
| `/assets` | Y | Y | Y | N‡ | — |
| `/assets/maintenance-calendar` | Y | Y | Y | N‡ | — |
| `/work-orders` | Y | Y | Y | Y | — |
| `/invoices` | Y | Y | N | N | — |
| `/billing/*` | Y | N | N | N | — |
| `/users` | Y | N | N | N | — |
| `/platform/*` | N | N | N | N | Y |
| `/scan` | Y | Y | Y | Y | — |

\* Field roles land on `/work-orders` from `/`.  
† Platform staff use platform company admin, not tenant Companies chrome.  
‡ Technician: assets feature may be denied by role even if subscription has `assets`.

---

## 2. Multi-actor journeys

### SC-GP-HOSP — Hospital path: onboard → maintain → invoice

- **Tags:** E2E | FULL (slice REG: see REGRESSION_SUITE)
- **Actors:** P-ADMIN → P-TECH → P-ADMIN
- **Preconditions:** Seed tenant with `assets` + `invoices`; at least one site (or create in steps).

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | P-ADMIN | Login | `/dashboard`; sidebar shows Clients, Assets, WO, Invoices |
| 2 | P-ADMIN | Open Companies → company detail → add site (if needed) | Site listed |
| 3 | P-ADMIN | Assets → Register asset (type + site) | Asset appears; label/QR available |
| 4 | P-ADMIN | Asset QR modal → Copy link | Feedback “Copied”; link contains `/a/` |
| 5 | P-ADMIN | Print label | PDF opens/downloads; QR present (not “QR unavailable”) |
| 6 | P-ADMIN | Create WO for asset → Assign P-TECH | Status assigned |
| 7 | P-TECH | Login | Lands `/work-orders`; no Companies/Billing in nav |
| 8 | P-TECH | Open WO → Start → fill report → Submit | Report submitted |
| 9 | P-ADMIN | Login → Approve report → Verify WO | Status verified |
| 10 | P-ADMIN | Generate invoice → open PDF | Invoice exists; PDF downloads |

**Corner cases**

- P-TECH cannot approve report or generate invoice.
- Complete without report → friendly `REPORT_REQUIRED` (no screaming snake).
- Hold without reason → blocked.
- Retired asset → cannot create new WO.

### SC-FIELD-DAY — Technician field day

- **Tags:** E2E | FULL
- **Actors:** P-ADMIN (setup) → P-TECH

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | P-ADMIN | Assign open WO to P-TECH | Assigned |
| 2 | P-TECH | Login → Queue shows WO | Visible in list |
| 3 | P-TECH | `/scan` or open camera / manual code | Resolves to asset or clear error |
| 4 | P-TECH | Start → On hold (reason) → Resume | Status transitions |
| 5 | P-TECH | Submit report | Cannot verify |

**Corner cases:** Unassigned WO not actionable by P-TECH; bad scan code → friendly not found.

### SC-SITE-MGR — Site manager scope

- **Tags:** E2E | FULL
- **Actors:** P-SITE, P-TECH

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | P-SITE | Login → home `/work-orders` | No Companies / Users / Billing |
| 2 | P-SITE | Assets + calendar for own site | Data scoped; no other clients |
| 3 | P-SITE | Open site detail if linked | Assets load via `/assets?site_id=` (not 404) |

### SC-CLIENT-VIEW — Client admin visibility

- **Tags:** REG | E2E
- **Actors:** P-CLIENT (+ P-CLIENT2 on pilot)

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | P-CLIENT | Login → Assets / WO / Invoices | Pages load in client scope |
| 2 | P-CLIENT | Open `/companies` | Denied or redirect (not full admin CRUD) |
| 3 | P-CLIENT2 | Login (pilot) | Cannot see P-CLIENT company assets |

### SC-PLATFORM — Platform staff

- **Tags:** E2E | FULL | MANUAL (heavy)
- **Actors:** P-SUPER

| Step | Actor | Action | Expected |
|------|-------|--------|----------|
| 1 | P-SUPER | Login | Platform nav (companies / packages / subscription) |
| 2 | P-SUPER | Open maintenance companies | List loads |
| 3 | P-SUPER | Open packages + subscription | Pages load |
| 4 | P-TECH | Open `/platform/packages` | Forbidden / redirect |

---

## 3. Domain scenarios (named actor)

### AUTH

| ID | Tags | Actor | Steps (summary) | Corners |
|----|------|-------|-----------------|---------|
| SC-AUTH-01 | REG E2E | P-ADMIN | Login → dashboard | — |
| SC-AUTH-02 | REG E2E | P-TECH | Login → `/work-orders` | Not dashboard |
| SC-AUTH-03 | REG E2E | — | Bad password on login | Friendly bilingual; no `INVALID_CREDENTIALS` raw |
| SC-AUTH-04 | E2E | P-ADMIN | Language toggle AR↔EN | Strings swap; RTL/LTR |
| SC-AUTH-05 | E2E | P-ADMIN | Logout → `/login`; deep link protected | Redirect to login |

### TEN / RBAC

| ID | Tags | Actor | Steps | Corners |
|----|------|-------|-------|---------|
| SC-TEN-01 | REG E2E | P-TECH | Visit `/companies`, `/billing/inventory` | Blocked |
| SC-TEN-02 | REG E2E | P-TECH | Nav has no Invoices/Clients | — |
| SC-TEN-03 | API E2E | P-CLIENT2 | Fetch other client asset | 403/empty |
| SC-TEN-04 | API MANUAL | gated tenant | Feature off | FeatureUnavailable copy |

### AST / CAL / QR

| ID | Tags | Actor | Steps | Corners |
|----|------|-------|-------|---------|
| SC-AST-01 | REG E2E | P-ADMIN | `/assets` loads; open Register | Modal |
| SC-AST-02 | REG E2E | P-ADMIN | Open `/assets/maintenance-calendar` | Year/month UI |
| SC-AST-03 | E2E | P-ADMIN | Finished preventive WO on calendar | Green + link to WO |
| SC-AST-04 | E2E | P-ADMIN | Retire asset | Out of service; no new WO |
| SC-QR-01 | E2E | P-ADMIN | QR modal print + copy | PDF has periapsis QR |
| SC-QR-02 | E2E MANUAL | anon | `/a/{token}` | Public landing / report |

### WO

| ID | Tags | Actor | Steps | Corners |
|----|------|-------|-------|---------|
| SC-WO-01 | API REG | — | FSM pytest suite | REPORT_REQUIRED, hold, assignee |
| SC-WO-02 | E2E | P-ADMIN→P-TECH | Assign → start → report | Multi-user |
| SC-WO-03 | E2E | P-ADMIN | Cancel with reason | Reason required |

### INV / BILL

| ID | Tags | Actor | Steps | Corners |
|----|------|-------|-------|---------|
| SC-INV-01 | REG E2E | P-ADMIN | `/invoices` heading visible | — |
| SC-INV-02 | E2E API | P-ADMIN | Preview/generate from verified WO | Gate off tenant |
| SC-BILL-01 | E2E | P-ADMIN | Commercial terms + inventory pages | P-TECH denied |

### USERS / TEMPLATES / MISC

| ID | Tags | Actor | Steps | Corners |
|----|------|-------|-------|---------|
| SC-USR-01 | E2E | P-ADMIN | `/users` loads | P-TECH denied |
| SC-TPL-01 | E2E | P-ADMIN | Report templates page | — |
| SC-I18N-01 | E2E | P-ADMIN | Switch language mid-session | Inactive locale lazy-loaded |
| SC-MOB-01 | MANUAL | P-TECH | Phone viewport bottom nav + More | — |

---

## 4. Mapping to legacy IDs

| Legacy | Catalog |
|--------|---------|
| GP-01..12 | SC-GP-HOSP |
| AST-01..06 | SC-AST-* / calendar on `/assets/maintenance-calendar` |
| INV-01..06 | SC-INV-* |
| WO-01..05 | SC-WO-* + API |
| ERR-LOGIN | SC-AUTH-03 |

Wave matrices under `docs/phase3-restructure/` remain historical; **this catalog is the product-wide source of truth**.
