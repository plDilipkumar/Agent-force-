from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import get_pool, require_user

router = APIRouter(prefix="/api/saved-work", tags=["saved work"])

class SavedItem(BaseModel):
    item_id: str = Field(min_length=1, max_length=160)
    item_type: str = Field(pattern="^(plan|artifact)$")
    payload: dict[str, Any]

@router.get("")
async def list_saved_work(user: dict = Depends(require_user)) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT item_id, item_type, payload, created_at, updated_at FROM agentforge_saved_work WHERE user_id=$1 ORDER BY updated_at DESC LIMIT 200",
            user["id"],
        )
    items = []
    for row in rows:
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        items.append({"item_id": row["item_id"], "item_type": row["item_type"], "payload": payload,
                      "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()})
    return {"items": items}

@router.put("/{item_type}/{item_id}")
async def save_item(item_type: str, item_id: str, body: dict[str, Any], user: dict = Depends(require_user)) -> dict:
    if item_type not in {"plan", "artifact"} or not item_id or len(item_id) > 160:
        raise HTTPException(422, "Invalid saved item.")
    if len(json.dumps(body, ensure_ascii=False)) > 1_000_000:
        raise HTTPException(413, "This saved item is too large.")
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO agentforge_saved_work(user_id, item_id, item_type, payload, created_at, updated_at)
            VALUES($1, $2, $3, $4::jsonb, NOW(), NOW())
            ON CONFLICT(user_id, item_id, item_type)
            DO UPDATE SET payload=EXCLUDED.payload, updated_at=NOW()
        """, user["id"], item_id, item_type, json.dumps(body, ensure_ascii=False))
    return {"saved": True, "item_id": item_id, "item_type": item_type}

@router.delete("/{item_type}/{item_id}")
async def delete_item(item_type: str, item_id: str, user: dict = Depends(require_user)) -> dict:
    if item_type not in {"plan", "artifact"}:
        raise HTTPException(422, "Invalid saved item type.")
    pool = get_pool()
    async with pool.acquire() as conn:
        status = await conn.execute("DELETE FROM agentforge_saved_work WHERE user_id=$1 AND item_id=$2 AND item_type=$3", user["id"], item_id, item_type)
    return {"deleted": status.endswith("1")}
