from __future__ import annotations

import re

from data_models.material_graph import MaterialEdge, MaterialGraph, MaterialNode, MaterialOutput

_NODE_BEGIN_RE = re.compile(
    r'^Begin Object Class=/Script/UnrealEd\.MaterialGraphNode(?:_Root)?\s+Name="([^"]+)"'
)
_EXPR_CLASS_RE = re.compile(
    r'^\s*Begin Object Class=/Script/Engine\.([A-Za-z0-9_]+)\s+Name="([^"]+)"'
)
_PIN_RE = re.compile(
    r'CustomProperties Pin \((.*)\)'
)
_PIN_NAME_RE = re.compile(r'PinName="([^"]+)"')
_LINKED_TO_RE = re.compile(r'LinkedTo=\((MaterialGraphNode_[^\s]+)\s+([A-F0-9]+),?\)')
_DIRECTION_OUT_RE = re.compile(r'Direction="EGPD_Output"')


def _parse_pin_data(pin_blob: str) -> tuple[str, str | None, str | None]:
    pin_name_match = _PIN_NAME_RE.search(pin_blob)
    pin_name = pin_name_match.group(1) if pin_name_match else "UnknownPin"

    linked_to_match = _LINKED_TO_RE.search(pin_blob)
    if linked_to_match:
        linked_node = linked_to_match.group(1)
        linked_pin = linked_to_match.group(2)
    else:
        linked_node = None
        linked_pin = None

    return pin_name, linked_node, linked_pin


def parse_paste_text_to_graph(text: str, material_name: str = "PastedMaterial") -> MaterialGraph:
    lines = text.splitlines()

    node_defs: dict[str, dict] = {}
    edges_set: set[tuple[str, str, str, str]] = set()
    outputs: list[MaterialOutput] = []

    current_graph_node: str | None = None
    current_is_root = False

    for line in lines:
        node_match = _NODE_BEGIN_RE.match(line)
        if node_match:
            current_graph_node = node_match.group(1)
            current_is_root = "MaterialGraphNode_Root" in current_graph_node
            if not current_is_root and current_graph_node not in node_defs:
                node_defs[current_graph_node] = {
                    "id": current_graph_node,
                    "name": current_graph_node,
                    "type": "Unknown",
                    "params": {},
                }
            continue

        if current_graph_node is None:
            continue

        expr_match = _EXPR_CLASS_RE.match(line)
        if expr_match and not current_is_root:
            expr_type = expr_match.group(1)
            expr_name = expr_match.group(2)
            node_defs[current_graph_node]["type"] = expr_type
            node_defs[current_graph_node]["name"] = expr_name
            continue

        pin_match = _PIN_RE.search(line)
        if not pin_match:
            continue

        pin_blob = pin_match.group(1)
        pin_name, linked_node, _ = _parse_pin_data(pin_blob)
        if not linked_node:
            continue

        is_output_pin = bool(_DIRECTION_OUT_RE.search(pin_blob))

        if current_is_root:
            if linked_node in node_defs:
                outputs.append(MaterialOutput(output=pin_name, source_node=linked_node))
            else:
                outputs.append(MaterialOutput(output=pin_name, source_node=linked_node))
            continue

        if is_output_pin:
            from_node = current_graph_node
            to_node = linked_node
            from_pin = pin_name
            to_pin = "Input"
        else:
            from_node = linked_node
            to_node = current_graph_node
            from_pin = "Output"
            to_pin = pin_name

        if from_node.startswith("MaterialGraphNode_") and to_node.startswith("MaterialGraphNode_"):
            edges_set.add((from_node, from_pin, to_node, to_pin))

    nodes = [
        MaterialNode(
            id=node["id"],
            name=node["name"],
            type=node["type"],
            params=node["params"],
        )
        for _, node in sorted(node_defs.items(), key=lambda item: item[0])
    ]

    edges = [
        MaterialEdge(from_node=f, from_pin=fp, to_node=t, to_pin=tp)
        for (f, fp, t, tp) in sorted(edges_set)
        if f in node_defs and t in node_defs
    ]

    outputs = [output for output in outputs if output.source_node in node_defs]

    graph = MaterialGraph(
        material_name=material_name,
        source_type="paste_text",
        nodes=nodes,
        edges=edges,
        outputs=outputs,
    )
    graph.validate()
    return graph
