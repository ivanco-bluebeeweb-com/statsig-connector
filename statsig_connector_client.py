"""HTTP client for Statsig Console API."""
from __future__ import annotations
import httpx
from typing import Any, Optional

DEFAULT_BASE = "https://statsigapi.net/console/v1"

class StatsigClient:
    def __init__(self, console_api_key: str, base_url: str = ""):
        self.console_api_key = console_api_key.strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_BASE).rstrip("/")
        self.headers = {
            "STATSIG-API-KEY": self.console_api_key,
            "Content-Type": "application/json",
            "User-Agent": "Imperal-Statsig-Connector/1.0.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def verify_auth(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(f"{self.base_url}/gates", headers=self.headers, params={"limit": 1})
                if resp.status_code in (200, 201, 204):
                    return {"status": "ok", "data": resp.json() if resp.content else {}}
                return {"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    async def list_gates(self, limit: int = 20) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/gates", headers=self.headers, params={"limit": limit})
            if resp.status_code == 200:
                body = resp.json()
                if isinstance(body, dict):
                    data = body.get("data", [])
                    if isinstance(data, list):
                        return data
                elif isinstance(body, list):
                    return body
                return []
            return []

    async def get_gate(self, gate_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/gates/{gate_id}", headers=self.headers)
            if resp.status_code == 200:
                body = resp.json()
                if isinstance(body, dict) and "data" in body and isinstance(body["data"], dict):
                    return body["data"]
                return body if isinstance(body, dict) else {"id": gate_id, "raw": body}
            raise ValueError(f"HTTP {resp.status_code}: {resp.text}")

    async def create_gate(self, name: str, description: str = "", is_enabled: bool = True) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "name": name,
                "description": description or f"Gate {name}",
                "isEnabled": is_enabled,
                "rules": [{"name": "All Users", "passPercentage": 100, "conditions": []}]
            }
            resp = await client.post(f"{self.base_url}/gates", headers=self.headers, json=payload)
            if resp.status_code in (200, 201):
                body = resp.json()
                if isinstance(body, dict) and "data" in body:
                    return body["data"]
                return body if isinstance(body, dict) else {"id": name}
            raise ValueError(f"HTTP {resp.status_code}: {resp.text}")

    async def delete_gate(self, gate_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(f"{self.base_url}/gates/{gate_id}", headers=self.headers)
            if resp.status_code in (200, 204):
                return True
            raise ValueError(f"HTTP {resp.status_code}: {resp.text}")
