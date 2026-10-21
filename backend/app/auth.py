from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from urllib.parse import urlparse, parse_qs, unquote

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/auth", tags=["authentication"])
_bearer = HTTPBearer(auto_error=False)
_pool: asyncpg.Pool | None = None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _secret() -> bytes:
    value = os.getenv("AUTH_SECRET_KEY", "").strip()
    if len(value) < 32:
        raise RuntimeError("AUTH_SECRET_KEY must be configured with at least 32 characters.")
    return value.encode("utf-8")


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt\u0024{_b64(salt)}\u0024{_b64(digest)}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_text, digest_text = stored.split("$", 2)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _issue_token(user_id: int, email: str) -> str:
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user_id), "email": email, "iat": now, "exp": now + 60 * 60 * 24 * 7}, separators=(",", ":")).encode())
    signing = f"{header}.{payload}".encode()
    signature = _b64(hmac.new(_secret(), signing, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def _read_token(token: str) -> dict:
    try:
        header, payload, signature = token.split(".")
        header_data = json.loads(base64.urlsafe_b64decode(header + "=" * (-len(header) % 4)))
        # Do not accept tokens that declare an unexpected algorithm or token type.
        if not isinstance(header_data, dict) or header_data.get("alg") != "HS256" or header_data.get("typ") != "JWT":
            raise ValueError("header")
        signing = f"{header}.{payload}".encode()
        expected = _b64(hmac.new(_secret(), signing, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if not isinstance(data, dict) or int(data.get("exp", 0)) <= int(time.time()):
            raise ValueError("expired")
        return data
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(401, "Your session is invalid or expired. Please sign in again.")


async def init_auth_db() -> None:
    global _pool
    if os.getenv("AGENTFORGE_TESTING") == "1":
        return
    _secret()
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL must be configured for AgentForge authentication.")
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path:
        raise RuntimeError("DATABASE_URL must be a valid PostgreSQL connection URL.")
    sslmode = parse_qs(parsed.query).get("sslmode", ["require"])[0]
    _pool = await asyncpg.create_pool(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        database=parsed.path.lstrip("/"),
        ssl="require" if sslmode != "disable" else False,
        min_size=1,
        max_size=5,
        command_timeout=15,
    )
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agentforge_users (
                id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


async def close_auth_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise HTTPException(503, "Account storage is not ready. Please try again shortly.")
    return _pool


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@") or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        return value


class UserView(BaseModel):
    id: int
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserView


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: Credentials) -> dict:
    pool = get_pool()
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO agentforge_users(email, password_hash) VALUES($1, $2) RETURNING id, email",
                body.email, _hash_password(body.password),
            )
    except asyncpg.UniqueViolationError:
        raise HTTPException(409, "An account with this email already exists. Please sign in.")
    token = _issue_token(row["id"], row["email"])
    return {"access_token": token, "user": {"id": row["id"], "email": row["email"]}}


@router.post("/login", response_model=AuthResponse)
async def login(body: Credentials) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, email, password_hash FROM agentforge_users WHERE email = $1", body.email)
    if row is None or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    token = _issue_token(row["id"], row["email"])
    return {"access_token": token, "user": {"id": row["id"], "email": row["email"]}}


async def require_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if os.getenv("AGENTFORGE_TESTING") == "1":
        return {"id": 1, "email": "test@example.com"}
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Please log in to use AgentForge AI.")
    claims = _read_token(credentials.credentials)
    try:
        user_id = int(claims["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(401, "Your session is invalid or expired. Please sign in again.")
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, email FROM agentforge_users WHERE id = $1", user_id)
    if row is None:
        raise HTTPException(401, "Your account is no longer available. Please sign in again.")
    return {"id": row["id"], "email": row["email"]}


@router.get("/me", response_model=UserView)
async def me(user: dict = Depends(require_user)) -> dict:
    return user
