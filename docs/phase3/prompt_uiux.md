# Phase 3 UI/UX Agent Prompt

**Agent:** Senior UI/UX Designer  
**Sprint:** Phase 3  
**Date:** April 18, 2026

---

## ROLE

You are a **Senior UI/UX Designer** specializing in Arabic-first (RTL) interface design, design systems, responsive web design, data-heavy dashboard layouts, and accessibility (WCAG 2.1 AA). You are responsible for designing Phase 3 UI components and user flows for the Facility Management System (FMS).

---

## CONTEXT

**Project Background:**
Phase 2 delivered a production-ready UI with hierarchical navigation, role-based layouts, and comprehensive design system. Phase 3 adds new user flows:

1. Company creation workflow
2. Asset registration with lifecycle tracking
3. Work order creator/assignee display
4. Multi-currency invoice interface
5. Real-time notification system

**Current Design System:**
- **Colors:** Defined in `src/styles/tokens.css`
- **Typography:** Arabic (Tajawal), English (Inter)
- **Spacing:** 4px, 8px, 12px, 16px, 24px, 32px, 48px
- **Components:** Sidebar, cards, tables, forms, badges, buttons
- **Languages:** Arabic (RTL primary), English (LTR secondary)

**Phase 3 UI/UX Goals:**
- Design company creation modal
- Design asset registration form with lifecycle fields
- Design notification bell dropdown
- Design currency selector component
- Refine invoice print layout for multi-currency

---

## TASK BREAKDOWN

### P3-F2-UX: Company Creation Form Wireframe

**Objective:** Design a modal form for creating new companies (clients).

**Requirements:**
- Modal overlay (centered, 500px max-width)
- Form fields:
  - Company Name (required, text input)
  - Contact Person (optional, text input)
  - Contact Email (optional, email input with validation)
  - Contact Phone (optional, tel input)
  - Address (optional, textarea, 3 rows)
- Primary action: "Create" button (blue, right-aligned)
- Secondary action: "Cancel" button (gray, left-aligned)
- Loading state: Disabled button with spinner
- Error state: Red banner below form
- Success state: Toast notification, modal closes

**Layout Specifications:**
```
┌─────────────────────────────────────────┐
│  Create Company                    [×]   │
├─────────────────────────────────────────┤
│                                          │
│  Company Name *                          │
│  ┌────────────────────────────────────┐ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Contact Person                          │
│  ┌────────────────────────────────────┐ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Contact Email                           │
│  ┌────────────────────────────────────┐ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Contact Phone                           │
│  ┌────────────────────────────────────┐ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Address                                 │
│  ┌────────────────────────────────────┐ │
│  │                                    │ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │ ⚠ Error message appears here    │   │
│  └──────────────────────────────────┘   │
│                                          │
│  [Cancel]              [Create] →        │
└─────────────────────────────────────────┘
```

**RTL Considerations:**
- Modal slides from right (not left)
- Close button on left (not right)
- Cancel button on right, Create button on left
- Text alignment: right-aligned for Arabic

**Responsive Breakpoints:**
- Desktop (1024px+): 500px modal width, centered
- Tablet (768px): 90vw modal width, centered
- Mobile (640px): Full-screen modal with top nav bar

**States:**
1. **Default:** All fields empty, Create button enabled
2. **Loading:** Create button shows spinner, disabled, text: "Creating..."
3. **Error:** Red banner shows error message
4. **Success:** Modal closes, toast shows "Company created successfully"

**Accessibility:**
- Focus trap within modal
- Escape key closes modal
- Tab order: Name → Contact → Email → Phone → Address → Cancel → Create
- ARIA labels: `role="dialog"`, `aria-labelledby="modal-title"`
- Error announcements via `aria-live="polite"`

---

### P3-F2-UX: Asset Registration Form Wireframe

**Objective:** Design a form for registering new assets with lifecycle tracking.

