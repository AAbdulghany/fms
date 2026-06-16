# Show the full demo to a client — deployment analysis

Your **local working demo** is not just a website. It is three layers:

| Layer | Local (Docker) | What the client needs |
|-------|----------------|------------------------|
| **UI** | React on port 8080 | Yes |
| **API** | FastAPI on port 8000 (proxied as `/api`) | Yes — login, work orders, assets |
| **Database** | PostgreSQL `fms_demo` + pitch seed | Yes — demo users and sample data |

```text
localhost:8080  →  nginx/web  →  /api/v1/*  →  FastAPI  →  Postgres
```

---

## Why Vercel / Netlify CLI / drag-and-drop is not enough

Commands like these only upload the **`dist/` folder** (static HTML/JS/CSS):

```bash
npm run build
npx vercel --prod
# or
npx netlify deploy --prod --dir=dist
# or drag dist/ to Netlify Drop
```

| Works | Does not work |
|-------|----------------|
| Pages load, layout, Arabic UI | Login (`super@demo.com`) |
| Routing in the browser | Work orders, assets, invoices |
| | Any `/api/v1/...` call → **404** |

The app calls **`/api/v1`** (see `src/lib/api.ts`). Without a live API + database on the same origin (or proxied), the customer sees a **broken shell**, not your demo.

**Use static-only deploy only** if you only need screenshots or a UI walkthrough with no real data.

---

## What you actually need (full dynamic demo)

Same behaviour as:

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml up
```

Options ranked by **speed to first client call** vs **stays online without your PC**.

### Comparison

| Method | Time to live URL | Full demo? | PC must stay on? | Free? | Best for |
|--------|------------------|------------|------------------|-------|----------|
| **A. Tunnel local Docker** | **~2 min** | Yes | **Yes** | Yes | **Call in 1 hour** |
| **B. Render one website** | ~15 min first time | Yes | No | Yes* | **Share link for days** |
| C. Vercel/Netlify CLI only | ~1 min | **No** | — | Yes | UI mockup only |
| D. Vercel + Render API + DB | ~30 min | Yes | No | Yes* | Two platforms |
| E. Oracle VM + Docker | ~45 min | Yes | No | Yes | Always-on, no cold start |

\*Render free tier: service sleeps when idle; first visit after ~15 min may take 30–60 s.

---

## Method A — Fastest full demo: tunnel your local Docker (~2 minutes)

Expose the **same stack** you already run — no Git, no blueprint, no new hosting.

### 1. Start local demo (if not running)

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml up
```

Confirm http://localhost:8080 works and login succeeds.

### 2. Install Cloudflare Tunnel (one time)

Download [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) or:

```powershell
winget install Cloudflare.cloudflared
```

### 3. Share a public URL

```powershell
cloudflared tunnel --url http://localhost:8080
```

Copy the `https://*.trycloudflare.com` URL → send to the client.

**Pros:** Full demo in minutes; identical to your machine.  
**Cons:** Your PC and Docker must stay running; URL changes each time (unless you set up a named tunnel).

**Alternative:** [ngrok](https://ngrok.com) `ngrok http 8080` — same idea.

---

## Method B — One free website online (no PC required)

**Recommended permanent link:** one Render project, one URL.

| File | Role |
|------|------|
| `render.yaml` | Postgres + single `fms-demo` service |
| `deploy/Dockerfile.demo` | Builds React + runs nginx + API in one container |

### Steps (one-time ~15 min)

1. Push repo to GitHub.
2. [render.com](https://render.com) → **New** → **Blueprint** → connect repo.
3. Wait until **Live**.
4. Open `https://fms-demo.onrender.com` (name from dashboard).
5. Share logins from [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md).

Full guide: **[DEMO_RENDER_ONE_URL.md](./DEMO_RENDER_ONE_URL.md)**

Migrate + pitch seed run **on container start** — no manual database step.

**Pros:** One URL; client can open anytime; matches demo features.  
**Cons:** Not 60 seconds; free tier cold starts; needs GitHub + Render account.

---

## Method C — Static CLI (UI only — not recommended for FMS demo)

Only if the client only needs to **see screens** without logging in:

```powershell
npm run build
npx vercel --prod
```

Tell the client: *“This is a UI preview only — login and data require the full environment.”*

---

## Decision tree

```text
Need client to LOG IN and use real demo data?
├─ YES, need link in the next hour?
│  └─ Method A: cloudflared tunnel → localhost:8080
├─ YES, link should work for days without my laptop?
│  └─ Method B: Render one website (render.yaml + Dockerfile.demo)
└─ NO, only show layout / Arabic / navigation?
   └─ Method C: npx vercel --prod or Netlify Drop (dist only)
```

---

## Demo logins (any full-stack method)

| Email | Password |
|-------|----------|
| super@demo.com | super123 |
| admin@demo.com | admin123 |
| client@demo.com | client123 |

---

## Related docs

| Doc | Use |
|-----|-----|
| [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md) | Local Docker |
| [DEMO_RENDER_ONE_URL.md](./DEMO_RENDER_ONE_URL.md) | Permanent free URL |
| [DEMO_VERCEL_NETLIFY.md](./DEMO_VERCEL_NETLIFY.md) | Split hosting (more setup) |
| [DEMO_LIVE_DEPLOY.md](./DEMO_LIVE_DEPLOY.md) | VM, always-on |
