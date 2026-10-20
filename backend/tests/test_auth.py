import pytest
from fastapi import HTTPException

from app import auth


def test_password_hash_is_salted_and_verifiable():
    first = auth._hash_password("correct horse battery staple")
    second = auth._hash_password("correct horse battery staple")

    assert first != second
    assert auth._verify_password("correct horse battery staple", first)
    assert not auth._verify_password("wrong password", first)


def test_token_round_trip_and_signature_validation(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-that-is-long-enough-123456")
    token = auth._issue_token(42, "person@example.com")

    claims = auth._read_token(token)
    assert claims["sub"] == "42"
    assert claims["email"] == "person@example.com"
    assert claims["exp"] > claims["iat"]

    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[:-1]}{'A' if signature[-1] != 'A' else 'B'}"
    with pytest.raises(HTTPException) as error:
        auth._read_token(tampered)
    assert error.value.status_code == 401


def test_expired_token_is_rejected(monkeypatch):
    import base64
    import hashlib
    import hmac
    import json
    import time

    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-that-is-long-enough-123456")
    header = auth._b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = auth._b64(json.dumps({"sub": "1", "email": "person@example.com", "iat": int(time.time()) - 20, "exp": int(time.time()) - 1}).encode())
    signing = f"{header}.{payload}".encode()
    signature = auth._b64(hmac.new(auth._secret(), signing, hashlib.sha256).digest())

    with pytest.raises(HTTPException) as error:
        auth._read_token(f"{header}.{payload}.{signature}")
    assert error.value.status_code == 401


def test_credentials_normalize_email_and_reject_short_password():
    credentials = auth.Credentials(email=" Person@Example.com ", password="a-long-enough-password")
    assert credentials.email == "person@example.com"

    with pytest.raises(ValueError):
        auth.Credentials(email="person@example.com", password="short")