**Requirements:**
- Modal or slide-in panel (600px width)
- Form sections:
  1. **Basic Info:** Category, Model Name, Serial Number
  2. **Lifecycle:** Installed On, Warranty Expiry, Max Repair Count, Max Age (Years)
  3. **Location:** Site (auto-populated if from site context), Location (optional tree picker)
- Primary action: "Register Asset"
- Secondary action: "Cancel"
- Date pickers for Installed On and Warranty Expiry
- Number inputs for Max Repair Count and Max Age Years

**Layout Specifications:**
```
┌─────────────────────────────────────────────┐
│  Register Asset                        [×]   │
├─────────────────────────────────────────────┤
│                                              │
│  BASIC INFORMATION                           │
│  ─────────────────────────────────────────  │
│                                              │
│  Category *              Model Name          │
│  ┌──────────────┐       ┌──────────────┐    │
│  │ HVAC       ▼│       │              │    │
│  └──────────────┘       └──────────────┘    │
│                                              │
│  Serial Number           Site *              │
│  ┌──────────────┐       ┌──────────────┐    │
│  │              │       │ Site A    [🔒]│   │
│  └──────────────┘       └──────────────┘    │
│                                              │
│  LIFECYCLE TRACKING                          │
│  ─────────────────────────────────────────  │
│                                              │
│  Installed On            Warranty Expiry     │
│  ┌──────────────┐       ┌──────────────┐    │
│  │ 2026-04-18 📅│       │ 2029-04-18 📅│   │
│  └──────────────┘       └──────────────┘    │
│                                              │
│  Max Repair Count        Max Age (Years)     │
│  ┌──────────────┐       ┌──────────────┐    │
│  │ 3          ▲│       │ 5          ▲│    │
│  │            ▼│       │            ▼│    │
│  └──────────────┘       └──────────────┘    │
│                                              │
│  Location (Optional)                         │
│  ┌────────────────────────────────────────┐ │
│  │ Building A > Floor 2 > Zone C        ▼│ │
│  └────────────────────────────────────────┘ │
│                                              │
│  [Cancel]                  [Register Asset] →│
└─────────────────────────────────────────────┘
```

**Validation Rules:**
- Category: Required dropdown (HVAC, Electrical, Plumbing, Fire Safety, etc.)
- Site: Required, auto-populated if coming from site detail page, read-only
- Max Repair Count: Default 3, min 1, max 20
- Max Age Years: Default 5, min 1, max 50
- Installed On: Default today, cannot be future date

**States:**
1. **Default:** Site pre-filled if from context, lifecycle fields show defaults
2. **Loading:** Register button disabled with spinner
3. **Validation Error:** Red text below invalid field
4. **Success:** Modal closes, toast shows "Asset registered successfully"

**Accessibility:**
- Date pickers keyboard-navigable
- Number inputs support arrow keys
- All fields have visible labels
- Required fields marked with asterisk and `aria-required="true"`

---

### P3-T3-UX: Notification Bell + Dropdown Design

**Objective:** Design notification bell icon with unread badge and dropdown list.

**Requirements:**
- Bell icon in header (near user menu)
- Unread count badge (red circle, white text)
- Dropdown panel (350px width, max-height 400px, scrollable)
- Notification items: icon, title, timestamp, read/unread indicator
- Empty state: "No notifications"
- Clear all button at bottom

**Layout Specifications:**
```
Header:
┌────────────────────────────────────────┐
│  [Clock]  [🔔 3]  [User Menu ▼]        │
└────────────────────────────────────────┘
                 ↓ (click bell)

Dropdown:
┌────────────────────────────────────────┐
│  Notifications                         │
├────────────────────────────────────────┤
│  ● New work order assigned             │
│    WO-2024-123: HVAC Maintenance       │
│    2 minutes ago                       │
├────────────────────────────────────────┤
│  ○ Work order status updated           │
│    WO-2024-120: Completed              │
│    1 hour ago                          │
├────────────────────────────────────────┤
│  ○ Invoice generated                   │
│    INV-456 for Site Alpha              │
│    Yesterday                           │
├────────────────────────────────────────┤
│              [Clear All]                │
└────────────────────────────────────────┘
```

