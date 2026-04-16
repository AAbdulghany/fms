# Facility Management System (FMS) - Technical Specification Prompt
## Version 2.0 - Refined Scope

---

## ROLE

You are a senior full-stack software architect with 10+ years of experience in:
- Building multi-tenant SaaS applications
- Facility management and CMMS (Computerized Maintenance Management Systems)
- RESTful API-first architectures
- Bilingual UI applications (Arabic frontend, English backend)
- Report generation and billing systems

---

## CONTEXT

### Business Domain

A facility management company provides maintenance services for multiple clients. Each client can have multiple sites (buildings/facilities). The company handles both preventive (scheduled) and corrective (breakdown) maintenance, tracks work orders, and generates professional reports and invoices.

**Key Business Flow:**
```
Client Request → Work Order Created → Technician Assigned → 
→ Technician Fills Template Report → Manager Approves → 
→ PDF Report Generated → Invoice Created → Client Billed
```

### User Hierarchy
```
Company (Service Provider)
  └── Clients (multiple)
        └── Sites (multiple per client)
              └── Assets/Equipment (multiple per site)
                    └── Maintenance Records (history per asset)
```

### User Roles & Access Matrix

| Role | Platform | Scope | Key Capabilities |
|------|----------|-------|------------------|
| Super Admin | Web | System-wide | System config, tenant management, all access |
| Company Admin | Web | Company-wide | Manage clients, sites, users, templates, billing |
| Client Admin | Web | All client sites | View all sites, approve work, view invoices, download reports |
| Site Manager | Web | Single site | Manage site assets, create requests, view site reports |
| Technician | Web | Assigned work | Fill report templates, upload photos, complete tasks |
| Manager | Mobile | Company-wide | Approve workflows, monitor progress, receive alerts |

### Platform Strategy

| Platform | Primary Users | Purpose |
|----------|--------------|---------|
| **Web App** (Primary) | Admin, Clients, Technicians | Full functionality, data entry, reports |
| **Mobile App** (Secondary) | Managers | Workflow approvals, monitoring, push notifications |

---

## CORE MODULES

### Module 1: Maintenance Management (MVP Priority)

#### 1.1 Preventive Maintenance
- Schedule recurring maintenance (daily, weekly, monthly, yearly)
- Calendar view of upcoming maintenance
- Auto-generate work orders from schedules
- Asset-based maintenance plans

#### 1.2 Corrective Maintenance
- Client can submit breakdown requests
- Urgency levels: Normal, Urgent, Emergency
- Problem categorization (Electrical, Mechanical, HVAC, Plumbing, etc.)

#### 1.3 Work Order Lifecycle
```
┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌───────────┐
│ Created │───►│ Assigned │───►│ In Progress │───►│ Completed │
└─────────┘    └──────────┘    └─────────────┘    └───────────┘
      │              │               │                   │
      ▼              ▼               ▼                   ▼
 [Cancelled]   [Reassigned]     [On Hold]          [Verified]
                                                        │
                                                        ▼
                                                   [Closed] ──► Invoice Generated
```

#### 1.4 SLA Management
- Define SLA per client/contract
- Response time tracking
- Resolution time tracking
- Auto-escalation on SLA breach
- SLA compliance reports

---

### Module 2: Template-Based Reporting System (Key Feature)

#### 2.1 Report Templates
- Admin creates reusable report templates
- Template sections: Checklist items, text fields, photo uploads, measurements, signatures
- Templates assigned to maintenance types (e.g., "HVAC Inspection Template", "Fire Safety Checklist")

#### 2.2 Template Builder (Admin)
```
Template Components:
├── Header (auto-filled: date, technician, site, asset)
├── Checklist Section (pass/fail/NA items)
├── Measurement Fields (numeric with units)
├── Text Areas (observations, recommendations)
├── Photo Upload Slots (before/after, evidence)
├── Parts Used Section (links to inventory)
├── Labor Time Log
└── Signature Capture (technician + client rep)
```

#### 2.3 Technician Report Filling
- Mobile-friendly form interface
- Offline draft saving (sync when online)
- Photo capture with annotation
- Voice-to-text for notes (optional)
- Auto-save progress

#### 2.4 PDF Report Generation
- Professional branded PDF output
- Company logo + client logo
- Bilingual option (Arabic/English)
- Attached photos embedded
- Digital signatures included
- Downloadable + email to client

---

### Module 3: Asset Management

- Equipment registry (name, model, serial, location, install date)
- QR code generation for asset tagging
- Asset hierarchy (Building → Floor → Zone → Equipment)
- Maintenance history per asset
- Warranty tracking
- Spare parts association

---

### Module 4: Billing & Invoicing (Linked to Reports)

#### 4.1 Billing Sources (Auto-calculated from completed reports)
```
Invoice Line Items:
├── Labor: Hours logged × Hourly rate
├── Parts: Parts used × Unit cost (+ markup)
├── Service Fee: Fixed fee per maintenance type
└── Additional Charges: Travel, emergency surcharge, etc.
```

