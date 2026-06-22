"""Re-export — canonical implementation in app.domains.auth.router."""

from app.domains.auth.router import login, logout, refresh_token, router

__all__ = ["router", "login", "refresh_token", "logout"]
