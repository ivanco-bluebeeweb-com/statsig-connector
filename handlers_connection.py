"""Connection management for Statsig Connector."""
from __future__ import annotations
import uuid, json
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import NoParams, ConnectParams, ConnectionIdParams, ConnectionRecord, ConnectionList, DeleteResult
from statsig_connector_client import StatsigClient

_SECRET = "statsig_connector_connections"

def _mask(v: str) -> str:
    return v[:4] + "…" + v[-4:] if len(v) > 8 else "***"

async def _load_conns(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw: return []
    try: data = json.loads(raw)
    except: return []
    return data if isinstance(data, list) else []

async def _save_conns(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))

async def resolve_client(ctx, connection_id: str = "") -> StatsigClient:
    conns = await _load_conns(ctx)
    if not conns:
        raise ValueError("No Statsig connections configured. Use connect_statsig_connector first.")
    conn = conns[0]
    if connection_id:
        for c in conns:
            if c["id"] == connection_id:
                conn = c
                break
    return StatsigClient(console_api_key=conn["console_api_key"], base_url=conn.get("base_url", ""))

@chat.function("connect_statsig_connector", "Connect Statsig account via credentials.", action_type="write", chain_callable=True, event="statsig-connector.connect_statsig_connector", effects=["create:connection"], data_model=ConnectionRecord)
async def connect_statsig_connector(params: ConnectParams, ctx) -> ActionResult:
    client = StatsigClient(console_api_key=params.console_api_key, base_url=params.base_url)
    res = await client.verify_auth()
    if res.get("status") == "error":
        return ActionResult.error(f"Failed to connect to Statsig: {res.get('error')}")
    conns = await _load_conns(ctx)
    cid = f"conn_{uuid.uuid4().hex[:8]}"
    rec = {
        "id": cid,
        "label": params.label or "Primary Statsig",
        "console_api_key": params.console_api_key,
        "masked_key": _mask(params.console_api_key),
        "base_url": params.base_url,
        "is_active": True
    }
    for c in conns: c["is_active"] = False
    conns.append(rec)
    await _save_conns(ctx, conns)
    return ActionResult.ok(rec, summary=f"Connected Statsig ({rec['label']}).")

@chat.function("list_connections", "List configured Statsig connections.", action_type="read", chain_callable=True, event="statsig-connector.list_connections", effects=["read:connections"], data_model=ConnectionList)
async def list_connections(params: NoParams, ctx) -> ActionResult:
    conns = await _load_conns(ctx)
    items = [{
        "id": c["id"],
        "label": c["label"],
        "masked_key": c.get("masked_key", "***"),
        "base_url": c.get("base_url", "https://statsigapi.net/console/v1"),
        "is_active": c.get("is_active", False)
    } for c in conns]
    return ActionResult.ok({"connections": items, "total": len(items)}, summary=f"Found {len(items)} connection(s).")

@chat.function("disconnect_statsig_connector", "Disconnect Statsig account and delete stored credentials.", action_type="destructive", chain_callable=True, event="statsig-connector.disconnect_statsig_connector", effects=["delete:connection"], data_model=DeleteResult)
async def disconnect_statsig_connector(params: ConnectionIdParams, ctx) -> ActionResult:
    conns = await _load_conns(ctx)
    if not conns:
        return ActionResult.error("No connections to disconnect.")
    if params.connection_id:
        conns = [c for c in conns if c["id"] != params.connection_id]
    else:
        conns.clear()
    await _save_conns(ctx, conns)
    return ActionResult.ok({"success": True, "message": "Disconnected successfully."}, summary="Disconnected Statsig connection.")