#### 4.2 Invoice Generation
- Auto-generate from completed & verified work orders
- Draft → Approved → Sent → Paid workflow
- PDF invoice with company branding
- Payment terms and due dates
- Invoice history per client

#### 4.3 Contract Management
- Client contracts with pricing agreements
- Retainer/subscription billing option
- Contract renewal alerts

---

### Module 5: Notification Center

| Event | Channels | Recipients |
|-------|----------|------------|
| New work order | Email, Push | Assigned technician |
| SLA warning (80% time elapsed) | Email, Push | Manager, Technician |
| SLA breach | Email, Push | Admin, Manager |
| Work completed | Email | Client, Manager |
| Report ready | Email + PDF attachment | Client |
| Invoice generated | Email + PDF attachment | Client |
| Payment overdue | Email | Client, Admin |

**Channels (Phase 1):**
- Email (SMTP integration)
- Push Notifications (Firebase Cloud Messaging)

---

### Module 6: Dashboards & Analytics

#### Admin Dashboard
- Open work orders by status
- SLA compliance rate
- Technician workload distribution
- Revenue this month
- Overdue invoices

#### Manager Dashboard (Mobile)
- Pending approvals count
- Today's scheduled maintenance
- Active work orders map view
- Quick approve/reject actions

#### Client Portal Dashboard
- My open requests
- Maintenance history
- Upcoming scheduled maintenance
- Invoice summary
- Download reports

---

## TECHNICAL REQUIREMENTS

### Architecture Principles
- **API-First**: All frontends consume the same REST API
- **Multi-Tenant**: Single database with row-level tenant isolation
- **Stateless Backend**: JWT authentication, horizontally scalable
- **Online-Only**: No offline sync complexity (drafts save to server)

### Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend** | Python FastAPI | Mandated, async support, auto-docs |
| **Database** | PostgreSQL | Mandated, JSONB for flexible templates |
| **Web Frontend** | React + TypeScript | Component ecosystem, RTL support |
| **Mobile App** | React Native | Code sharing with web, cross-platform |
| **UI Framework** | Tailwind CSS + shadcn/ui | Rapid development, RTL utilities |
| **PDF Generation** | WeasyPrint or ReportLab | Python-native, template-based |
| **File Storage** | S3-compatible (MinIO/AWS S3) | Scalable, CDN-ready |
| **Push Notifications** | Firebase Cloud Messaging | Free tier, reliable |
| **Email** | SMTP (SendGrid/AWS SES) | Transactional emails |
| **Auth** | JWT + OAuth2 | Stateless, refresh tokens |
| **Design Tool** | Pencil MCP | Wireframes and mockups |

### Language Strategy

| Layer | Language | Notes |
|-------|----------|-------|
| Database | English only | Column names, enums, stored data |
| API | English only | Endpoints, JSON keys, error codes |
| Backend Code | English only | Variables, comments, logs |
| Web UI | Arabic (primary) + English toggle | RTL layout, translated labels |
| Mobile UI | Arabic (primary) + English toggle | Same translation files |
| Reports/PDFs | Bilingual option | User selects language |

### Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Concurrent Users | 50-200 |
| API Response Time | < 500ms (p95) |
| Uptime | 99.5% |
| Data Retention | 7 years |
| File Upload Limit | 10MB per file, 50MB per report |
| Supported Browsers | Chrome, Safari, Edge (latest 2 versions) |

---

## TASK

Design and document the complete system. Provide:

### Deliverable 1: System Architecture
- High-level architecture diagram (Mermaid)
- Component responsibilities
- Data flow for key processes (work order lifecycle, report→invoice flow)

### Deliverable 2: Database Schema
- ERD diagram
- Multi-tenancy approach (row-level security with tenant_id)
- Core tables: tenants, users, clients, sites, assets, work_orders, templates, reports, invoices
- Audit logging strategy

### Deliverable 3: API Design
- Authentication flow (login, refresh, logout)
- RESTful endpoint structure by module
- Key endpoints with request/response examples
- File upload handling
- Pagination and filtering patterns

### Deliverable 4: Template System Design
- Template schema (JSONB structure for dynamic fields)
- Template builder UI flow
- Report filling flow
- PDF generation pipeline

### Deliverable 5: Billing Integration Design
- How completed reports feed into invoices
- Pricing rules engine
- Invoice calculation logic
- Payment status tracking

### Deliverable 6: UI/UX Specifications
- Design system (colors, typography, spacing)
- Key screen wireframes (web)
- Mobile app screens (manager approval flow)
- RTL layout guidelines
- Component library recommendations

### Deliverable 7: Implementation Roadmap
- Phase 1 (MVP): Core maintenance + templates + basic billing
- Phase 2: Full billing + client portal
- Phase 3: Mobile app + advanced analytics
- Timeline estimates per phase

---

## CONSTRAINTS

### Must Have
- [ ] API-first (no direct DB access from frontends)
- [ ] Multi-tenant with strict data isolation
- [ ] Arabic UI with proper RTL support
- [ ] Template-based report system
- [ ] Report-to-invoice linkage
- [ ] Role-based access control (RBAC)
- [ ] Audit trail for work orders and invoices
- [ ] PDF generation for reports and invoices

