# CMMS color palettes — research for eye comfort

**Context:** Orbit Concept D field shell (Queue / Scan / Time). Users are often on-site (bright wards, outdoor yards).  
**Current apply:** P4 Copper Signal + Pat2 Dot grid.

## What leading CMMS / EAM products do

| Pattern | Who it resembles | Primary | CTA / signal | Why it works |
|---------|------------------|---------|--------------|--------------|
| Teal / cyan ops | MaintainX-class mobile CMMS | Cool teal | Amber for warnings | Calm “ops” feel; easy long sessions |
| Green “go” | UpKeep-style systems | Neutrals + green CTA | Orange edit / red alert | Primary action is unmistakable |
| Industrial blue + yellow | Trimble Modus / heavy EAM | `#0063A3`-class blue | Yellow/amber signal | High trust, industrial brand DNA |
| High-contrast field | Sunlight / industrial UX guides | Near-black bg OR near-white | Yellow/cyan highlights | Survives glare; not a marketing palette |

Sources: Trimble Modus palette docs; UpKeep-style purpose-driven color systems; industrial sunlight UX (high luminance contrast, avoid blue-on-black, drop gradients); WCAG AA minimum 4.5:1 text.

## Eye comfort rules for technicians

1. **Cool chrome, hot only for meaning** — Blue/teal for brand/nav; amber/red only for urgency/errors. Warm copper as *everything* (current P4) reads as constant alert.
2. **One loud CTA color** — Green or deep blue for “Start / Complete”; secondary actions stay neutral outline.
3. **Flat surfaces outdoors** — Soft shadows and busy patterns wash out in sun; Pat2 dots are OK if very light.
4. **Never color-only status** — Pair with label/icon (WCAG 1.4.1).
5. **Optional later:** dark “sunlight mode” (light text on near-black) for yards — best outdoor readability per industrial UX.

## Map to Orbit P0–P4

| Orbit ID | Eye comfort (field) | Notes |
|----------|---------------------|-------|
| P0 Industrial Teal | Good | Industry-familiar; closest to MaintainX |
| P1 Harbor Navy | **Very good** | Closest to Trimble industrial blue |
| P2 Field Olive | OK | Outdoor grit; less “hospital clinical” |
| P3 Midnight Steel | Good indoors | Slate chrome; amber CTA |
| **P4 Copper Signal (now)** | **Weaker for long sessions** | Distinctive brand, but primary = urgency color |
| **Hybrid (recommended)** | **Best** | Navy chrome + green Start CTA + amber urgency only |

## Recommendation

For **eye comfort on site**, move off P4 as the *primary* brand color:

- **Best:** apply **hybrid** — Harbor Navy chrome (`#1D4E89`) + green Start/Complete (`#2B8831`) + keep Pat2.  
- **Simple:** `use P1 + Pat2` (one palette ID, already designed).  
- **Keep P4 only if** you want a bold “urgent field” brand and accept more visual heat.

Reply with `apply hybrid` or `use P1 + Pat2` (or keep P4) to retoken the app.
