# Demo on Vercel / Netlify (+ free subdomain)

Host the **React UI** on [Vercel](https://vercel.com) or [Netlify](https://netlify.com) (`your-app.vercel.app` / `your-app.netlify.app`).  
The **API + database** run on [Render](https://render.com) (free tier) — Vercel/Netlify cannot run long-lived FastAPI + Postgres for this stack.

| Layer | Provider | Free URL example |
|-------|----------|------------------|
| Frontend | **Vercel** or **Netlify** | `https://fms-demo.vercel.app` |
| API | **Render** Web Service (Docker) | `https://fms-demo-api.onrender.com` |
| Database | **Render Postgres** (or Neon) | internal only |

**Branch:** deploy from `demo/live` (see [deploy/demo/BRANCH_MANIFEST.md](../../deploy/demo/BRANCH_MANIFEST.md)).

---

## Architecture

```
Browser → fms-demo.vercel.app
            ├─ /*           → static React (dist/)
            └─ /api/*       → proxy → fms-demo-api.onrender.com/api/*
                    API → Render Postgres (fms_demo)
```

The browser always calls **same-origin** `/api/v1/...` — no CORS issues. Vercel/Netlify rewrite `/api` to Render.

---

## Phase 1 — Database + API on Render (~15 min)

### 1.1 Create Render account

Sign up at [render.com](https://render.com) (GitHub login).

### 1.2 Deploy with Blueprint (easiest)

1. Push repo (branch `demo/live`) to GitHub.
2. Render Dashboard → **New** → **Blueprint**.
3. Connect repo → Render reads root **`render.yaml`**.
4. Review services: `fms-demo-db`, `fms-demo-api`, and optionally `fms-demo-web` (static frontend).
5. Deploy. Wait until API status is **Live** (first start may take 5–10 min on free tier).

> **Blueprint note:** Static sites use `type: web` + `runtime: static` — not `type: static`. If Blueprint validation fails, pull the latest `render.yaml` from the repo.

Note your API URL: `https://fms-demo-api.onrender.com` (name may vary).

### 1.3 Set API environment variables

In Render → **fms-demo-api** → **Environment**:

| Variable | Example |
|----------|---------|
| `APP_ENV` | `demo` |
| `SEED_MODULE` | `pitch` |
| `CORS_ORIGINS` | `https://fms-demo.vercel.app` (set after Phase 2) |
| `PUBLIC_APP_URL` | same as CORS |
| `SECRET_KEY` | auto-generated or your own 64-char hex |

`DATABASE_URL` is wired from Render Postgres by the blueprint.

### 1.4 Run migrate + pitch seed (one time)

Render → **fms-demo-api** → **Shell**:

```bash
python -m app.docker_migrate
```

Expect: `Migrate complete.` and pitch demo logins created.

Verify:

```bash
curl https://YOUR-API.onrender.com/health
# {"status":"ok"}
```

**Free tier cold start:** API sleeps after ~15 min idle; first request may take 30–60 s.

---

## Phase 2A — Frontend on Vercel (~10 min)

### 2A.1 Import project

1. [vercel.com](https://vercel.com) → **Add New** → **Project** → import GitHub repo.
2. **Branch:** `demo/live`
3. **Framework Preset:** Vite
4. **Build Command:** `npm run build`
5. **Output Directory:** `dist`
6. Deploy once (API proxy not wired yet — expect login errors until step 2A.2).

### 2A.2 Wire API proxy

Edit **`vercel.json`** in repo — replace placeholder:

```json
"destination": "https://YOUR-ACTUAL-API.onrender.com/api/$1"
```

Commit and push → Vercel redeploys automatically.

### 2A.3 Update Render CORS

Render → API env:

```
CORS_ORIGINS=https://your-project.vercel.app
PUBLIC_APP_URL=https://your-project.vercel.app
```

Redeploy API if needed.

### 2A.4 Test

Open `https://your-project.vercel.app` → login `super@demo.com` / `super123`.

---

## Phase 2B — Frontend on Netlify (~10 min)

### 2B.1 Import site

1. [netlify.com](https://netlify.com) → **Add new site** → **Import from Git**.
2. Branch: `demo/live`
3. Build: `npm run build`, publish: `dist`
4. Deploy.

### 2B.2 Wire API proxy

Edit **`netlify.toml`** — replace:

```toml
to = "https://YOUR-ACTUAL-API.onrender.com/api/:splat"
```

Push → Netlify rebuilds.

### 2B.3 CORS on Render

Same as Vercel step 2A.3 with your `*.netlify.app` URL.

---

## Alternative: Neon Postgres + Render API only

If Render Postgres free tier is unavailable:

1. Create DB at [neon.tech](https://neon.tech) (free).
2. Copy connection string → Render API env `DATABASE_URL`.
3. Render Shell: `python -m app.docker_migrate`.

---

## Demo logins (share with evaluators)

| Email | Password | Role |
|-------|----------|------|
| super@demo.com | super123 | Platform super_user |
| admin@demo.com | admin123 | Maintenance company admin |
| client@demo.com | client123 | End client admin |

Full list: [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md)

---

## Custom domain (optional)

| Provider | Steps |
|----------|--------|
| **Vercel** | Project → Settings → Domains → add `demo.yourdomain.com` |
| **Netlify** | Site → Domain management → add custom domain |
| **Render API** | Update `CORS_ORIGINS` + `PUBLIC_APP_URL` to match frontend URL |

---

## Reset demo data

Log in as **super@demo.com** → or call:

```bash
curl -X POST https://YOUR-API.onrender.com/api/v1/platform/demo/reset \
  -H "Authorization: Bearer <token>"
```

Or re-run in Render Shell: `SEED_MODULE=pitch python -m app.docker_migrate`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Login fails / network error | Check `vercel.json` / `netlify.toml` API URL; open DevTools → Network on `/api/v1/auth/login` |
| 502 / timeout on first load | Render free tier waking up — wait 60 s, retry |
| CORS error | `CORS_ORIGINS` on API must exactly match frontend URL (no trailing slash) |
| Empty DB | Run `python -m app.docker_migrate` in Render Shell |
| Proxy works locally not on Vercel | Ensure rewrite is **before** SPA fallback in `vercel.json` |

---

## Files in this repo

| File | Purpose |
|------|---------|
| `vercel.json` | Vercel build + `/api` proxy + SPA routes |
| `netlify.toml` | Netlify build + `/api` proxy + SPA routes |
| `render.yaml` | Render Blueprint (API + Postgres) |
| `.env.production.example` | Optional direct `VITE_API_BASE_URL` (skip proxy) |
| `src/lib/api.ts` | Uses `/api/v1` or `VITE_API_BASE_URL` |

---

## Cost notes (2026)

- **Vercel / Netlify** hobby: free subdomain, generous static hosting.
- **Render** free web service: spins down when idle; free Postgres may have limits — fine for pitch demo.
- For always-on demo without cold starts, use [DEMO_LIVE_DEPLOY.md](./DEMO_LIVE_DEPLOY.md) (VM + Docker) instead.