### Must NOT Have
- [ ] No offline-first architecture (online required)
- [ ] No WhatsApp integration (future consideration)
- [ ] No desktop app (web is responsive)
- [ ] No Arabic in database/API (English only backend)
- [ ] No hardcoded pricing (configurable)

### Assumptions
- Users have stable internet connectivity
- Company provides SMTP credentials for email
- Cloud hosting on AWS/GCP (region: Middle East)
- Single currency (SAR) for MVP, multi-currency later

### If Uncertain
- State your assumption clearly
- Flag technical risks with severity level
- Propose 2-3 alternatives where applicable

---

## OUTPUT FORMAT

```markdown
# 1. Executive Summary
Brief overview of the solution (200 words max)

# 2. System Architecture
## 2.1 Architecture Diagram
## 2.2 Component Breakdown
## 2.3 Key Data Flows

# 3. Database Design
## 3.1 Multi-Tenancy Approach
## 3.2 ERD Diagram
## 3.3 Core Tables (with columns)
## 3.4 Template Storage Schema (JSONB structure)

# 4. API Specification
## 4.1 Authentication
## 4.2 Endpoints by Module
## 4.3 Sample Requests/Responses

# 5. Template & Report System
## 5.1 Template Schema Design
## 5.2 Report Filling Flow
## 5.3 PDF Generation Pipeline

# 6. Billing System
## 6.1 Pricing Configuration
## 6.2 Report-to-Invoice Flow
## 6.3 Invoice Lifecycle

# 7. UI/UX Guidelines
## 7.1 Design Tokens
## 7.2 Key Screens (wireframe descriptions)
## 7.3 RTL Implementation Notes

# 8. Implementation Roadmap
## 8.1 Phase 1: MVP (8-10 weeks)
## 8.2 Phase 2: Full Features (6-8 weeks)
## 8.3 Phase 3: Mobile + Analytics (6-8 weeks)

# 9. Risks & Mitigations
| Risk | Impact | Mitigation |

# 10. Open Questions
List items needing clarification
```

---

## EXAMPLES

### Example: Template Schema (JSONB)
```json
{
  "template_id": "tpl_hvac_inspection",
  "name": "HVAC Inspection Checklist",
  "version": 2,
  "sections": [
    {
      "id": "sec_1",
      "title": "Visual Inspection",
      "fields": [
        {
          "id": "fld_1",
          "type": "checklist",
          "label": "Filters clean",
          "options": ["Pass", "Fail", "N/A"],
          "required": true
        },
        {
          "id": "fld_2",
          "type": "photo",
          "label": "Filter condition photo",
          "max_photos": 2,
          "required": false
        }
      ]
    },
    {
      "id": "sec_2",
      "title": "Measurements",
      "fields": [
        {
          "id": "fld_3",
          "type": "number",
          "label": "Supply air temperature",
          "unit": "°C",
          "min": 10,
          "max": 35,
          "required": true
        }
      ]
    }
  ]
}
```

### Example: Report-to-Invoice Flow
```
1. Technician completes work order #WO-2025-0042
2. Technician fills "HVAC Inspection" template
   - Labor: 2.5 hours
   - Parts used: 2x Air Filter (SKU: FLT-001)
3. Manager approves report
4. System auto-calculates:
   - Labor: 2.5 hrs × 150 SAR/hr = 375 SAR
   - Parts: 2 × 45 SAR × 1.2 markup = 108 SAR
   - Service fee: 200 SAR (from contract)
   - Total: 683 SAR
5. Invoice #INV-2025-0018 created (draft)
6. Admin reviews and approves
7. Invoice PDF generated and emailed to client
```

### Example: API Endpoint Pattern
```
# Work Orders
GET    /api/v1/work-orders                    # List (filterable)
POST   /api/v1/work-orders                    # Create
GET    /api/v1/work-orders/{id}               # Get details
PATCH  /api/v1/work-orders/{id}               # Update
POST   /api/v1/work-orders/{id}/assign        # Assign technician
POST   /api/v1/work-orders/{id}/complete      # Mark complete

# Reports
GET    /api/v1/work-orders/{id}/report        # Get filled report
POST   /api/v1/work-orders/{id}/report        # Submit report
GET    /api/v1/work-orders/{id}/report/pdf    # Download PDF

# Invoices  
POST   /api/v1/work-orders/{id}/generate-invoice  # Create from WO
GET    /api/v1/invoices/{id}/pdf              # Download invoice PDF
```

---

## VERIFICATION CHECKLIST

Before finalizing, verify:
- [ ] All 7 deliverables are complete
- [ ] Template system supports dynamic fields
- [ ] Report-to-invoice automation is clear
- [ ] RBAC covers all 6 user roles
- [ ] Arabic RTL UI is addressed
- [ ] API supports all required operations
- [ ] PDF generation approach is defined
- [ ] Mobile app scope is limited to manager workflows
