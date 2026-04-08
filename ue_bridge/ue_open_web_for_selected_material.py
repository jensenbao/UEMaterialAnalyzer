"""UE-side helper script for opening the Streamlit analyzer from selected material.

Usage in Unreal Python console:

import ue_open_web_for_selected_material as launcher
launcher.open_web_for_selected_material()

You can bind this function to a plugin button/menu action.
"""

from __future__ import annotations

from urllib.parse import quote

import unreal


def _get_selected_material_asset_path() -> str:
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in assets:
        if isinstance(asset, unreal.Material):
            return asset.get_path_name()
    raise RuntimeError("No Material selected in Content Browser")


def open_web_for_selected_material(web_url: str = "http://127.0.0.1:8501") -> dict:
    material_path = _get_selected_material_asset_path()
    target_url = f"{web_url}?material_name={quote(material_path, safe='')}"
    unreal.SystemLibrary.launch_url(target_url)
    return {
        "ok": True,
        "material_path": material_path,
        "url": target_url,
    }


def open_web_home(web_url: str = "http://127.0.0.1:8501") -> dict:
    unreal.SystemLibrary.launch_url(web_url)
    return {
        "ok": True,
        "url": web_url,
    }
