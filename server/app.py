"""Minimal FastAPI health endpoint for uptime probing."""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

VERSION = "0.1.0"

app = FastAPI(title="Healthcheck", version=VERSION)


def _utc_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_bearer(authorization: str | None) -> None:
    expected = os.environ.get("HEALTHCHECK_TOKEN")
    if not expected:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="invalid_token")


@app.get("/health")
def health(authorization: str | None = Header(default=None)) -> JSONResponse:
    _require_bearer(authorization)
    body = {
        "status": "ok",
        "time": _utc_iso_z(),
        "hostname": socket.gethostname(),
        "version": VERSION,
    }
    return JSONResponse(content=body, status_code=200)


@app.get("/health/ready")
def ready(authorization: str | None = Header(default=None)) -> JSONResponse:
    """Readiness probe; extend with DB checks when needed."""
    _require_bearer(authorization)
    return health(authorization)  # type: ignore[return-value]


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("server.app:app", host=host, port=port, factory=False, reload=False)
