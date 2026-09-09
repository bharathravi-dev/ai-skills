"""FastAPI application: validation, authorization, error translation.

M2-L15. Run with:
    uvicorn ticketapi.main:app --reload
"""

from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ticketapi import db, services
from ticketapi.config import Principal, Settings, load_settings
from ticketapi.errors import NoChangesRequested, NotAuthorized, TicketNotFound
from ticketapi.models import ErrorResponse, TicketCreate, TicketOut, TicketUpdate

logger = logging.getLogger("ticketapi")

_state: dict[str, object] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared resources ONCE at startup (M2-L15 section 5.6)."""
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    )
    _state["settings"] = settings
    _state["conn"] = db.connect(settings.database_path)
    logger.info("startup", extra={"app_env": settings.app_env})
    yield
    conn = _state.get("conn")
    if isinstance(conn, sqlite3.Connection):
        conn.close()
    _state.clear()


app = FastAPI(title="Ticket API", version="0.1.0", lifespan=lifespan)


# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------
def get_settings() -> Settings:
    settings = _state.get("settings")
    if not isinstance(settings, Settings):
        raise RuntimeError("settings not initialised")
    return settings


def get_db() -> Iterator[sqlite3.Connection]:
    conn = _state.get("conn")
    if not isinstance(conn, sqlite3.Connection):
        raise RuntimeError("database not initialised")
    yield conn


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def current_principal(
    authorization: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Authentication. 401 = we do not know who you are (M2-L11)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    principal = settings.tokens.get(authorization[7:].strip())
    if principal is None:
        raise HTTPException(401, "invalid token")
    return principal


def require_admin(
    principal: Principal = Depends(current_principal),
) -> Principal:
    """Authorization. 403 = we know you, and you may not (M2-L11)."""
    if not principal.is_admin:
        raise HTTPException(403, "admin role required")
    return principal


# --------------------------------------------------------------------------
# Middleware and error handlers
# --------------------------------------------------------------------------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    # Log metadata only: never the body (M2-L18).
    logger.info(
        "request_completed",
        extra={"request_id": request_id, "method": request.method,
               "path": request.url.path, "status": response.status_code,
               "duration_ms": round((time.perf_counter() - started) * 1000)},
    )
    response.headers["X-Request-ID"] = request_id
    return response


def _error(status: int, detail: str, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(
            detail=detail, request_id=get_request_id(request)
        ).model_dump(),
    )


@app.exception_handler(TicketNotFound)
async def handle_not_found(request: Request, exc: TicketNotFound) -> JSONResponse:
    return _error(404, "ticket not found", request)


@app.exception_handler(NotAuthorized)
async def handle_not_authorized(request: Request, exc: NotAuthorized) -> JSONResponse:
    # Deliberately 404 for ticket access, so we do not confirm existence.
    if exc.action == "read this ticket":
        return _error(404, "ticket not found", request)
    return _error(403, str(exc), request)


@app.exception_handler(NoChangesRequested)
async def handle_no_changes(request: Request, exc: NoChangesRequested) -> JSONResponse:
    return _error(422, str(exc), request)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(
    payload: TicketCreate,
    request: Request,
    principal: Principal = Depends(current_principal),
    conn: sqlite3.Connection = Depends(get_db),
) -> TicketOut:
    ticket = services.create_ticket(
        conn, payload, principal, request_id=get_request_id(request)
    )
    return TicketOut.model_validate(ticket.model_dump())


@app.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    request: Request,
    principal: Principal = Depends(current_principal),
    conn: sqlite3.Connection = Depends(get_db),
    status: str | None = Query(default=None, pattern="^(open|pending|resolved)$"),
    sort: str = Query(default="created_at"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TicketOut]:
    try:
        tickets = services.list_tickets(
            conn, principal, status=status, sort=sort, limit=limit, offset=offset
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [TicketOut.model_validate(t.model_dump()) for t in tickets]


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    request: Request,
    principal: Principal = Depends(current_principal),
    conn: sqlite3.Connection = Depends(get_db),
) -> TicketOut:
    ticket = services.get_ticket(
        conn, ticket_id, principal, request_id=get_request_id(request)
    )
    return TicketOut.model_validate(ticket.model_dump())


@app.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    request: Request,
    principal: Principal = Depends(current_principal),
    conn: sqlite3.Connection = Depends(get_db),
) -> TicketOut:
    ticket = services.update_ticket(
        conn, ticket_id, payload, principal, request_id=get_request_id(request)
    )
    return TicketOut.model_validate(ticket.model_dump())


@app.get("/admin/stats")
def admin_stats(
    principal: Principal = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, int]:
    return {"total_tickets": db.count_for(conn, owner_id=None)}
