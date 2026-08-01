# Design System — FMS Phase 2

**Version:** 1.0  
**Date:** 2026-04-17  
**Status:** Living Document

This document defines the comprehensive design system for the FMS project, including color palette, typography, spacing, components, and RTL support guidelines.

---

## Table of Contents

1. [Color Palette](#1-color-palette)
2. [Typography](#2-typography)
3. [Spacing](#3-spacing)
4. [Components](#4-components)
5. [RTL Support Guidelines](#5-rtl-support-guidelines)
6. [Responsive Breakpoints](#6-responsive-breakpoints)
7. [Shadows and Elevation](#7-shadows-and-elevation)
8. [Border Radius](#8-border-radius)
9. [Animation and Transitions](#9-animation-and-transitions)
10. [Icons](#10-icons)

---

## 1. Color Palette

### Primary Colors

**Industrial Teal** — Primary brand color for interactive elements.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary-50` | `#e6f4f7` | Lightest tint, backgrounds |
| `--color-primary-100` | `#b3dee6` | Light backgrounds, hovers |
| `--color-primary-200` | `#80c8d5` | Light accents |
| `--color-primary-300` | `#4db2c4` | Borders, dividers |
| `--color-primary-400` | `#269cb3` | Disabled buttons |
| `--color-primary-500` | `#0d7c8c` | **Default primary color** |
| `--color-primary-600` | `#0a6270` | **Buttons, links** (most used) |
| `--color-primary-700` | `#074954` | Button hover states |
| `--color-primary-800` | `#042f38` | Button active states |
| `--color-primary-900` | `#02161c` | Darkest shade |

**Tailwind Usage:**
```tsx
<button className="bg-primary-600 hover:bg-primary-700">
  Primary Button
</button>
<Link className="text-primary-600 hover:text-primary-700">
  Link Text
</Link>
```

### Secondary Colors

**Warm Orange** — Secondary accent for warnings, highlights, CTAs.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-secondary-50` | `#fff4e6` | Light backgrounds |
| `--color-secondary-100` | `#ffe0b3` | Hover states |
| `--color-secondary-200` | `#ffcc80` | Light accents |
| `--color-secondary-300` | `#ffb74d` | Borders |
| `--color-secondary-400` | `#ffa726` | Default secondary |
| `--color-secondary-500` | `#f57c00` | **Primary secondary color** |
| `--color-secondary-600` | `#e65100` | Hover states |
| `--color-secondary-700` | `#bf360c` | Active states |
| `--color-secondary-800` | `#8c2703` | Darkest shades |
| `--color-secondary-900` | `#5c1a02` | Darkest shade |

**Tailwind Usage:**
```tsx
<button className="bg-secondary-500 hover:bg-secondary-600">
  Secondary Button
</button>
```

### Neutral Colors

**Warm Gray** — Text, backgrounds, borders.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-neutral-0` | `#ffffff` | Pure white, cards, inputs |
| `--color-neutral-50` | `#fafaf9` | Page background |
| `--color-neutral-100` | `#f5f5f4` | Light backgrounds, disabled states |
| `--color-neutral-200` | `#e7e5e4` | Borders, dividers |
| `--color-neutral-300` | `#d6d3d1` | Input borders, subtle borders |
| `--color-neutral-400` | `#a8a29e` | Placeholder text |
| `--color-neutral-500` | `#78716c` | Secondary text |
| `--color-neutral-600` | `#57534e` | Body text |
| `--color-neutral-700` | `#44403c` | Headings, labels |
| `--color-neutral-800` | `#292524` | Dark headings |
| `--color-neutral-900` | `#1c1917` | Darkest text |

**Usage Guide:**
- **Page background:** `neutral-50`
- **Card background:** `neutral-0`
- **Primary text:** `neutral-900` (headings), `neutral-700` (body)
- **Secondary text:** `neutral-600` (labels), `neutral-500` (captions)
- **Borders:** `neutral-200` (default), `neutral-300` (inputs)

**Tailwind Usage:**
```tsx
<div className="bg-neutral-50"> {/* Page */}
  <div className="bg-neutral-0 border border-neutral-200"> {/* Card */}
    <h1 className="text-neutral-900">Heading</h1>
    <p className="text-neutral-700">Body text</p>
    <p className="text-neutral-500">Caption</p>
  </div>
</div>
```

### Semantic Colors

**Success (Green)** — Successful actions, active states.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-success-light` | `#d1fae5` | Background for success messages |
| `--color-success-main` | `#10b981` | **Success badges, icons** |
| `--color-success-dark` | `#047857` | **Text on success backgrounds** |

**Warning (Amber)** — Warnings, attention needed.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-warning-light` | `#fef3c7` | Background for warning messages |
| `--color-warning-main` | `#f59e0b` | **Warning badges, icons** |
| `--color-warning-dark` | `#b45309` | **Text on warning backgrounds** |

**Error (Red)** — Errors, destructive actions.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-error-light` | `#fee2e2` | Background for error messages |
| `--color-error-main` | `#ef4444` | **Error badges, icons** |
| `--color-error-dark` | `#b91c1c` | **Text on error backgrounds** |

**Info (Blue)** — Informational messages.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-info-light` | `#dbeafe` | Background for info messages |
| `--color-info-main` | `#3b82f6` | **Info badges, icons** |
| `--color-info-dark` | `#1d4ed8` | **Text on info backgrounds** |

**Tailwind Usage:**
```tsx
<Alert variant="success">
  <div className="bg-success-light text-success-dark p-4">
    ✓ Work order completed successfully.
  </div>
</Alert>

<Alert variant="error">
  <div className="bg-error-light text-error-dark p-4">
    ✗ Failed to create work order.
  </div>
</Alert>
```

### Status Colors

**Work Order Statuses:**

| Status | Token | Value | Usage |
|--------|-------|-------|-------|
| Created | `--status-created` | `#94a3b8` | Slate gray |
| Assigned | `--status-assigned` | `#3b82f6` | Blue |
| In Progress | `--status-in-progress` | `#f59e0b` | Amber |
| On Hold | `--status-on-hold` | `#8b5cf6` | Purple |
| Completed | `--status-completed` | `#10b981` | Green |
| Verified | `--status-verified` | `#059669` | Dark green |
| Cancelled | `--status-cancelled` | `#ef4444` | Red |
| Rejected | `--status-rejected` | `#dc2626` | Dark red |

**Tailwind Usage:**
```tsx
<StatusBadge status="in_progress">
  <span className="bg-status-in-progress/10 text-status-in-progress">
    In Progress
  </span>
</StatusBadge>
```

### Urgency Colors

| Urgency | Token | Value | Usage |
|---------|-------|-------|-------|
| Normal | `--urgency-normal` | `#10b981` | Green |
| Urgent | `--urgency-urgent` | `#f59e0b` | Amber |
| Emergency | `--urgency-emergency` | `#ef4444` | Red |

### Lifecycle Status Colors

**Asset Lifecycle Statuses:**

| Status | Color | Token Mapping | Usage |
|--------|-------|---------------|-------|
| Active | Green | `success-light` bg, `success-dark` text | Asset operating normally |
| Warning | Yellow | `warning-light` bg, `warning-dark` text | Approaching end of life |
| End of Life | Red | `error-light` bg, `error-dark` text | Exceeded lifespan |
| Replaced | Gray | `neutral-200` bg, `neutral-600` text | Decommissioned |

**Tailwind Usage:**
```tsx
<AssetLifecycleBadge status="warning">
  <span className="bg-warning-light text-warning-dark px-2.5 py-0.5 rounded-full text-xs font-medium">
    Warning
  </span>
</AssetLifecycleBadge>
```

### Maintenance Tag Colors

**Work Order Tags:**

| Tag | Color | Tailwind Class | Usage |
|-----|-------|----------------|-------|
| Preventive | Blue | `bg-blue-100 text-blue-700` | Scheduled preventive maintenance |
| Corrective | Orange | `bg-orange-100 text-orange-700` | Reactive repairs |
| Protective | Purple | `bg-purple-100 text-purple-700` | Protective measures |

**New Design Tokens (to add to `tokens.css`):**
```css
/* Maintenance tag colors */
--tag-preventive-bg: #dbeafe;
--tag-preventive-text: #1d4ed8;
--tag-corrective-bg: #ffedd5;
--tag-corrective-text: #c2410c;
--tag-protective-bg: #f3e8ff;
--tag-protective-text: #7c3aed;
```

**Tailwind Usage:**
```tsx
<TagBadge tag="preventive">
  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-medium">
    Preventive
  </span>
</TagBadge>
```

### Sidebar Colors

**Navigation Sidebar:**

| Element | Color | Token | Usage |
|---------|-------|-------|-------|
| Background | White | `neutral-0` | Sidebar background |
| Border | Light gray | `neutral-200` | Right border (LTR) |
| Active item background | Primary blue | `primary-600` | Active nav item |
| Active item text | White | `neutral-0` | Active nav item text |
| Inactive item text | Dark gray | `neutral-700` | Inactive nav items |
| Hover background | Light gray | `neutral-100` | Hover state |

**Tailwind Usage:**
```tsx
<aside className="bg-neutral-0 border-e border-neutral-200">
  <NavItem active className="bg-primary-600 text-white">
    Dashboard
  </NavItem>
  <NavItem className="text-neutral-700 hover:bg-neutral-100">
    Companies
  </NavItem>
</aside>
```

### Chart Colors

**Data Visualization Palette:**

| Color | Hex | Usage |
|-------|-----|-------|
| Chart 1 (Primary) | `#0d7c8c` | Primary data series |
| Chart 2 (Secondary) | `#f57c00` | Secondary data series |
| Chart 3 (Success) | `#10b981` | Positive metrics |
| Chart 4 (Warning) | `#f59e0b` | Warning metrics |
| Chart 5 (Error) | `#ef4444` | Negative metrics |
| Chart 6 (Purple) | `#8b5cf6` | Additional series |
| Chart 7 (Pink) | `#ec4899` | Additional series |
| Chart 8 (Teal) | `#14b8a6` | Additional series |

**Usage Example:**
```tsx
<PieChart colors={['#0d7c8c', '#f57c00', '#10b981', '#f59e0b', '#ef4444']} />
```

---

## 2. Typography

### Font Families

**English (LTR):**
- **Display:** `Plus Jakarta Sans` → Fallback: `Segoe UI, system-ui, sans-serif`
- **Body:** `Inter` → Fallback: `Segoe UI, system-ui, sans-serif`
- **Monospace:** `JetBrains Mono` → Fallback: `Fira Code, ui-monospace, monospace`

**Arabic (RTL):**
- **Display:** `IBM Plex Sans Arabic` → Fallback: `Segoe UI, system-ui, sans-serif`
- **Body:** `Noto Sans Arabic` → Fallback: `Segoe UI, system-ui, sans-serif`

**Design Tokens:**
```css
--font-display-en: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
--font-body-en: "Inter", "Segoe UI", system-ui, sans-serif;
--font-mono: "JetBrains Mono", "Fira Code", ui-monospace, monospace;
--font-display-ar: "IBM Plex Sans Arabic", "Segoe UI", system-ui, sans-serif;
--font-body-ar: "Noto Sans Arabic", "Segoe UI", system-ui, sans-serif;
```

**Tailwind Classes:**
```tsx
<h1 className="font-display-en">English Display Heading</h1>
<p className="font-body-en">English body text</p>
<code className="font-mono">Monospace code</code>

{/* RTL mode: Auto-applied via base CSS */}
<html dir="rtl">
  <h1>Arabic Display Heading</h1> {/* Uses font-display-ar */}
  <p>Arabic body text</p> {/* Uses font-body-ar */}
</html>
```

### Font Size Scale

| Token | Value | Line Height | Usage |
|-------|-------|-------------|-------|
| `--text-xs` | `0.75rem` (12px) | `1rem` (16px) | Badge labels, captions, metadata |
| `--text-sm` | `0.875rem` (14px) | `1.25rem` (20px) | **Default body text**, labels |
| `--text-base` | `1rem` (16px) | `1.5rem` (24px) | Large body text, subheadings |
| `--text-lg` | `1.125rem` (18px) | `1.75rem` (28px) | Subheadings, card titles |
| `--text-xl` | `1.25rem` (20px) | `1.75rem` (28px) | H4 headings |
| `--text-2xl` | `1.5rem` (24px) | `2rem` (32px) | H3 headings |
| `--text-3xl` | `1.875rem` (30px) | `2.25rem` (36px) | H2 headings, **page titles** |
| `--text-4xl` | `2.25rem` (36px) | `2.5rem` (40px) | H1 headings, hero titles |

**Tailwind Usage:**
```tsx
<h1 className="text-3xl">Page Title</h1>
<h2 className="text-2xl">Section Heading</h2>
<h3 className="text-xl">Subsection Heading</h3>
<p className="text-sm">Body text (default)</p>
<p className="text-xs">Caption or metadata</p>
```

### Font Weight Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--font-display` | `700` | Display headings |
| `--font-h1` | `600` | H1 headings |
| `--font-h2` | `600` | H2 headings |
| `--font-h3` | `600` | H3 headings |
| `--font-h4` | `500` | H4 headings |
| `--font-body` | `400` | Body text |
| `--font-overline` | `600` | Uppercase labels |

**Tailwind Usage:**
```tsx
<h1 className="text-3xl font-h1">Page Title</h1>
<h2 className="text-2xl font-h2">Section Heading</h2>
<p className="text-sm font-body">Body text</p>
<span className="text-xs font-overline uppercase">Overline Label</span>
```

### Typography Hierarchy

**Standard Page Hierarchy:**

```tsx
<div className="space-y-6">
  {/* Page Title */}
  <h1 className="text-3xl font-semibold text-neutral-900">
    Page Title
  </h1>
  
  {/* Section Heading */}
  <h2 className="text-xl font-medium text-neutral-800">
    Section Heading
  </h2>
  
  {/* Subsection Heading */}
  <h3 className="text-lg font-medium text-neutral-800">
    Subsection Heading
  </h3>
  
  {/* Body Text */}
  <p className="text-sm text-neutral-700">
    Body text content goes here. This is the default text size for paragraphs.
  </p>
  
  {/* Caption/Metadata */}
  <p className="text-xs text-neutral-500">
    Created on 2026-04-17 • Last updated 2 hours ago
  </p>
</div>
```

### Text Color Standards

| Use Case | Color | Tailwind Class |
|----------|-------|----------------|
| Page titles (H1) | Neutral 900 | `text-neutral-900` |
| Section headings (H2-H4) | Neutral 800 | `text-neutral-800` |
| Body text | Neutral 700 | `text-neutral-700` |
| Labels | Neutral 700 | `text-neutral-700` |
| Secondary text | Neutral 600 | `text-neutral-600` |
| Captions, metadata | Neutral 500 | `text-neutral-500` |
| Placeholder text | Neutral 400 | `text-neutral-400` |
| Disabled text | Neutral 400 | `text-neutral-400` |
| Links | Primary 600 | `text-primary-600` |
| Link hover | Primary 700 | `hover:text-primary-700` |

---

## 3. Spacing

### Spacing Scale

**Design Tokens:**
```css
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-5: 1.25rem;  /* 20px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
--spacing-10: 2.5rem;  /* 40px */
--spacing-12: 3rem;    /* 48px */
```

**Tailwind Spacing Scale:**

| Tailwind | Value | Usage |
|----------|-------|-------|
| `1` | `4px` | Minimal spacing, icon gaps |
| `2` | `8px` | Small gaps, badge padding |
| `3` | `12px` | Medium gaps, button padding |
| `4` | `16px` | **Standard gap**, form field spacing |
| `5` | `20px` | Large gaps |
| `6` | `24px` | **Card padding**, section spacing |
| `8` | `32px` | Extra large gaps |
| `10` | `40px` | Section spacing |
| `12` | `48px` | Large section spacing |

### Container Padding Standards

| Container | Padding | Tailwind Class | Usage |
|-----------|---------|----------------|-------|
| Page | `24px` (1.5rem) | `p-6` | Main page container |
| Card | `24px` (1.5rem) | `p-6` | Card components |
| Modal | `24px` (1.5rem) | `p-6` | Modal dialogs |
| Sidebar | `16px` (1rem) | `p-4` | Navigation sidebar |
| Table cell | `16px 16px` (1rem) | `px-4 py-3` | Table cells |
| Button | `16px 12px` (1rem 0.75rem) | `px-4 py-3` | Standard button |
| Badge | `10px 8px` (0.625rem 0.5rem) | `px-2.5 py-0.5` | Badge labels |

### Vertical Spacing Standards

| Context | Spacing | Tailwind Class | Usage |
|---------|---------|----------------|-------|
| Page sections | `24px` (1.5rem) | `space-y-6` | Between major sections |
| Card content | `16px` (1rem) | `space-y-4` | Inside cards |
| Form fields | `16px` (1rem) | `space-y-4` | Between form fields |
| Button groups | `12px` (0.75rem) | `gap-3` | Between buttons |
| List items | `8px` (0.5rem) | `space-y-2` | Between list items |

**Usage Example:**
```tsx
<div className="space-y-6"> {/* Page sections */}
  <Card className="p-6"> {/* Card padding */}
    <div className="space-y-4"> {/* Card content */}
      <h2>Section Title</h2>
      <p>Content</p>
      <div className="flex gap-3"> {/* Button group */}
        <Button>Save</Button>
        <Button>Cancel</Button>
      </div>
    </div>
  </Card>
</div>
```

---

## 4. Components

### Button Variants

**Primary Button:**
```tsx
<button className="
  rounded-lg
  bg-primary-600 hover:bg-primary-700 active:bg-primary-800
  px-4 py-2.5
  text-sm font-medium text-white
  transition-colors
  disabled:bg-neutral-300 disabled:text-neutral-500 disabled:cursor-not-allowed
  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
">
  Primary Button
</button>
```

**Secondary Button:**
```tsx
<button className="
  rounded-lg
  bg-neutral-0 hover:bg-neutral-50 active:bg-neutral-100
  border border-neutral-300
  px-4 py-2.5
  text-sm font-medium text-neutral-700
  transition-colors
  disabled:bg-neutral-100 disabled:text-neutral-400 disabled:cursor-not-allowed
  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
">
  Secondary Button
</button>
```

**Ghost Button:**
```tsx
<button className="
  rounded-lg
  bg-transparent hover:bg-neutral-100 active:bg-neutral-200
  px-4 py-2.5
  text-sm font-medium text-neutral-700
  transition-colors
  disabled:text-neutral-400 disabled:cursor-not-allowed
  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
">
  Ghost Button
</button>
```

**Danger Button:**
```tsx
<button className="
  rounded-lg
  bg-error-main hover:bg-error-dark active:bg-error-dark
  px-4 py-2.5
  text-sm font-medium text-white
  transition-colors
  disabled:bg-neutral-300 disabled:text-neutral-500 disabled:cursor-not-allowed
  focus:outline-none focus:ring-2 focus:ring-error-main focus:ring-offset-2
">
  Delete
</button>
```

**Button Sizes:**

| Size | Padding | Text Size | Tailwind Classes |
|------|---------|-----------|------------------|
| Small | `px-3 py-1.5` | `text-xs` | `px-3 py-1.5 text-xs` |
| Medium (default) | `px-4 py-2.5` | `text-sm` | `px-4 py-2.5 text-sm` |
| Large | `px-6 py-3` | `text-base` | `px-6 py-3 text-base` |

### Badge Variants

**Status Badge:**
```tsx
<span className="
  inline-flex items-center
  rounded-full
  px-2.5 py-0.5
  text-xs font-medium
  bg-success-light text-success-dark
">
  Active
</span>
```

**Badge Colors by Context:**

| Context | Background | Text | Example |
|---------|------------|------|---------|
| Success | `bg-success-light` | `text-success-dark` | Active, Completed |
| Warning | `bg-warning-light` | `text-warning-dark` | Warning, Pending |
| Error | `bg-error-light` | `text-error-dark` | Error, End of Life |
| Info | `bg-info-light` | `text-info-dark` | Info, New |
| Neutral | `bg-neutral-200` | `text-neutral-600` | Default, Inactive |

### Card Variants

**Standard Card:**
```tsx
<div className="
  rounded-lg
  border border-neutral-200
  bg-neutral-0
  p-6
  shadow-sm
">
  Card content
</div>
```

**Interactive Card (Clickable):**
```tsx
<Link className="
  block
  rounded-lg
  border border-neutral-200
  bg-neutral-0
  p-6
  shadow-sm
  transition-colors
  hover:border-primary-300
">
  Card content
</Link>
```

**Card with Header:**
```tsx
<div className="rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
  <div className="border-b border-neutral-200 px-6 py-4">
    <h3 className="text-lg font-medium text-neutral-800">Card Title</h3>
  </div>
  <div className="p-6">
    Card content
  </div>
</div>
```

### Form Field Standards

**Input Field:**
```tsx
<div className="space-y-1">
  <label className="block text-sm font-medium text-neutral-700">
    Label
  </label>
  <input
    type="text"
    className="
      w-full
      rounded-md
      border border-neutral-300
      px-3 py-2
      text-sm
      placeholder:text-neutral-400
      focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500
      disabled:bg-neutral-100 disabled:text-neutral-400 disabled:cursor-not-allowed
    "
    placeholder="Enter text..."
  />
  <p className="text-xs text-neutral-500">Helper text</p>
</div>
```

**Input with Error:**
```tsx
<div className="space-y-1">
  <label className="block text-sm font-medium text-neutral-700">
    Label
  </label>
  <input
    type="text"
    className="
      w-full
      rounded-md
      border border-error-main
      px-3 py-2
      text-sm
      focus:border-error-main focus:outline-none focus:ring-1 focus:ring-error-main
    "
  />
  <p className="text-xs text-error-main">Error message</p>
</div>
```

### Modal Standards

**Modal Overlay:**
```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
  <div className="
    w-full max-w-md
    rounded-xl
    bg-white
    p-6
    shadow-xl
  ">
    {/* Modal content */}
  </div>
</div>
```

### Table Standards

**Standard Table:**
```tsx
<div className="overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-0 shadow-sm">
  <table className="min-w-full text-start text-sm">
    <thead className="bg-neutral-100 text-neutral-700">
      <tr>
        <th className="px-4 py-3 font-medium">Column 1</th>
        <th className="px-4 py-3 font-medium">Column 2</th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-t border-neutral-200 hover:bg-neutral-50">
        <td className="px-4 py-3">Data 1</td>
        <td className="px-4 py-3">Data 2</td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 5. RTL Support Guidelines

### Logical Properties

**DO:** Use logical properties that adapt to text direction.

```tsx
{/* ✅ Correct: Logical properties */}
<div className="ms-4">Margin start (left in LTR, right in RTL)</div>
<div className="me-4">Margin end (right in LTR, left in RTL)</div>
<div className="ps-4">Padding start</div>
<div className="pe-4">Padding end</div>
<div className="text-start">Text align start</div>
<div className="text-end">Text align end</div>
<div className="border-s">Border start</div>
<div className="border-e">Border end</div>
```

**DON'T:** Use directional properties that break in RTL.

```tsx
{/* ❌ Wrong: Physical directions */}
<div className="ml-4">Margin left (always left, breaks RTL)</div>
<div className="mr-4">Margin right (always right, breaks RTL)</div>
<div className="text-left">Text align left (always left)</div>
<div className="text-right">Text align right (always right)</div>
```

### Flexbox and Grid RTL

**Flexbox:**
```tsx
{/* ✅ Correct: Use gap (symmetric) */}
<div className="flex gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

{/* ⚠️ Requires RTL adjustment: space-x */}
<div className="flex space-x-4 rtl:space-x-reverse">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

**Grid:**
```tsx
{/* ✅ Correct: Grid auto-reverses in RTL */}
<div className="grid grid-cols-3 gap-4">
  <div>1</div>
  <div>2</div>
  <div>3</div>
</div>
```

### Icon Flipping Rules

**DO Flip:**
- Directional arrows (→, ←, ↑, ↓)
- Chevrons (›, ‹)
- Forward/back navigation icons
- Undo/redo icons

**DON'T Flip:**
- Symmetric icons (✓, ✗, +, −)
- Recognizable objects (🏠, 📦, 👤)
- Status icons (⚠️, ℹ️, ✓)

**Implementation:**
```tsx
{/* Directional icon: Flip in RTL */}
<ArrowRightIcon className="w-5 h-5 rtl:scale-x-[-1]" />

{/* Symmetric icon: No flip needed */}
<CheckIcon className="w-5 h-5" />
```

### Layout Mirroring

**Sidebar Position:**
```tsx
{/* LTR: Left sidebar */}
<aside className="fixed inset-y-0 start-0 w-60">
  {/* Sidebar content */}
</aside>

{/* Main content with start offset */}
<main className="ms-60">
  {/* Page content */}
</main>
```

In RTL:
- `start-0` becomes `right: 0`
- `ms-60` becomes `margin-right: 15rem`

**Breadcrumb Separator:**
```css
.breadcrumb-separator {
  content: '›';
}

[dir="rtl"] .breadcrumb-separator {
  transform: scaleX(-1); /* Flip to ‹ */
}
```

### RTL Testing Checklist

- [ ] All margin/padding uses logical properties
- [ ] Flexbox `space-x` has `rtl:space-x-reverse`
- [ ] Icons are flipped where appropriate
- [ ] Sidebar positioned with `start-*`
- [ ] Text alignment uses `text-start`/`text-end`
- [ ] Forms and tables tested in RTL mode
- [ ] Breadcrumbs tested with RTL separator

---

## 6. Responsive Breakpoints

### Breakpoint Scale

| Breakpoint | Min Width | Max Width | Usage |
|------------|-----------|-----------|-------|
| **xs (default)** | `0px` | `639px` | Mobile portrait |
| **sm** | `640px` | `767px` | Mobile landscape, small tablets |
| **md** | `768px` | `1023px` | Tablets |
| **lg** | `1024px` | `1279px` | Desktops, laptops |
| **xl** | `1280px` | `1535px` | Large desktops |
| **2xl** | `1536px` | — | Extra large screens |

### Mobile-First Approach

**Tailwind uses mobile-first responsive design:**
- Base styles apply to mobile (< 640px)
- Use breakpoint prefixes to override for larger screens

**Example:**
```tsx
<div className="
  grid
  grid-cols-1        {/* Mobile: 1 column */}
  sm:grid-cols-2     {/* Small+: 2 columns */}
  lg:grid-cols-4     {/* Large+: 4 columns */}
  gap-4
">
  {/* Content */}
</div>
```

### Common Responsive Patterns

**Sidebar:**
```tsx
{/* Mobile: Hidden, hamburger menu */}
<aside className="hidden lg:block fixed inset-y-0 start-0 w-60">
  {/* Sidebar content */}
</aside>

{/* Mobile: Hamburger button */}
<button className="lg:hidden fixed top-4 start-4 z-50">
  <MenuIcon />
</button>
```

**Typography:**
```tsx
<h1 className="
  text-2xl        {/* Mobile: 24px */}
  sm:text-3xl     {/* Small+: 30px */}
  lg:text-4xl     {/* Large+: 36px */}
">
  Responsive Heading
</h1>
```

**Grid Layouts:**
```tsx
{/* Stat cards */}
<div className="
  grid
  grid-cols-1       {/* Mobile: 1 col */}
  sm:grid-cols-2    {/* Small+: 2 cols */}
  lg:grid-cols-4    {/* Large+: 4 cols */}
  gap-4
">
  {/* Cards */}
</div>
```

**Table to Cards:**
```tsx
{/* Desktop: Table */}
<table className="hidden md:table min-w-full">
  {/* Table content */}
</table>

{/* Mobile: Cards */}
<div className="md:hidden space-y-4">
  {items.map(item => (
    <Card key={item.id}>
      {/* Card content */}
    </Card>
  ))}
</div>
```

---

## 7. Shadows and Elevation

### Shadow Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Subtle cards, inputs |
| `--shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | Cards, dropdowns |
| `--shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1)` | Popovers, tooltips |
| `--shadow-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1)` | Modals, overlays |

**Tailwind Usage:**
```tsx
<Card className="shadow-sm">Subtle card</Card>
<Dropdown className="shadow-lg">Dropdown menu</Dropdown>
<Modal className="shadow-xl">Modal dialog</Modal>
```

### Elevation Hierarchy

| Level | Shadow | Usage |
|-------|--------|-------|
| 0 | None | Flat elements, backgrounds |
| 1 | `shadow-sm` | Subtle cards, inputs |
| 2 | `shadow-md` | Standard cards, buttons |
| 3 | `shadow-lg` | Dropdowns, popovers |
| 4 | `shadow-xl` | Modals, drawers |

---

## 8. Border Radius

### Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `4px` | Small elements, badges |
| `--radius-md` | `8px` | Buttons, inputs |
| `--radius-lg` | `12px` | Cards, containers |
| `--radius-xl` | `16px` | Modals, large containers |
| `--radius-full` | `9999px` | Pills, circular badges |

**Tailwind Usage:**
```tsx
<Badge className="rounded-full">Pill badge</Badge>
<Button className="rounded-lg">Button</Button>
<Input className="rounded-md">Input field</Input>
<Card className="rounded-lg">Card</Card>
<Modal className="rounded-xl">Modal</Modal>
```

### Border Radius Standards

| Element | Radius | Tailwind Class |
|---------|--------|----------------|
| Badge | Full | `rounded-full` |
| Button | Large | `rounded-lg` |
| Input | Medium | `rounded-md` |
| Card | Large | `rounded-lg` |
| Modal | Extra large | `rounded-xl` |
| Dropdown | Large | `rounded-lg` |

---

## 9. Animation and Transitions

### Transition Standards

**Duration:**
- **Fast:** `150ms` — Hover states, small UI changes
- **Base:** `200ms` — Default transitions
- **Slow:** `300ms` — Page transitions, large elements

**Easing:**
- **Ease-in-out:** Default for most transitions
- **Ease-out:** For appearing elements
- **Ease-in:** For disappearing elements

**Tailwind Usage:**
```tsx
<button className="
  transition-colors duration-200
  hover:bg-primary-700
">
  Button
</button>

<div className="
  transition-all duration-300 ease-in-out
  hover:scale-105
">
  Card
</div>
```

### Common Animations

**Fade In:**
```tsx
<div className="animate-fade-in opacity-0">
  Content fades in
</div>

{/* Define in globals.css */}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.animate-fade-in {
  animation: fade-in 200ms ease-out forwards;
}
```

**Slide In:**
```tsx
<div className="animate-slide-in-right">
  Content slides in from right
</div>

@keyframes slide-in-right {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.animate-slide-in-right {
  animation: slide-in-right 300ms ease-out;
}
```

**Pulse (Loading):**
```tsx
<div className="animate-pulse">
  Loading skeleton
</div>
```

---

## 10. Icons

### Icon Library

**Recommended:** [Lucide Icons](https://lucide.dev/) or [Heroicons](https://heroicons.com/)

**Icon Sizes:**

| Size | Width | Height | Usage |
|------|-------|--------|-------|
| XS | `12px` | `12px` | Inline text icons |
| SM | `16px` | `16px` | Badges, small buttons |
| Base | `20px` | `20px` | Standard icons |
| LG | `24px` | `24px` | Large buttons, nav items |
| XL | `32px` | `32px` | Hero sections, empty states |

**Tailwind Usage:**
```tsx
<HomeIcon className="w-5 h-5" /> {/* 20px */}
<CheckIcon className="w-4 h-4" /> {/* 16px */}
<MenuIcon className="w-6 h-6" /> {/* 24px */}
```

### Icon Color Standards

| Context | Color | Tailwind Class |
|---------|-------|----------------|
| Default | Neutral 600 | `text-neutral-600` |
| Active | Primary 600 | `text-primary-600` |
| Success | Success main | `text-success-main` |
| Warning | Warning main | `text-warning-main` |
| Error | Error main | `text-error-main` |
| Disabled | Neutral 400 | `text-neutral-400` |

**Usage:**
```tsx
<CheckIcon className="w-5 h-5 text-success-main" />
<AlertIcon className="w-5 h-5 text-warning-main" />
<XIcon className="w-5 h-5 text-error-main" />
```

---

## Implementation Checklist

### New Design Tokens to Add

Add these tokens to `src/styles/tokens.css`:

```css
/* Maintenance tag colors */
--tag-preventive-bg: #dbeafe;
--tag-preventive-text: #1d4ed8;
--tag-corrective-bg: #ffedd5;
--tag-corrective-text: #c2410c;
--tag-protective-bg: #f3e8ff;
--tag-protective-text: #7c3aed;

/* Chart colors */
--chart-1: #0d7c8c;
--chart-2: #f57c00;
--chart-3: #10b981;
--chart-4: #f59e0b;
--chart-5: #ef4444;
--chart-6: #8b5cf6;
--chart-7: #ec4899;
--chart-8: #14b8a6;
```

### Tailwind Theme Extension

Add to `src/styles/tailwind.theme.js`:

```javascript
colors: {
  // ... existing colors ...
  
  tag: {
    'preventive-bg': 'var(--tag-preventive-bg)',
    'preventive-text': 'var(--tag-preventive-text)',
    'corrective-bg': 'var(--tag-corrective-bg)',
    'corrective-text': 'var(--tag-corrective-text)',
    'protective-bg': 'var(--tag-protective-bg)',
    'protective-text': 'var(--tag-protective-text)',
  },
  
  chart: {
    1: 'var(--chart-1)',
    2: 'var(--chart-2)',
    3: 'var(--chart-3)',
    4: 'var(--chart-4)',
    5: 'var(--chart-5)',
    6: 'var(--chart-6)',
    7: 'var(--chart-7)',
    8: 'var(--chart-8)',
  },
}
```

---

## Conclusion

This design system provides a comprehensive foundation for building consistent, accessible, and maintainable UI components for the FMS project. All design decisions are grounded in design tokens defined in `src/styles/tokens.css` and mapped to Tailwind utilities via `src/styles/tailwind.theme.js`.

**Key Principles:**
1. **Token-driven:** All colors, spacing, typography reference design tokens
2. **RTL-first:** Use logical properties for Arabic/RTL support
3. **Responsive:** Mobile-first approach with clear breakpoints
4. **Accessible:** WCAG 2.1 AA compliance for contrast, focus states
5. **Consistent:** Standardized component patterns and spacing

**Next Steps:**
1. Add new design tokens to `tokens.css`
2. Extend Tailwind theme with new tokens
3. Create core component library following these standards
4. Document component usage examples
5. Conduct design review and accessibility audit
