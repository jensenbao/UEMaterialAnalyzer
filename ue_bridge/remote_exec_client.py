from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request
from typing import Any


@dataclass(slots=True)
class RemoteExecConfig:
    base_url: str = "http://127.0.0.1:30010"
    timeout_sec: float = 15.0


class UERemoteExecClient:
    """Minimal HTTP client for UE Python remote execution bridge.

    This expects a UE-side bridge service that accepts Python code or commands
    and returns JSON payloads.
    """

    def __init__(self, config: RemoteExecConfig | None = None) -> None:
        self.config = config or RemoteExecConfig()

    def health_check(self) -> bool:
        try:
            req = request.Request(f"{self.config.base_url}/health", method="GET")
            with request.urlopen(req, timeout=self.config.timeout_sec) as resp:
                return resp.status == 200
        except (error.URLError, TimeoutError):
            return False

    def run_python(self, code: str) -> dict[str, Any]:
        body = json.dumps({"code": code}).encode("utf-8")
        req = request.Request(
            f"{self.config.base_url}/run_python",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_sec) as resp:
                raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("UE remote response is not a JSON object")
            return payload
        except error.HTTPError as exc:
            details = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
                details = f" | body={body}"
            except Exception:
                details = ""
            raise RuntimeError(
                f"UE remote request failed: HTTP {exc.code} {exc.reason}{details}"
            ) from exc
        except (error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"UE remote request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("UE remote response is not valid JSON") from exc
