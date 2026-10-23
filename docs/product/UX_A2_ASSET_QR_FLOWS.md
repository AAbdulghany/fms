# UX — A2 Asset QR

## Flow 1 — Print from asset detail

- Button **Print label** next to label code
- Opens PDF (inline) with: client legal name, asset name, label code, QR image
- Secondary: **Show QR** modal (on-screen QR + copy link `/a/{token}`)

## Flow 2 — Scan landing `/a/:token`

| State | UI |
|-------|-----|
| Loading | Skeleton |
| Invalid / revoked | “Label not found” |
| Logged in, same tenant | Redirect to `/assets/:id` |
| Logged out / other tenant | Card: company · site · asset name · **Report a problem** CTA |
| Report submitted | Success toast; no history shown |

## RTL

Mirror actions; QR stays LTR; company name uses Arabic reshape in PDF.
