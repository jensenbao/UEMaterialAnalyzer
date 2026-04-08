import json
from pathlib import Path

import streamlit as st

from data_models.material_graph import MaterialGraph
from parser.paste_text_parser import parse_paste_text_to_graph
from parser.ue_api_parser import parse_ue_api_payload
from ue_bridge.export_material_graph import (
    export_material_graph_by_name,
    export_selected_material_graph,
)


st.set_page_config(page_title="UE AI Material Analyzer", layout="wide")
st.title("UE AI Material Analyzer (MVP)")
query_material_name = st.query_params.get("material_name", "")

sample_path = Path("samples/sample_graph_01.json")
case_text_path = Path("材质案例/M_ShockWave.txt")


def show_graph(graph: MaterialGraph) -> None:
    data = graph.to_dict()
    stats = data["stats"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Material", data["material_name"])
    c2.metric("Nodes", stats["node_count"])
    c3.metric("Edges", stats["edge_count"])
    c4.metric("Outputs", stats["output_count"])

    st.subheader("Nodes")
    st.dataframe(data["nodes"], use_container_width=True)

    st.subheader("Edges")
    st.dataframe(data["edges"], use_container_width=True)

    st.subheader("Outputs")
    st.dataframe(data["outputs"], use_container_width=True)

if st.button("Load sample graph"):
    if not sample_path.exists():
        st.error("Sample file not found: samples/sample_graph_01.json")
    else:
        with sample_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            graph = MaterialGraph.from_dict(data)
            st.success("Sample graph loaded and validated")
            show_graph(graph)
        except Exception as exc:
            st.error(f"Validation failed: {exc}")

if st.button("Load from UE Live"):
    try:
        raw_payload = export_selected_material_graph()
        graph = parse_ue_api_payload(raw_payload)
        st.success("UE Live graph loaded and validated")
        show_graph(graph)
    except Exception as exc:
        st.error(f"UE Live load failed: {exc}")

if query_material_name:
    st.info(f"Material from UE selection: {query_material_name}")
    if st.button("Load from Query Material"):
        try:
            raw_payload = export_material_graph_by_name(query_material_name)
            graph = parse_ue_api_payload(raw_payload)
            st.success("UE material loaded by query name")
            show_graph(graph)
        except Exception as exc:
            st.error(f"UE query load failed: {exc}")

st.subheader("Paste UE Node Text (Fallback)")

default_text = ""
if case_text_path.exists():
    default_text = case_text_path.read_text(encoding="utf-8")

paste_text = st.text_area(
    "Paste copied material node text from UE",
    value=default_text,
    height=280,
)

paste_material_name = st.text_input("Material name for pasted text", value="M_Pasted")

if st.button("Parse Pasted Text"):
    if not paste_text.strip():
        st.error("Paste text is empty")
    else:
        try:
            graph = parse_paste_text_to_graph(paste_text, material_name=paste_material_name)
            st.success("Pasted text parsed and validated")
            show_graph(graph)
        except Exception as exc:
            st.error(f"Paste text parse failed: {exc}")

st.caption("Next: connect UE Live export and normalize parser output")
