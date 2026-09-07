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
async def list_gates(ctx, params: ListGateParams) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        raw_items = await client.list_gates(limit=params.limit)
        items = []
        for r in raw_items:
            rid = str(r.get("id") or r.get("name") or "unknown")
            rname = r.get("name") or rid
            items.append({
                "id": rid,
                "name": rname,
                "status": "enabled" if r.get("isEnabled") else "disabled",
                "created_at": str(r.get("createdTime") or r.get("createdAt") or ""),
                "raw": r
            })
        return ActionResult.success({"gates": items, "total": len(items)}, summary=f"Found {len(items)} gates.")
    except Exception as e:
        return ActionResult.error(f"Error listing gates: {e}")

@chat.function("get_gate", "Get details of one Gate in Statsig.", action_type="read", chain_callable=True, event="statsig-connector.get_gate", effects=["read:gate"], data_model=GateRecord)
async def get_gate(ctx, params: GetGateParams) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        r = await client.get_gate(params.gate_id)
        rid = str(r.get("id") or r.get("name") or params.gate_id)
        rname = r.get("name") or rid
        return ActionResult.success({
            "id": rid,
            "name": rname,
            "status": "enabled" if r.get("isEnabled") else "disabled",
            "created_at": str(r.get("createdTime") or r.get("createdAt") or ""),
            "raw": r
        }, summary=f"Retrieved Gate {rid}.")
    except Exception as e:
        return ActionResult.error(f"Error retrieving Gate: {e}")

@chat.function("audit_gate_health", "Audit health of Statsig gates and connectivity.", action_type="read", chain_callable=True, event="statsig-connector.audit_gate_health", effects=["read:audit"], data_model=AuditHealthReport)
async def audit_gate_health(ctx, params: ConnectionIdParams) -> ActionResult:
    client = await resolve_client(ctx, params.connection_id)
    try:
        items = await client.list_gates(limit=50)
        return ActionResult.success({
            "healthy": True,
            "total_gates": len(items),
            "details": {"sample_count": len(items)},
            "summary": f"Statsig healthy. Sampled {len(items)} gates."
        }, summary=f"Statsig health check passed with {len(items)} gates.")
    except Exception as e:
        return ActionResult.error(f"Error auditing Statsig health: {e}")
