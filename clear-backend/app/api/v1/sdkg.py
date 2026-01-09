# app/api/v1/sdkg.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings


router = APIRouter(prefix="/sdkg", tags=["sdkg"])


#======================= 1. Index Graph Model ===================

class SDKGNode(BaseModel):
    id: str
    type: Literal["behavior", "attribute", "function", "segment", "trajectory"]
    label: str


class SDKGLink(BaseModel):
    source: str
    target: str
    relation: Optional[str] = None


class SDKGIndexGraph(BaseModel):
    nodes: List[SDKGNode]
    links: List[SDKGLink]


# ======================= 2. Node Detail Model ===================

class RelatedNode(BaseModel):
    id: str
    label: str


class BaseNodeDetail(BaseModel):
    """
    All nodes have common fields, and the front-end NodeDoc.vue can rely on these:
    """
    id: str
    type: Literal["behavior", "attribute", "function", "segment", "trajectory"]

    title: str
    summary: str

    description: List[str] = []
    notes: List[str] = []
    related: List[RelatedNode] = []


class BehaviorNodeDetail(BaseNodeDetail):
    type: Literal["behavior"]
    degree: Optional[int] = None
    support: Optional[float] = None
    behavior: List[str] = []


class AttributeNodeDetail(BaseNodeDetail):
    type: Literal["attribute"]
    degree: Optional[int] = None


class FunctionNodeDetail(BaseNodeDetail):
    type: Literal["function"]
    degree: Optional[int] = None


class SegmentNodeDetail(BaseNodeDetail):
    type: Literal["segment"]
    trajectory_id: Optional[str] = None
    vessel_id: Optional[str] = None
    vessel_type: Optional[str] = None
    pattern: List[str] = []
    
    static_attributes: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None
    
    behavior_estimator: Optional[BehaviorEstimator] = None
    method_selector: Optional[MethodSelector] = None
    explanation_composer: Optional[ExplanationComposer] = None

class TrajectoryNodeDetail(BaseNodeDetail):
    type: Literal["trajectory"]
    degree: Optional[int] = None


NodeDetail = Union[
    BehaviorNodeDetail,
    AttributeNodeDetail,
    FunctionNodeDetail,
    SegmentNodeDetail,
    TrajectoryNodeDetail,
]


# This is the "original JSON on disk" model, as loose as possible, compatible with what you want to write in the future:
class RawNodeFile(BaseModel):
    id: str
    type: Literal["behavior", "attribute", "function", "segment", "trajectory"]

    label: Optional[str] = None
    title: Optional[str] = None

    summary: Optional[str] = None
    description: Optional[List[str]] = None
    notes: Optional[List[str]] = None

    related: Optional[List[RelatedNode]] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    static_attributes: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

    behavior_estimator: Optional[Dict[str, Any]] = None
    method_selector: Optional[Dict[str, Any]] = None
    explanation_composer: Optional[Dict[str, Any]] = None
# ======================= 3. Subgraph Models ===================
class BehaviorEstimator(BaseModel):
    graph_support: Optional[str] = None
    contextual_justification: Optional[str] = None

class MethodSelector(BaseModel):
    statistical_support: Optional[str] = None

class ExplanationComposer(BaseModel):
    regulatory_rule_cue: Optional[str] = None
    operational_protocol_rationale: Optional[str] = None
    
class SubgraphNode(BaseModel):
    id: str
    label: str
    type: Literal["behavior", "attribute", "function", "segment", "trajectory"]
    level: int
    isCenter: bool
    # Additional fields from node details
    title: Optional[str] = None
    summary: Optional[str] = None


class SubgraphLink(BaseModel):
    source: str
    target: str
    level: int


class SubgraphData(BaseModel):
    nodes: List[SubgraphNode]
    links: List[SubgraphLink]
    allNodeIds: List[str]
    centerNodeId: str
    maxLevel: int
    totalNodes: int
    totalLinks: int


# ======================= 4. load index JSON ===================

def _load_sdkg_index_raw() -> Dict[str, Any]:
    path = Path(settings.SDKG_INDEX_JSON_PATH)
    if not path.exists():
        raise FileNotFoundError(f"SD-KG index JSON not found: {path}")

    import json
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "nodes" not in data or "links" not in data:
        raise ValueError("SD-KG index JSON must contain 'nodes' and 'links'")

    return data


def _get_index_graph() -> SDKGIndexGraph:
    raw = _load_sdkg_index_raw()

    nodes = [
        SDKGNode(
            id=n["id"],
            type=n["type"],
            label=n["label"],
        )
        for n in raw.get("nodes", [])
    ]

    links = [SDKGLink(**l) for l in raw.get("links", [])]

    return SDKGIndexGraph(nodes=nodes, links=links)


# ======================= 5. Read node details file ===================

def _load_node_file(node_id: str) -> RawNodeFile:
    """
    Read the node definition from data/sdkg _ nodes/{node _ id}. json.
    """
    base_dir = Path(settings.SDKG_NODES_DIR)
    path = base_dir / f"{node_id}.json"

    if not path.exists():
        raise FileNotFoundError(f"Node detail file not found: {path}")

    import json
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return RawNodeFile(**data)


