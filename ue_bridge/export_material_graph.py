from __future__ import annotations

import json
from typing import Any

from ue_bridge.remote_exec_client import UERemoteExecClient


def get_selected_material_name(client: UERemoteExecClient | None = None) -> str:
    ue = client or UERemoteExecClient()
    payload = ue.run_python("result = get_selected_material_name()")

    name = payload.get("material_name")
    if not isinstance(name, str):
        result_name = payload.get("result")
        if isinstance(result_name, str):
            name = result_name

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Failed to get selected material name from UE")
    return name


def export_selected_material_graph(client: UERemoteExecClient | None = None) -> dict[str, Any]:
    ue = client or UERemoteExecClient()
    payload = ue.run_python("result = export_selected_material_graph()")

    result_payload = payload.get("result", payload)

    if not isinstance(result_payload, dict):
        raise ValueError("UE export payload is invalid")
    return result_payload


def export_material_graph_by_name(
    name: str,
    client: UERemoteExecClient | None = None,
) -> dict[str, Any]:
    if not name.strip():
        raise ValueError("Material name cannot be empty")

    ue = client or UERemoteExecClient()
    payload = ue.run_python(f"result = export_material_graph_by_name({json.dumps(name)})")

    result_payload = payload.get("result", payload)

    if not isinstance(result_payload, dict):
        raise ValueError("UE export payload is invalid")
    return result_payload
