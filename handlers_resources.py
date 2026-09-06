"""Resource handlers for Statsig Connector."""
from __future__ import annotations
from typing import Any
from imperal_sdk import ActionResult
from app import chat
from schemas import (
    ListGateParams, GetGateParams,
    GateRecord, GateList, AuditHealthReport, ConnectionIdParams
)
from handlers_connection import resolve_client

@chat.function("list_gates", "List gates in Statsig.", action_type="read", chain_callable=True, event="statsig-connector.list_gates", effects=["read:gates"], data_model=GateList)
async def list_gates(params: ListGateParams, ctx) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        raw_items = await client.list_gates(limit=params.limit)
        items = []
        for r in raw_items:
            rid = str(r.get("id") or r.get("key") or r.get("uuid") or "unknown")
            rname = r.get("name") or r.get("title") or r.get("label") or rid
            items.append({"id": rid, "name": rname, "status": r.get("status"), "created_at": r.get("createdAt") or r.get("created_at"), "raw": r})
        return ActionResult.ok({"gates": items, "total": len(items)}, summary=f"Found {len(items)} gates.")
    except Exception as e:
        return ActionResult.error(f"Error listing gates: {e}")

@chat.function("get_gate", "Get details of one Gate in Statsig.", action_type="read", chain_callable=True, event="statsig-connector.get_gate", effects=["read:gate"], data_model=GateRecord)
async def get_gate(params: GetGateParams, ctx) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        r = await client.get_gate(params.gate_id)
        rid = str(r.get("id") or params.gate_id)
        rname = r.get("name") or r.get("title") or rid
        return ActionResult.ok({"id": rid, "name": rname, "status": r.get("status"), "created_at": r.get("createdAt") or r.get("created_at"), "raw": r}, summary=f"Retrieved Gate {rid}.")
    except Exception as e:
        return ActionResult.error(f"Error retrieving Gate: {e}")

@chat.function("audit_gate_health", "Audit health of Statsig gates and connectivity.", action_type="read", chain_callable=True, event="statsig-connector.audit_gate_health", effects=["read:audit"], data_model=AuditHealthReport)
async def audit_gate_health(params: ConnectionIdParams, ctx) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        items = await client.list_gates(limit=50)
        return ActionResult.ok({
            "healthy": True,
            "total_gates": len(items),
            "details": {"sample_count": len(items)},
            "summary": f"Statsig healthy. Sampled {len(items)} gates."
        }, summary=f"Statsig health check passed with {len(items)} gates.")
    except Exception as e:
        return ActionResult.error(f"Error auditing Statsig health: {e}")
