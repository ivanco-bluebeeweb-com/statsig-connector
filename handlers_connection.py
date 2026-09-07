"""Connection management for Statsig Connector."""
from __future__ import annotations
import uuid
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import NoParams, ConnectParams, ConnectionIdParams, ConnectionRecord, ConnectionList, DeleteResult
from statsig_connector_client import StatsigClient

_COLLECTION = "connections"

def _mask(v: str) -> str:
    if not v:
        return "******"
    if len(v) <= 4:
        return "******"
    return v[:2] + "******" + v[-2:]

async def _load_conns(ctx) -> list[dict]:
    res = await ctx.store.query(_COLLECTION)
    items = []
    if hasattr(res, "data"):
        for doc in res.data:
            d = dict(doc.data) if hasattr(doc, "data") else dict(doc)
            d["id"] = getattr(doc, "id", d.get("id"))
            items.append(d)
    elif isinstance(res, list):
        for doc in res:
            d = dict(doc.data) if hasattr(doc, "data") else dict(doc)
            items.append(d)
    return items

async def resolve_client(ctx, connection_id: str = "") -> StatsigClient:
    conns = await _load_conns(ctx)
    if not conns:
        raise ValueError("No Statsig connections configured. Use connect_statsig_connector first.")
    conn = conns[0]
    if connection_id:
        for c in conns:
            if c.get("id") == connection_id:
                conn = c
                break
    return StatsigClient(console_api_key=conn["console_api_key"], base_url=conn.get("base_url", ""))

@chat.function("connect_statsig_connector", "Connect Statsig account via credentials.", action_type="write", chain_callable=True, event="statsig-connector.connect_statsig_connector", effects=["create:connection"], data_model=ConnectionRecord)
async def connect_statsig_connector(ctx, params: ConnectParams) -> ActionResult:
    client = StatsigClient(console_api_key=params.console_api_key, base_url=params.base_url)
    res = await client.verify_auth()
    if res.get("status") == "error":
        return ActionResult.error(f"Failed to connect to Statsig: {res.get('error')}")
    
    cid = f"conn_{uuid.uuid4().hex[:8]}"
    rec = {
        "id": cid,
        "label": params.label or "Primary Statsig",
        "console_api_key": params.console_api_key,
        "masked_key": _mask(params.console_api_key),
        "base_url": params.base_url or "https://statsigapi.net/console/v1",
        "is_active": True
    }
    
    # Inactivate older connections
    existing = await _load_conns(ctx)
    for c in existing:
        if c.get("is_active"):
            c_update = dict(c)
            c_update["is_active"] = False
            await ctx.store.create(_COLLECTION, c_update, id=c["id"])
            
    await ctx.store.create(_COLLECTION, rec, id=cid)
    safe_rec = {
        "id": cid,
        "label": rec["label"],
        "masked_key": rec["masked_key"],
        "base_url": rec["base_url"],
        "is_active": True
    }
    return ActionResult.success(safe_rec, summary=f"Connected Statsig ({rec['label']}).")

@chat.function("list_connections", "List configured Statsig connections.", action_type="read", chain_callable=True, event="statsig-connector.list_connections", effects=["read:connections"], data_model=ConnectionList)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    conns = await _load_conns(ctx)
    items = [{
        "id": c["id"],
        "label": c.get("label", "Statsig"),
        "masked_key": c.get("masked_key") or _mask(c.get("console_api_key", "")),
        "base_url": c.get("base_url", "https://statsigapi.net/console/v1"),
        "is_active": c.get("is_active", False)
    } for c in conns]
    return ActionResult.success({"connections": items, "total": len(items)}, summary=f"Found {len(items)} connection(s).")

@chat.function("disconnect_statsig_connector", "Disconnect Statsig account and delete stored credentials.", action_type="destructive", chain_callable=True, event="statsig-connector.disconnect_statsig_connector", effects=["delete:connection"], data_model=DeleteResult)
async def disconnect_statsig_connector(ctx, params: ConnectionIdParams) -> ActionResult:
    conns = await _load_conns(ctx)
    if not conns:
        return ActionResult.error("No connections to disconnect.")
    
    if params.connection_id:
        target_ids = [c["id"] for c in conns if c["id"] == params.connection_id]
    else:
        target_ids = [c["id"] for c in conns]
        
    for doc_id in target_ids:
        await ctx.store.delete(_COLLECTION, doc_id)
        
    return ActionResult.success({"success": True, "message": "Disconnected successfully."}, summary="Disconnected Statsig connection.")