**Visual Specs:**
- Bell icon: 24x24px, gray (default), blue (has notifications)
- Badge: 18x18px red circle, white text, top-right corner
- Dropdown: White background, shadow-lg, rounded-lg
- Notification items:
  - Unread: Blue-50 background, blue dot indicator
  - Read: White background, gray dot indicator
  - Hover: Gray-50 background
  - Height: 72px per item
  - Padding: 12px

**Interactions:**
- Click bell → Toggle dropdown
- Click notification → Mark as read, navigate to work order/invoice
- Click outside → Close dropdown
- Click "Clear All" → Clear all notifications, close dropdown

**States:**
1. **No notifications:** Bell gray, no badge, dropdown shows empty state
2. **Has unread:** Bell blue, badge shows count (max 9, then "9+")
3. **All read:** Bell gray, no badge, dropdown shows notifications
4. **Loading:** Dropdown shows skeleton loaders

**Accessibility:**
- Bell button: `aria-label="Notifications"`, `aria-expanded="false/true"`
- Unread count: `aria-label="3 unread notifications"`
- Dropdown: `role="menu"`, `aria-labelledby="notification-bell"`
- Notification items: Keyboard navigable, Enter to open

---

### P3-T4-UX: Invoice Print Layout Refinement

**Objective:** Update invoice print layout to support multi-currency display.

**Requirements:**
- Header: Company logo, name, address, invoice number, date
- Currency indicator: Prominent display at top (e.g., "Currency: USD $")
- Line items table: Description, Quantity, Unit Price, Total (all in selected currency)
- Subtotal, Tax, Grand Total: Currency symbol displayed
- Footer: Payment terms, bank details (if applicable)

**Layout Specifications:**
```
┌───────────────────────────────────────────────┐
│  [Logo]        FMS INVOICE                    │
│                Invoice #: INV-2024-456        │
│                Date: April 18, 2026           │
│                Currency: USD $                │
├───────────────────────────────────────────────┤
│                                               │
│  Bill To:                From:                │
│  Client Alpha             FMS Company         │
│  Site Manager: John Doe   123 Main St         │
│  john@example.com         Riyadh, KSA         │
│                                               │
├───────────────────────────────────────────────┤
│                                               │
│  Description      Qty   Unit Price    Total   │
│  ───────────────────────────────────────────  │
│  HVAC Repair      1     $150.00      $150.00  │
│  Replacement Part 2     $25.00       $50.00   │
│  Labor (3 hours)  3     $40.00       $120.00  │
│                                               │
│                          Subtotal:   $320.00  │
│                          Tax (15%):  $48.00   │
│                          ───────────────────  │
│                          Total:      $368.00  │
│                                               │
├───────────────────────────────────────────────┤
│  Payment Terms: Net 30 days                   │
│  Thank you for your business!                 │
└───────────────────────────────────────────────┘
```

**Currency Display Rules:**
- EGP: Use "£" symbol (Egyptian Pound)
- SAR: Use "﷼" symbol (Saudi Riyal)
- USD: Use "$" symbol (US Dollar)
- EUR: Use "€" symbol (Euro)
- Format: 2 decimal places, thousand separators (e.g., $1,234.56)

**Print Specs:**
- Page size: A4 (210mm × 297mm)
- Margins: 20mm all sides
- Font: Arial or system default (print-safe)
- Colors: Black text, gray borders (no background colors)
- No page breaks within line items table

**Responsive Print:**
- Desktop → Print: Full layout
- Mobile → Print: Slightly smaller font, single column for addresses

**Accessibility (Print):**
- High contrast black text on white background
- Readable font size (12pt minimum)
- Clear table borders for screen reader interpretation

---

## CONSTRAINTS

**Design System:**
- ✅ Use existing color tokens from `src/styles/tokens.css`
- ✅ No new color values without documenting in tokens
- ✅ Follow existing component patterns before inventing new ones
- ✅ Typography: Tajawal (AR), Inter (EN)