def _build_node_detail(raw: RawNodeFile) -> NodeDetail:
    """
    RawNodeFile-> Concrete NodeDetail subclass (distributed according to type).
    Here's doing some default value padding:
    -title: first raw.title, otherwise raw.label, otherwise id
    -summary: Give at least an empty string
    -description/notes/related: at least an empty list
    """
    common = dict(
        id=raw.id,
        type=raw.type,
        title=raw.title or raw.label or raw.id,
        summary=raw.summary or "",
        description=raw.description or [],
        notes=raw.notes or [],
        related=raw.related or [],
    )

    if raw.type == "behavior":
        return BehaviorNodeDetail(**common)

    if raw.type == "attribute":
        return AttributeNodeDetail(**common)

    if raw.type == "function":
        return FunctionNodeDetail(**common)

    if raw.type == "segment":
        # Construct objects for three new fields
        behavior_estimator = None
        if raw.behavior_estimator:
            behavior_estimator = BehaviorEstimator(
                graph_support=raw.behavior_estimator.get('graph_support'),
                contextual_justification=raw.behavior_estimator.get('contextual_justification')
            )
        
        method_selector = None
        if raw.method_selector:
            method_selector = MethodSelector(
                statistical_support=raw.method_selector.get('statistical_support')
            )
        
        explanation_composer = None
        if raw.explanation_composer:
            explanation_composer = ExplanationComposer(
                regulatory_rule_cue=raw.explanation_composer.get('regulatory_rule_cue'),
                operational_protocol_rationale=raw.explanation_composer.get('operational_protocol_rationale')
            )
        
        segment_data = common.copy()
        segment_data.update({
            "trajectory_id": raw.metadata.get("trajectory_id"),
            "vessel_id": raw.metadata.get("vessel_id"),
            "vessel_type": raw.metadata.get("vessel_type"), 
            "pattern": [], 
            "static_attributes": raw.static_attributes or [],
            "context": raw.context or {},
            # New three fields
            "behavior_estimator": behavior_estimator,
            "method_selector": method_selector,
            "explanation_composer": explanation_composer
        })
        return SegmentNodeDetail(**segment_data)
    if raw.type == "trajectory":
        return TrajectoryNodeDetail(**common)

    raise HTTPException(status_code=500, detail=f"Unsupported node type: {raw.type}")


# ======================= 6. Subgraph Functions ===================
def _load_subgraph_file(node_id: str) -> Dict[str, Any]:
    """
    Read subgraph data from subgraph folder
    """
    subgraph_dir = Path(settings.SUBGRAPH_DIR)
    path = subgraph_dir / f"{node_id}.json"

    if not path.exists():
        raise FileNotFoundError(f"Subgraph file not found: {path}")

    import json
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def _enrich_subgraph_nodes(subgraph_data: Dict[str, Any]) -> SubgraphData:
    """
    Enrich subgraph nodes with additional details from node files
    """
    enriched_nodes = []
    
    for node in subgraph_data.get("nodes", []):
        # Create base node with subgraph data
        enriched_node = {
            "id": node["id"],
            "label": node.get("label", ""),
            "type": node["type"],
            "level": node["level"],
            "isCenter": node.get("isCenter", False)
        }
        
        # Try to load additional details from node file
        try:
            node_detail = _load_node_file(node["id"])
            enriched_node["title"] = node_detail.title or node_detail.label or node["id"]
            enriched_node["summary"] = node_detail.summary or ""
        except FileNotFoundError:
            # If node detail file doesn't exist, use basic info
            enriched_node["title"] = node.get("label", node["id"])
            enriched_node["summary"] = ""
        except Exception:
            # If any other error, continue with basic info
            enriched_node["title"] = node.get("label", node["id"])
            enriched_node["summary"] = ""
        
        enriched_nodes.append(SubgraphNode(**enriched_node))
    
    # Build links
    links = [SubgraphLink(**link) for link in subgraph_data.get("links", [])]
    
    return SubgraphData(
        nodes=enriched_nodes,
        links=links,
        allNodeIds=subgraph_data.get("allNodeIds", []),
        centerNodeId=subgraph_data.get("centerNodeId", ""),
        maxLevel=subgraph_data.get("maxLevel", 3),
        totalNodes=subgraph_data.get("totalNodes", 0),
        totalLinks=subgraph_data.get("totalLinks", 0)
    )


# =========================== 7. API ===========================

@router.get("/index", response_model=SDKGIndexGraph)
async def get_sdkg_index():
    """Returns the SD-KG index graph (nodes + links) for the front-end ForceGraph."""
    return _get_index_graph()


@router.get("/nodes/{node_id}", response_model=NodeDetail)
async def get_sdkg_node_detail(node_id: str):
    """
    Return to SD-KG node complete details.
    Now implement: read from data/sdkg _ nodes/{node _ id}. json and then map to NodeDetail by type.
    """
    try:
        raw = _load_node_file(node_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Node not found")

    return _build_node_detail(raw)


@router.get("/subgraph/{node_id}", response_model=SubgraphData)
async def get_node_subgraph(node_id: str):
    """
    Return the subgraph data for a specific node (1-3 levels)
    This provides the pre-computed relationship graph for the frontend visualization
    """
    try:
        # Load the pre-computed subgraph
        subgraph_data = _load_subgraph_file(node_id)
        
        # Enrich nodes with additional details
        enriched_subgraph = _enrich_subgraph_nodes(subgraph_data)
        
        return enriched_subgraph
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Subgraph not found for node: {node_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading subgraph: {str(e)}")
