# Accessibility Guidelines — FMS Phase 2

**Version:** 1.0  
**Date:** 2026-04-17  
**Standard:** WCAG 2.1 AA Compliance  
**Status:** Living Document

This document defines accessibility (a11y) standards and guidelines for the FMS project to ensure all users, including those with disabilities, can effectively use the application.

---

## Table of Contents

1. [ARIA Labels and Roles](#1-aria-labels-and-roles)
2. [Keyboard Navigation](#2-keyboard-navigation)
3. [Screen Reader Compatibility](#3-screen-reader-compatibility)
4. [Color Contrast Requirements](#4-color-contrast-requirements)
5. [Focus Management](#5-focus-management)
6. [Form Accessibility](#6-form-accessibility)
7. [Interactive Elements](#7-interactive-elements)
8. [Testing and Validation](#8-testing-and-validation)

---

## 1. ARIA Labels and Roles

### Overview

ARIA (Accessible Rich Internet Applications) attributes provide semantic information to assistive technologies when native HTML semantics are insufficient.

### ARIA Roles

**Navigation:**
```tsx
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/companies">Companies</a></li>
  </ul>
</nav>

<nav aria-label="Breadcrumb navigation">
  <ol>
    <li><a href="/">Home</a></li>
    <li aria-current="page">Current Page</li>
  </ol>
</nav>
```

**Landmarks:**
```tsx
<header role="banner">
  {/* Site header */}
</header>

<main role="main">
  {/* Main content */}
</main>

<aside role="complementary">
  {/* Sidebar */}
</aside>

<footer role="contentinfo">
  {/* Site footer */}
</footer>
```

**Dialogs:**
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">Dialog Title</h2>
  <p id="dialog-description">Dialog description</p>
  {/* Dialog content */}
</div>
```

**Tabs:**
```tsx
<div role="tablist" aria-label="Site information">
  <button
    role="tab"
    aria-selected="true"
    aria-controls="tab-panel-1"
    id="tab-1"
  >
    Details
  </button>
  <button
    role="tab"
    aria-selected="false"
    aria-controls="tab-panel-2"
    id="tab-2"
  >
    History
  </button>
</div>

<div
  role="tabpanel"
  id="tab-panel-1"
  aria-labelledby="tab-1"
  tabIndex={0}
>
  {/* Tab content */}
</div>
```

**Tables:**
```tsx
{/* Semantic table (preferred) */}
<table role="table" aria-label="Work orders list">
  <thead>
    <tr>
      <th scope="col">Title</th>
      <th scope="col">Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Work Order 1</td>
      <td>Completed</td>
    </tr>
  </tbody>
</table>
```

### ARIA Labels

**Buttons without visible text:**
```tsx
<button aria-label="Close dialog">
  <XIcon className="w-5 h-5" />
</button>

<button aria-label="Edit company ABC Facilities">
  <EditIcon className="w-5 h-5" />
</button>

<button aria-label="Delete work order WO-001">
  <TrashIcon className="w-5 h-5" />
</button>
```

**Links with non-descriptive text:**
```tsx
{/* ❌ Bad: Non-descriptive */}
<a href="/work-orders/123">Click here</a>

{/* ✅ Good: Descriptive */}
<a href="/work-orders/123">View work order WO-001</a>

{/* ✅ Good: aria-label for context */}
<a href="/work-orders/123" aria-label="View details for work order WO-001">
  View Details
</a>
```

**Images:**
```tsx
{/* Decorative image */}
<img src="logo.png" alt="" role="presentation" />

{/* Informative image */}
<img src="chart.png" alt="Work orders by status: 60% completed, 30% in progress, 10% pending" />
```

**Form fields:**
```tsx
<label htmlFor="company-name">Company Name</label>
<input
  id="company-name"
  type="text"
  aria-required="true"
  aria-describedby="company-name-help"
/>
<p id="company-name-help" className="text-xs text-neutral-500">
  Enter the full legal name of the company
</p>
```

### ARIA States

**Current page:**
```tsx
<nav>
  <a href="/" aria-current="page">Dashboard</a>
  <a href="/companies">Companies</a>
</nav>
```

**Expanded/Collapsed:**
```tsx
<button
  aria-expanded={isOpen}
  aria-controls="dropdown-menu"
  onClick={() => setIsOpen(!isOpen)}
>
  Menu
</button>
<div id="dropdown-menu" hidden={!isOpen}>
  {/* Dropdown content */}
</div>
```

**Selected:**
```tsx
<button
  role="tab"
  aria-selected={isActive}
  aria-controls="tab-panel"
>
  Tab Label
</button>
```

**Disabled:**
```tsx
<button disabled aria-disabled="true">
  Save Changes
</button>
```

### ARIA Live Regions

**Announcements:**
```tsx
{/* Polite: Wait for current speech to finish */}
<div role="status" aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>

{/* Assertive: Interrupt immediately */}
<div role="alert" aria-live="assertive" aria-atomic="true">
  {errorMessage}
</div>
```

**Loading states:**
```tsx
<div
  role="status"
  aria-live="polite"
  aria-label="Loading work orders"
>
  <SpinnerIcon className="animate-spin" />
  <span className="sr-only">Loading work orders...</span>
</div>
```

### Screen Reader Only Text

**Utility class:**
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Usage:**
```tsx
<button>
  <PlusIcon className="w-5 h-5" />
  <span className="sr-only">Create new work order</span>
</button>
```

---

## 2. Keyboard Navigation

### Navigation Patterns

**Tab Order:**
- Interactive elements should be keyboard accessible in logical order
- Use native HTML elements (`<button>`, `<a>`, `<input>`) when possible
- Custom interactive elements need `tabIndex={0}`

**Focus indicators:**
```tsx
{/* ✅ Good: Visible focus ring */}
<button className="
  focus:outline-none
  focus:ring-2
  focus:ring-primary-500
  focus:ring-offset-2
">
  Button
</button>

{/* ❌ Bad: No focus indicator */}
<button className="focus:outline-none">
  Button
</button>
```

### Keyboard Shortcuts

| Key | Action | Context |
|-----|--------|---------|
| **Tab** | Move focus forward | Global |
| **Shift + Tab** | Move focus backward | Global |
| **Enter** | Activate button/link | Buttons, links |
| **Space** | Activate button, toggle checkbox | Buttons, checkboxes |
| **Escape** | Close modal/dropdown | Modals, dropdowns, menus |
| **Arrow keys** | Navigate tabs, menu items | Tabs, menus, lists |
| **Home** | Jump to first item | Lists, tables |
| **End** | Jump to last item | Lists, tables |

### Tab Navigation Examples

**Sidebar navigation:**
```tsx
<nav aria-label="Main navigation">
  <Link href="/" className="focus:ring-2 focus:ring-primary-500">
    Dashboard
  </Link>
  <Link href="/companies" className="focus:ring-2 focus:ring-primary-500">
    Companies
  </Link>
</nav>
```

**Modal focus trap:**
```tsx
function Modal({ isOpen, onClose, children }) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Trap focus inside modal
      const focusableElements = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements?.[0] as HTMLElement;
      const lastElement = focusableElements?.[focusableElements.length - 1] as HTMLElement;

      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key === 'Tab') {
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      };

      document.addEventListener('keydown', handleTabKey);
      firstElement?.focus();

      return () => document.removeEventListener('keydown', handleTabKey);
    }
  }, [isOpen]);

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
    >
      {children}
    </div>
  );
}
```

**Skip to content link:**
```tsx
<a
  href="#main-content"
  className="
    sr-only
    focus:not-sr-only
    focus:absolute
    focus:top-4
    focus:left-4
    focus:z-50
    focus:bg-primary-600
    focus:text-white
    focus:px-4
    focus:py-2
    focus:rounded-md
  "
>
  Skip to main content
</a>

<main id="main-content">
  {/* Page content */}
</main>
```

### Arrow Key Navigation

**Tabs:**
```tsx
function Tabs({ tabs, activeTab, onChange }) {
  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const nextIndex = (index + 1) % tabs.length;
      onChange(tabs[nextIndex].id);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevIndex = (index - 1 + tabs.length) % tabs.length;
      onChange(tabs[prevIndex].id);
    }
  };

  return (
    <div role="tablist">
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onKeyDown={(e) => handleKeyDown(e, index)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
```

**Dropdown menu:**
```tsx
function DropdownMenu({ items }) {
  const [focusedIndex, setFocusedIndex] = useState(0);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedIndex((prev) => (prev + 1) % items.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedIndex((prev) => (prev - 1 + items.length) % items.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      items[focusedIndex].onClick();
    }
  };

  return (
    <div role="menu" onKeyDown={handleKeyDown}>
      {items.map((item, index) => (
        <button
          key={index}
          role="menuitem"
          tabIndex={index === focusedIndex ? 0 : -1}
          onClick={item.onClick}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
```

---

## 3. Screen Reader Compatibility

### Semantic HTML

**Use native HTML elements:**
```tsx
{/* ✅ Good: Semantic HTML */}
<button onClick={handleClick}>Click Me</button>
<a href="/page">Link</a>
<nav>Navigation</nav>
<main>Main content</main>
<header>Header</header>
<footer>Footer</footer>

{/* ❌ Bad: Non-semantic divs */}
<div onClick={handleClick}>Click Me</div>
<div onClick={navigate}>Link</div>
```

### Form Labels

**Always label inputs:**
```tsx
{/* ✅ Good: Explicit label */}
<label htmlFor="email">Email</label>
<input id="email" type="email" />

{/* ✅ Good: Wrapped label */}
<label>
  Email
  <input type="email" />
</label>

{/* ❌ Bad: No label */}
<input type="email" placeholder="Email" />
```

### Descriptive Links

**Link text should make sense out of context:**
```tsx
{/* ❌ Bad: Non-descriptive */}
<a href="/work-orders/123">Click here</a>
<a href="/work-orders/123">Read more</a>

{/* ✅ Good: Descriptive */}
<a href="/work-orders/123">View work order WO-001 details</a>
<a href="/work-orders/123">Read more about HVAC repair at Riyadh HQ</a>
```

### Table Headers

**Use scope attribute:**
```tsx
<table>
  <thead>
    <tr>
      <th scope="col">Company</th>
      <th scope="col">Sites</th>
      <th scope="col">Active WOs</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">ABC Facilities</th>
      <td>12</td>
      <td>8</td>
    </tr>
  </tbody>
</table>
```

### Status Messages

**Announce dynamic content:**
```tsx
function SaveButton() {
  const [status, setStatus] = useState('');

  const handleSave = async () => {
    setStatus('Saving...');
    await saveData();
    setStatus('Saved successfully');
  };

  return (
    <>
      <button onClick={handleSave}>Save</button>
      <div role="status" aria-live="polite" aria-atomic="true">
        {status}
      </div>
    </>
  );
}
```

### Empty States

**Provide meaningful empty state messages:**
```tsx
{/* ✅ Good: Descriptive */}
<EmptyState>
  <p>No work orders found matching your search criteria.</p>
  <p>Try adjusting your filters or create a new work order.</p>
  <Button>Create Work Order</Button>
</EmptyState>

{/* ❌ Bad: Generic */}
<EmptyState>
  <p>No results</p>
</EmptyState>
```

---

## 4. Color Contrast Requirements

### WCAG 2.1 AA Standards

**Minimum Contrast Ratios:**
- **Normal text (< 18pt):** 4.5:1
- **Large text (≥ 18pt or 14pt bold):** 3:1
- **UI components and graphics:** 3:1

### Color Contrast Audit

**Text on Backgrounds:**

| Foreground | Background | Ratio | Pass AA? | Usage |
|------------|------------|-------|----------|-------|
| `neutral-900` | `neutral-0` | 19.5:1 | ✅ AAA | Page titles, headings |
| `neutral-700` | `neutral-0` | 10.8:1 | ✅ AAA | Body text |
| `neutral-600` | `neutral-0` | 7.4:1 | ✅ AAA | Secondary text |
| `neutral-500` | `neutral-0` | 5.1:1 | ✅ AA | Captions, metadata |
| `neutral-500` | `neutral-50` | 4.8:1 | ✅ AA | Captions on light bg |
| `neutral-400` | `neutral-0` | 3.2:1 | ❌ Fail | Placeholder text (fail) |
| `primary-600` | `neutral-0` | 5.8:1 | ✅ AAA | Links |
| `white` | `primary-600` | 5.8:1 | ✅ AAA | Primary buttons |
| `success-dark` | `success-light` | 7.2:1 | ✅ AAA | Success messages |
| `error-dark` | `error-light` | 7.5:1 | ✅ AAA | Error messages |
| `warning-dark` | `warning-light` | 6.1:1 | ✅ AAA | Warning messages |

**Issues to Fix:**
1. **Placeholder text (`neutral-400`):** Fails AA for normal text
   - **Solution:** Use `neutral-500` for placeholders (5.1:1 ratio)

### Button Contrast

**Primary button:**
```tsx
{/* White text on primary-600 background: 5.8:1 ✅ */}
<button className="bg-primary-600 text-white">
  Primary Button
</button>
```

**Secondary button:**
```tsx
{/* neutral-700 text on neutral-0 background: 10.8:1 ✅ */}
<button className="bg-neutral-0 border border-neutral-300 text-neutral-700">
  Secondary Button
</button>
```

**Disabled button:**
```tsx
{/* ⚠️ Check: neutral-500 text on neutral-300 background */}
{/* Better: Use neutral-600 text for sufficient contrast */}
<button disabled className="bg-neutral-300 text-neutral-600">
  Disabled Button
</button>
```

### Interactive Elements

**Focus indicators:**
```tsx
{/* Blue ring on white background: Must meet 3:1 ratio */}
<button className="
  focus:outline-none
  focus:ring-2
  focus:ring-primary-500
  focus:ring-offset-2
">
  Button
</button>
```

**Borders:**
```tsx
{/* neutral-200 border on neutral-0 background: Must meet 3:1 */}
{/* Current ratio: ~1.3:1 ❌ Fails */}
{/* Solution: Use neutral-300 for important borders */}
<input className="border border-neutral-300" />
```

### Color-Only Information

**DON'T rely solely on color:**
```tsx
{/* ❌ Bad: Color-only status */}
<span className="text-success-main">Active</span>
<span className="text-error-main">Inactive</span>

{/* ✅ Good: Text + color */}
<span className="text-success-main">● Active</span>
<span className="text-error-main">○ Inactive</span>

{/* ✅ Good: Badge with text */}
<Badge className="bg-success-light text-success-dark">Active</Badge>
<Badge className="bg-error-light text-error-dark">Inactive</Badge>
```

### Charts and Visualizations

**Provide text alternatives:**
```tsx
<PieChart
  data={data}
  aria-label="Work orders by status"
  aria-describedby="chart-description"
/>
<p id="chart-description" className="sr-only">
  Work orders by status: 60% completed (24 orders), 30% in progress (12 orders), 10% pending (4 orders).
</p>
```

---

## 5. Focus Management

### Focus Indicators

**Always provide visible focus:**
```tsx
{/* ✅ Good: Visible focus ring */}
<button className="
  rounded-lg
  bg-primary-600
  text-white
  px-4 py-2
  focus:outline-none
  focus:ring-2
  focus:ring-primary-500
  focus:ring-offset-2
">
  Button
</button>

{/* ❌ Bad: No focus indicator */}
<button className="focus:outline-none">
  Button
</button>
```

**Custom focus styles:**
```tsx
<Link className="
  text-primary-600
  focus:outline-none
  focus:underline
  focus:underline-offset-4
">
  Link
</Link>
```

### Focus Order

**Logical tab order:**
```tsx
<form>
  {/* Tab order: 1 → 2 → 3 → 4 */}
  <input type="text" placeholder="Name" />
  <input type="email" placeholder="Email" />
  <select>
    <option>Role</option>
  </select>
  <button type="submit">Submit</button>
</form>
```

**Skip navigation with `tabIndex`:**
```tsx
{/* Skip decorative elements */}
<div tabIndex={-1}> {/* Not in tab order */}
  <DecorativeIcon />
</div>

{/* Include interactive custom elements */}
<div tabIndex={0} role="button" onClick={handleClick}>
  Custom Button
</div>
```

### Focus Restoration

**Return focus after modal close:**
```tsx
function Modal({ isOpen, onClose }) {
  const triggerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Store the element that opened the modal
      triggerRef.current = document.activeElement as HTMLElement;
    } else {
      // Restore focus when modal closes
      triggerRef.current?.focus();
    }
  }, [isOpen]);

  return isOpen ? (
    <div role="dialog" aria-modal="true">
      {/* Modal content */}
      <button onClick={onClose}>Close</button>
    </div>
  ) : null;
}
```

**Auto-focus first input in modal:**
```tsx
function CreateWorkOrderModal({ isOpen }) {
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      firstInputRef.current?.focus();
    }
  }, [isOpen]);

  return (
    <form>
      <input ref={firstInputRef} type="text" placeholder="Title" />
      {/* Other fields */}
    </form>
  );
}
```

---

## 6. Form Accessibility

### Form Labels

**Always provide labels:**
```tsx
<div className="space-y-1">
  <label htmlFor="company-name" className="block text-sm font-medium">
    Company Name
  </label>
  <input
    id="company-name"
    type="text"
    aria-required="true"
  />
</div>
```

### Required Fields

**Indicate required fields:**
```tsx
<label htmlFor="email" className="block text-sm font-medium">
  Email <span className="text-error-main">*</span>
</label>
<input
  id="email"
  type="email"
  required
  aria-required="true"
/>
```

### Field Descriptions

**Use `aria-describedby` for help text:**
```tsx
<label htmlFor="password">Password</label>
<input
  id="password"
  type="password"
  aria-describedby="password-help"
/>
<p id="password-help" className="text-xs text-neutral-500">
  Must be at least 8 characters with uppercase, lowercase, and number.
</p>
```

### Error Messages

**Associate errors with fields:**
```tsx
<label htmlFor="email">Email</label>
<input
  id="email"
  type="email"
  aria-invalid={hasError}
  aria-describedby={hasError ? "email-error" : undefined}
  className={hasError ? "border-error-main" : "border-neutral-300"}
/>
{hasError && (
  <p id="email-error" className="text-xs text-error-main" role="alert">
    Please enter a valid email address.
  </p>
)}
```

### Fieldsets and Legends

**Group related fields:**
```tsx
<fieldset>
  <legend className="text-sm font-medium text-neutral-700">
    Contact Information
  </legend>
  <div className="space-y-4">
    <input type="email" placeholder="Email" />
    <input type="tel" placeholder="Phone" />
  </div>
</fieldset>
```

### Form Validation

**Announce validation errors:**
```tsx
function Form() {
  const [errors, setErrors] = useState<string[]>([]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      // Focus first error
      document.getElementById('form-errors')?.focus();
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {errors.length > 0 && (
        <div
          id="form-errors"
          role="alert"
          tabIndex={-1}
          className="bg-error-light text-error-dark p-4 rounded-md"
        >
          <h3 className="font-medium">Please fix the following errors:</h3>
          <ul className="list-disc list-inside">
            {errors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}
      {/* Form fields */}
    </form>
  );
}
```

---

## 7. Interactive Elements

### Touch Target Size

**Minimum size: 44x44 pixels (WCAG 2.5.5)**

```tsx
{/* ✅ Good: 44x44px button */}
<button className="px-4 py-3 text-sm">
  Button
</button>

{/* ⚠️ Marginal: 40px button */}
<button className="px-4 py-2 text-sm">
  Button (increase to py-3)
</button>

{/* ❌ Bad: Small button */}
<button className="px-2 py-1 text-xs">
  Button (too small for touch)
</button>
```

**Icon buttons:**
```tsx
{/* ✅ Good: Sufficient padding */}
<button
  aria-label="Close"
  className="p-2" {/* 16px icon + 8px padding = 40px (increase to p-3 for 44px) */}
>
  <XIcon className="w-4 h-4" />
</button>

{/* Better: Larger touch target */}
<button
  aria-label="Close"
  className="p-3" {/* 16px icon + 12px padding = 44px ✅ */}
>
  <XIcon className="w-4 h-4" />
</button>
```

**Links in text:**
```tsx
{/* Add sufficient spacing around inline links */}
<p className="text-sm leading-relaxed">
  View the <a href="/report" className="text-primary-600 underline px-1">detailed report</a> for more information.
</p>
```

### Hover States

**Provide visual feedback:**
```tsx
<button className="
  bg-primary-600
  hover:bg-primary-700
  transition-colors
">
  Button
</button>

<Link className="
  text-primary-600
  hover:text-primary-700
  hover:underline
">
  Link
</Link>
```

### Active States

**Show feedback on press:**
```tsx
<button className="
  bg-primary-600
  hover:bg-primary-700
  active:bg-primary-800
  transition-colors
">
  Button
</button>
```

### Disabled States

**Make disabled state obvious:**
```tsx
<button
  disabled
  aria-disabled="true"
  className="
    bg-neutral-300
    text-neutral-600
    cursor-not-allowed
  "
>
  Disabled Button
</button>
```

---

## 8. Testing and Validation

### Automated Testing Tools

**Browser Extensions:**
1. **axe DevTools** — Accessibility scanner
2. **WAVE** — Web accessibility evaluation tool
3. **Lighthouse** — Chrome DevTools audit

**Command-line:**
```bash
# Install axe-core
npm install --save-dev @axe-core/cli

# Run audit
axe https://localhost:3000 --save results.json
```

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical
- [ ] Focus indicators are visible
- [ ] Modal focus is trapped
- [ ] Escape closes modals/dropdowns
- [ ] Arrow keys work in menus/tabs

#### Screen Reader
- [ ] Test with NVDA (Windows) or VoiceOver (Mac)
- [ ] All images have alt text
- [ ] Form fields have labels
- [ ] Status messages are announced
- [ ] Tables have headers
- [ ] Links are descriptive

#### Color Contrast
- [ ] All text meets 4.5:1 contrast (AA)
- [ ] Large text meets 3:1 contrast (AA)
- [ ] UI components meet 3:1 contrast
- [ ] Focus indicators are visible
- [ ] Status is not color-only

#### Zoom and Magnification
- [ ] Page works at 200% zoom
- [ ] No horizontal scrolling (desktop)
- [ ] Content reflows correctly
- [ ] Text is readable

#### Touch Targets
- [ ] All interactive elements ≥ 44x44px
- [ ] Sufficient spacing between targets
- [ ] Links in paragraphs are easy to tap

### Screen Reader Testing Script

**Test with NVDA (Windows) or VoiceOver (Mac):**

1. **Navigate by headings:**
   - Press `H` to jump to next heading
   - Verify heading hierarchy (H1 → H2 → H3)

2. **Navigate by landmarks:**
   - Press `D` (NVDA) to jump to next landmark
   - Verify main, nav, complementary regions

3. **Navigate forms:**
   - Press `F` to jump to next form field
   - Verify all fields are labeled
   - Verify required fields are announced

4. **Navigate tables:**
   - Press `T` to jump to next table
   - Verify headers are read with cells

5. **Navigate links:**
   - Press `K` to jump to next link
   - Verify link text is descriptive

### Browser Testing

**Test in multiple browsers:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

### Accessibility Audit Report Template

```markdown
# Accessibility Audit Report

**Date:** YYYY-MM-DD
**Page:** /page-url
**Auditor:** Name

## Summary
- Total issues: X
- Critical: X
- Moderate: X
- Minor: X

## Critical Issues

### Issue 1: Missing alt text on hero image
- **Severity:** Critical
- **WCAG Criterion:** 1.1.1 Non-text Content (Level A)
- **Location:** Homepage, hero section
- **Issue:** `<img src="hero.jpg">` missing alt attribute
- **Fix:** Add `alt="Team collaborating on facility maintenance">`
- **Status:** ❌ Open

### Issue 2: Insufficient color contrast on button text
- **Severity:** Critical
- **WCAG Criterion:** 1.4.3 Contrast (Minimum) (Level AA)
- **Location:** All pages, secondary buttons
- **Issue:** Light gray text on white background (2.8:1 ratio)
- **Fix:** Use darker gray (neutral-700) for 4.5:1+ ratio
- **Status:** ❌ Open

## Moderate Issues

[...]

## Minor Issues

[...]
```

---

## Component Accessibility Checklist

### Button Component
- [ ] Uses `<button>` element
- [ ] Has visible focus indicator
- [ ] Has hover state
- [ ] Has active state
- [ ] Disabled state has `aria-disabled="true"`
- [ ] Icon-only buttons have `aria-label`
- [ ] Touch target ≥ 44x44px

### Link Component
- [ ] Uses `<a>` element with `href`
- [ ] Link text is descriptive
- [ ] Has visible focus indicator
- [ ] Has hover state
- [ ] Current page has `aria-current="page"`

### Modal Component
- [ ] Has `role="dialog"`
- [ ] Has `aria-modal="true"`
- [ ] Has `aria-labelledby` pointing to title
- [ ] Traps focus inside modal
- [ ] Closes on Escape key
- [ ] Restores focus on close
- [ ] Has close button with `aria-label`

### Form Component
- [ ] All inputs have labels
- [ ] Required fields have `aria-required="true"`
- [ ] Error messages have `role="alert"`
- [ ] Error messages linked with `aria-describedby`
- [ ] Invalid fields have `aria-invalid="true"`
- [ ] Help text linked with `aria-describedby`

### Table Component
- [ ] Uses semantic `<table>` element
- [ ] Has `<thead>` and `<tbody>`
- [ ] Headers have `scope="col"` or `scope="row"`
- [ ] Has `aria-label` or `<caption>`
- [ ] Sortable columns indicate sort direction

### Tab Component
- [ ] Tab list has `role="tablist"`
- [ ] Tabs have `role="tab"`
- [ ] Tab panels have `role="tabpanel"`
- [ ] Active tab has `aria-selected="true"`
- [ ] Inactive tabs have `tabindex="-1"`
- [ ] Arrow keys navigate tabs
- [ ] Tab panel linked with `aria-labelledby`

---

## Resources

### WCAG 2.1 Guidelines
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [Understanding WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/)

### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Browser Extension](https://wave.webaim.org/extension/)
- [Chrome Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Color Contrast Analyzer](https://www.tpgi.com/color-contrast-checker/)

### Screen Readers
- [NVDA (Windows, Free)](https://www.nvaccess.org/)
- [JAWS (Windows, Paid)](https://www.freedomscientific.com/products/software/jaws/)
- [VoiceOver (Mac, Built-in)](https://www.apple.com/accessibility/voiceover/)

### Guides and Checklists
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)
- [WebAIM WCAG 2 Checklist](https://webaim.org/standards/wcag/checklist)
- [Inclusive Components](https://inclusive-components.design/)

---

## Conclusion

Accessibility is not optional—it's essential for creating an inclusive FMS application that serves all users effectively. By following these guidelines and testing thoroughly, we ensure compliance with WCAG 2.1 AA standards and provide a better experience for everyone.

**Key Takeaways:**
1. Use semantic HTML whenever possible
2. Provide ARIA labels for non-semantic elements
3. Ensure keyboard navigation works everywhere
4. Test with screen readers regularly
5. Maintain sufficient color contrast (4.5:1 for text)
6. Make touch targets ≥ 44x44px
7. Trap focus in modals and restore on close
8. Announce dynamic content with ARIA live regions

**Next Steps:**
1. Audit existing components with automated tools
2. Conduct manual keyboard navigation tests
3. Test with screen readers (NVDA, VoiceOver)
4. Fix critical accessibility issues
5. Integrate accessibility testing into CI/CD
6. Train team on accessibility best practices