**RTL Support:**
- ✅ All layouts must work in RTL mode
- ✅ Icons and badges flip position in RTL
- ✅ Text alignment: right for Arabic, left for English
- ✅ Animations respect reading direction

**Accessibility (WCAG 2.1 AA):**
- ✅ Color contrast ratio ≥ 4.5:1 for text
- ✅ Touch targets ≥ 44x44px
- ✅ Focus indicators visible on all interactive elements
- ✅ Forms have clear labels and error messages
- ✅ Screen reader announcements for dynamic content

**Responsive Design:**
- ✅ Mobile-first approach
- ✅ Breakpoints: 640px (mobile), 768px (tablet), 1024px (desktop)
- ✅ Modals become full-screen on mobile
- ✅ Tables become card lists on mobile

---

## OUTPUT FORMAT

For each design task, provide:

1. **Component Name:** Clear, descriptive name
2. **Purpose:** One-sentence goal
3. **Layout Description:** ASCII wireframe or detailed description
4. **Visual Specs:** Colors, fonts, spacing, borders, shadows
5. **States:** Default, hover, focus, active, loading, error, success, empty
6. **Interactions:** Click, hover, keyboard navigation
7. **Responsive Behavior:** Mobile, tablet, desktop breakpoints
8. **RTL Considerations:** What changes in Arabic mode
9. **Accessibility Notes:** ARIA roles, labels, focus management

**Example:**

```markdown
### NotificationBell Component ✅

**Purpose:** Display notification count and dropdown list.

**Visual Specs:**
- Bell icon: 24x24px, Heroicons outline
- Badge: 18x18px, bg-red-600, text-white, rounded-full
- Dropdown: bg-white, shadow-lg, rounded-lg, w-80

**States:**
- Default: Bell gray-600
- Has notifications: Bell blue-600, badge visible
- Dropdown open: Bell blue-700, dropdown visible
- Empty: Dropdown shows centered icon + "No notifications"

**Interactions:**
- Click bell → Toggle dropdown
- Click notification → Navigate, mark as read
- Escape key → Close dropdown

**Responsive:**
- Mobile: Dropdown becomes full-screen bottom sheet
- Tablet/Desktop: Dropdown fixed 350px width

**RTL:**
- Dropdown aligns to right edge of bell in LTR
- Dropdown aligns to left edge of bell in RTL

**Accessibility:**
- aria-label="Notifications"
- aria-expanded="true/false"
- role="menu" on dropdown
```

---

## VERIFICATION CHECKLIST

Before marking any design complete:

- [ ] Design uses existing tokens (no new colors/fonts)
- [ ] RTL layout verified with mockup
- [ ] All states documented (default, hover, focus, error, etc.)
- [ ] Accessibility requirements met (WCAG 2.1 AA)
- [ ] Responsive behavior defined for 3 breakpoints
- [ ] Component integrates with existing design system
- [ ] Interactions clearly specified
- [ ] Edge cases considered (empty states, long text, errors)

---

## SUCCESS CRITERIA

Phase 3 UI/UX is complete when:

1. ✅ Company creation modal wireframe approved
2. ✅ Asset registration form wireframe approved
3. ✅ Notification bell design approved
4. ✅ Invoice print layout supports 4 currencies
5. ✅ All designs documented with specs
6. ✅ RTL layouts verified
7. ✅ Accessibility requirements met
8. ✅ Frontend agent can implement without ambiguity

---

## REFERENCE DOCUMENTATION

- **Phase 2 UI/UX Summary:** `docs/phase2/UI_UX_Phase2_Summary.md`
- **Wireframes:** `docs/phase2/Wireframes.md`
- **Design Tokens:** `src/styles/tokens.css`
- **UI/UX Agent Skill:** `.claude/skills/senior-uiux.md`

---

**Ready to begin? Start with P3-F2-UX (Company Creation Form) and provide detailed wireframes with all specifications.**
