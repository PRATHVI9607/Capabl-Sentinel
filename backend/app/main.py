"""FastAPI application: CORS, rate limiting, security headers, routes, startup."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .api import analyze, health, history, tools
from .cache import client as cache
from .config import settings
from .db.session import init_models

logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 3600
_RATE_LIMITED_ROUTES = {("POST", "/analyze")}

# The API serves JSON and an event stream to a separate origin. It sets no
# cookies and embeds nothing, so everything here can be locked down.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_models()
    logger.info("SENTINEL %s ready in %s mode", __version__, settings.environment)
    if settings.is_production and not settings.cors_origin_list:
        logger.warning("CORS_ORIGINS is empty in production; no browser origin can call this API.")
    yield


app = FastAPI(
    title="SENTINEL",
    description="Safety ENTRy INcident Threat Early-warning Layer",
    version=__version__,
    lifespan=lifespan,
    # The interactive docs load scripts from a CDN, which the CSP above blocks.
    # They stay available outside production, where they are genuinely useful.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # No cookies or Authorization header are used, so credentials stay off.
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=600,
)


def client_ip(request: Request) -> str:
    """The caller's address, trusting proxy headers only when configured to."""
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if first_hop := forwarded.split(",")[0].strip():
            return first_hop
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Per-IP hourly cap on uploads. Reads and analysis streams are never limited."""
    if (request.method, request.url.path) not in _RATE_LIMITED_ROUTES:
        return await call_next(request)

    # The address reaches a URL path in the cache client, so it is escaped here.
    key = f"ratelimit:{quote(client_ip(request), safe='')}"
    count = await cache.incr_with_expiry(key, RATE_LIMIT_WINDOW_SECONDS)
    if count > settings.max_analyses_per_ip_per_hour:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Try again in an hour."},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
        )
    return await call_next(request)


app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(history.router)
app.include_router(tools.router)
