# pyright: reportMissingImports=false

"""UE-side HTTP bridge service for Streamlit analyzer.

Run inside Unreal Python environment.
"""

from __future__ import annotations

import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import unreal


def get_selected_material_name() -> str:
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in assets:
        if isinstance(asset, unreal.Material):
            return asset.get_path_name()
    raise RuntimeError("No Material selected in Content Browser")


def _get_material_expressions(material: unreal.Material) -> list:
    """Get material expression nodes with UE-version-compatible fallbacks."""
    # Preferred path for UE5.3+: read editor property directly.
    try:
        expressions = material.get_editor_property("expressions")
        if expressions:
            return list(expressions)
    except Exception:
        pass

    # Fallback: direct attribute access.
    try:
        expressions = getattr(material, "expressions", None)
        if expressions:
            return list(expressions)
    except Exception:
        pass

    # Fallback: expression_collection on material.
    try:
        expression_collection = material.get_editor_property("expression_collection")
        if expression_collection:
            expressions = expression_collection.get_editor_property("expressions")
            if expressions:
                return list(expressions)
    except Exception:
        pass

    # Fallback: editor_only_data -> expression_collection -> expressions.
    try:
        editor_only_data = material.get_editor_property("editor_only_data")
        if editor_only_data:
            expression_collection = editor_only_data.get_editor_property("expression_collection")
            if expression_collection:
                expressions = expression_collection.get_editor_property("expressions")
                if expressions:
                    return list(expressions)
    except Exception:
        pass

    # Optional fallback for engines that expose this helper.
    try:
        method = getattr(unreal.MaterialEditingLibrary, "get_material_expressions", None)
        if callable(method):
            expressions = method(material)
            if expressions:
                return list(expressions)
    except Exception:
        pass

    return []


def _material_to_graph(material: unreal.Material) -> dict:
    expressions = _get_material_expressions(material)
    nodes = []

    for idx, expr in enumerate(expressions):
        node_id = f"node_{idx + 1}"
        node_name = expr.get_name() if hasattr(expr, "get_name") else node_id
        node_type = expr.get_class().get_name() if hasattr(expr, "get_class") else "Unknown"

        nodes.append(
            {
                "id": node_id,
                "name": node_name,
                "type": node_type,
                "params": {},
            }
        )

    return {
        "material_name": material.get_name(),
        "nodes": nodes,
        "edges": [],
        "outputs": [],
    }


def export_selected_material_graph() -> dict:
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in assets:
        if isinstance(asset, unreal.Material):
            return _material_to_graph(asset)
    raise RuntimeError("No Material selected in Content Browser")


def export_material_graph_by_name(name: str) -> dict:
    asset = unreal.load_asset(name)
    if asset is None:
        raise RuntimeError(f"Material not found: {name}")
    if not isinstance(asset, unreal.Material):
        raise RuntimeError(f"Asset is not a Material: {name}")
    return _material_to_graph(asset)


_UE_BRIDGE_GLOBALS = {
    "unreal": unreal,
    "get_selected_material_name": get_selected_material_name,
    "export_selected_material_graph": export_selected_material_graph,
    "export_material_graph_by_name": export_material_graph_by_name,
}


class UEBridgeHandler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {"ok": True, "service": "ue-bridge"})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/run_python":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            request_data = json.loads(raw) if raw else {}
            code = request_data.get("code", "")

            local_vars = {}
            exec(code, _UE_BRIDGE_GLOBALS, local_vars)

            if "result" in local_vars:
                result = local_vars["result"]
                payload = result if isinstance(result, dict) else {"result": result}
            else:
                payload = {"ok": True}

            self._send_json(200, payload)
        except Exception as exc:
            self._send_json(
                500,
                {
                    "error": str(exc),
                    "trace": traceback.format_exc(),
                },
            )


def start_bridge(host: str = "127.0.0.1", port: int = 30010) -> dict:
    global _UE_BRIDGE_SERVER, _UE_BRIDGE_THREAD

    try:
        _UE_BRIDGE_SERVER.shutdown()
    except Exception:
        pass

    _UE_BRIDGE_SERVER = ThreadingHTTPServer((host, port), UEBridgeHandler)
    _UE_BRIDGE_THREAD = threading.Thread(target=_UE_BRIDGE_SERVER.serve_forever, daemon=True)
    _UE_BRIDGE_THREAD.start()

    message = f"UE Bridge started at http://{host}:{port}"
    unreal.log(message)
    return {"ok": True, "message": message}


def stop_bridge() -> dict:
    global _UE_BRIDGE_SERVER

    try:
        _UE_BRIDGE_SERVER.shutdown()
        _UE_BRIDGE_SERVER.server_close()
        unreal.log("UE Bridge stopped")
        return {"ok": True}
    except Exception:
        return {"ok": False, "message": "Bridge is not running"}


_UE_BRIDGE_SERVER = None
_UE_BRIDGE_THREAD = None
