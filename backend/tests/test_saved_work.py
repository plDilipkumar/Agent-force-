import asyncio
import json
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app import saved_work


class FakeConnection:
    def __init__(self):
        self.fetch_query = ""
        self.fetch_args = ()
        self.execute_query = ""
        self.execute_args = ()
        self.rows = []
        self.status = "DELETE 1"

    async def fetch(self, query, *args):
        self.fetch_query, self.fetch_args = query, args
        return self.rows

    async def execute(self, query, *args):
        self.execute_query, self.execute_args = query, args
        return self.status


class Acquire:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, *args):
        return False


class FakePool:
    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return Acquire(self.connection)


def test_list_saved_work_is_scoped_to_authenticated_user(monkeypatch):
    conn = FakeConnection()
    conn.rows = [{
        "item_id": "plan-1",
        "item_type": "plan",
        "payload": {"summary": "Demo"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }]
    monkeypatch.setattr(saved_work, "get_pool", lambda: FakePool(conn))

    result = asyncio.run(saved_work.list_saved_work({"id": 17, "email": "a@example.com"}))

    assert conn.fetch_args == (17,)
    assert "WHERE user_id=$1" in conn.fetch_query
    assert result["items"][0]["payload"]["summary"] == "Demo"


def test_save_item_upserts_only_for_authenticated_user(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(saved_work, "get_pool", lambda: FakePool(conn))

    result = asyncio.run(saved_work.save_item(
        "plan", "plan-2", {"summary": "Saved"},
        {"id": 23, "email": "b@example.com"},
    ))

    assert result == {"saved": True, "item_id": "plan-2", "item_type": "plan"}
    assert conn.execute_args[:3] == (23, "plan-2", "plan")
    assert "ON CONFLICT(user_id, item_id, item_type)" in conn.execute_query


def test_save_item_rejects_invalid_type(monkeypatch):
    monkeypatch.setattr(saved_work, "get_pool", lambda: FakePool(FakeConnection()))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(saved_work.save_item("other", "item-1", {}, {"id": 1}))
    assert exc.value.status_code == 422


def test_save_item_rejects_oversized_payload(monkeypatch):
    monkeypatch.setattr(saved_work, "get_pool", lambda: FakePool(FakeConnection()))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(saved_work.save_item("plan", "item-1", {"text": "x" * 1_000_001}, {"id": 1}))
    assert exc.value.status_code == 413


def test_delete_item_is_scoped_to_authenticated_user(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(saved_work, "get_pool", lambda: FakePool(conn))

    result = asyncio.run(saved_work.delete_item("artifact", "artifact-1", {"id": 31}))

    assert result == {"deleted": True}
    assert conn.execute_args == (31, "artifact-1", "artifact")
    assert "WHERE user_id=$1 AND item_id=$2 AND item_type=$3" in conn.execute_query


def test_delete_item_reports_missing_record(monkeypatch):
    conn = FakeConnection()
    conn.status = "DELETE 0"
    monkeypatch.setattr(saved_work, "get_pool", lambda: FakePool(conn))

    result = asyncio.run(saved_work.delete_item("plan", "missing", {"id": 31}))

    assert result == {"deleted": False}
