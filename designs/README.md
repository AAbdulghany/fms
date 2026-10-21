# Orbit layout concepts (mobile-first pilot)

## Files

| File | Purpose |
|------|---------|
| `orbit-mobile-first-layouts.pen` | Pencil canvas — open in the Pencil / pen.dev extension to edit frames |
| `orbit-layout-concepts.html` | Self-contained preview of **4** concepts (phone + desktop companion) |
| `UX_COPY.md` | UX writing for chrome, empty, error, confirm |

## How to open the `.pen`

1. Install / enable the **Pencil** (pen.dev) Cursor extension.  
2. Open `designs/orbit-mobile-first-layouts.pen` from the file tree (double-click).  
3. Ask the agent to generate frames into that file once Pencil reports the file as active.

Until Pencil has the file active, use `orbit-layout-concepts.html` as the reviewable design board.

## Concepts (recommended pick for pilot: **C — Field tabs**)

| ID | Name | Phone idea | Desktop |
|----|------|------------|---------|
| A | Overlay drawer only | Keep hamburger + full sidebar | Current sidebar |
| B | Top segmented | Segmented control under header | Sidebar + segments |
| C | **Field tabs** | Bottom tabs: Home · Work · Assets · More | Sidebar unchanged |
| D | Split role shells | Tech: WO-first; Admin: dashboard-first | Role-aware sidebar order |

**Pilot decision:** ship **C** (implemented in code). Keep desktop sidebar. Native app = vision anti-scope (1C).
