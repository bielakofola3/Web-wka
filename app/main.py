from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette_csrf import CSRFMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

load_dotenv()

from .models import init_db
from .routes import router

app = FastAPI(title="MycoForum", docs_url=None, redoc_url=None)  # Wyłączone docs w prod

# Sekrety z env (nigdy w kodzie)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-strong-random")
CSRF_SECRET = os.getenv("CSRF_SECRET", SECRET_KEY)

# Sesje: Secure, HttpOnly, SameSite
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="myco_session",
    max_age=3600,  # 1h
    same_site="lax",
    https_only=True,  # W prod True; lokalnie ustaw False jeśli HTTP
    path="/",
)

# CSRF
app.add_middleware(CSRFMiddleware, secret=CSRF_SECRET)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(router)

@app.on_event("startup")
def startup():
    init_db()

# Redirect HTTP→HTTPS jeśli za proxy (w prod ustawić)
@app.middleware("http")
async def https_redirect(request: Request, call_next):
    if os.getenv("FORCE_HTTPS", "false").lower() == "true":
        if request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url, status_code=301)
    return await call_next(request)
