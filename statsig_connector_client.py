"""HTTP client for Statsig API."""
from __future__ import annotations
import httpx
from typing import Any, Optional

DEFAULT_BASE = "https://statsigapi.net/console/v1"

class StatsigClient:
    def __init__(self, console_api_key: str, base_url: str = ""):
        self.console_api_key = console_api_key.strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_BASE).rstrip("/")
        self.headers = {
            "STATSIG-API-KEY": f"Bearer {self.console_api_key}" if "STATSIG-API-KEY" == "Authorization" else self.console_api_key,
            "Content-Type": "application/json",
            "User-Agent": "Imperal-Statsig-Connector/1.0.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def verify_auth(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(f"{self.base_url}/gates", headers=self.headers)
                if resp.status_code in (200, 201, 204):
                    return {"status": "ok", "data": resp.json() if resp.content else {}}
                return {"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    async def list_gates(self, limit: int = 20) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/gates", headers=self.headers, params={"limit": limit})
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list): return data
                for k in ["data", "gates", "items", "results"]:
                    if k in data and isinstance(data[k], list): return data[k]
                return []
            return []

    async def get_gate(self, gate_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/gates/{gate_id}", headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            raise ValueError(f"HTTP {resp.status_code}: {resp.text}")
