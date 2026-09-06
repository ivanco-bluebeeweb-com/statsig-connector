"""Extension declaration, capabilities, health check for Statsig Connector."""
from __future__ import annotations
import json
from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "statsig-connector",
    version="0.1.0",
    display_name="Statsig",
    icon="icon.svg",
    capabilities=["statsig:manage"],
    description="Official Imperal connector for Statsig (C30. Email Marketing & Newsletter). Manage operations securely."
)

chat = ChatExtension(ext)

@ext.health_check
async def health_check(ctx) -> dict:
    raw = await ctx.secrets.get("statsig_connections")
    try:
        count = len(json.loads(raw)) if raw else 0
    except Exception:
        count = 0
    return {
        "healthy": True,
        "detail": f"{count} Statsig connection(s) configured." if count else "Not connected yet."
    }
