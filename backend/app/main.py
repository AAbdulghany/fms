from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, assets, billing_actions, catalog, clients, invoices, reports, sites, templates, users, work_orders
from app.config import get_settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = settings.api_v1_prefix
app.include_router(auth.router, prefix=api)
app.include_router(users.router, prefix=api)
app.include_router(clients.router, prefix=api)
app.include_router(sites.router, prefix=api)
app.include_router(assets.router, prefix=api)
app.include_router(templates.router, prefix=api)
app.include_router(work_orders.router, prefix=api)
app.include_router(reports.router, prefix=api)
app.include_router(invoices.router, prefix=api)
app.include_router(billing_actions.router, prefix=api)
app.include_router(catalog.router, prefix=api)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
