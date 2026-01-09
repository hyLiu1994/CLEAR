# app/api/v1/trajectory.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/trajectories", tags=["trajectories"])


# ==========
# Internal Data Models
# ==========

class TrackPoint(BaseModel):
    """A single point on a trajectory (from AIS)"""
    timestamp: datetime
    lat: float
    lon: float
    sog: Optional[float] = Field(None, description="Speed over ground (knots)")
    cog: Optional[float] = Field(None, description="Course over ground (deg)")


class Segment(BaseModel):
    """Basic unit in CLEAR: a trajectory segment"""
    id: str
    trajectory_id: str
    vessel_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    short_description: Optional[str] = None
    points: List[TrackPoint] = Field(default_factory=list)


class Trajectory(BaseModel):
    """A trajectory consisting of multiple segments"""
    id: str
    vessel_id: Optional[str] = None
    segments: List[Segment]
    start_time: datetime
    end_time: datetime
    num_points: int


# ==========
# Response Models for Map
# ==========

class MapSegment(BaseModel):
    """
    Segment view for the frontend map:
    - coordinates: [[lon, lat], ...]
    - summary comes from Segment.short_description
    - vessel_type is currently mapped using a simple demo mapping
    """
    id: str
    coordinates: List[List[float]]
    summary: Optional[str] = None
    vessel_id: Optional[str] = None
    vessel_type: Optional[str] = None
    start_ts: datetime
    end_ts: datetime


class MapTrajectory(BaseModel):
    id: str
    segments: List[MapSegment]


# ==========
# Utility Functions: Read segments from JSON and construct Trajectory list
# ==========

def _load_raw_segments() -> List[Dict[str, Any]]:
    """
    Read the raw segment list (dict) from a JSON file without conversion.
    """
    path = Path(settings.SEGMENTS_JSON_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Segments JSON not found: {path}")

    import json
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Segments JSON must be a list of objects")
    return data



def _get_all_segments() -> List[Segment]:
    """
    JSON -> Segment (internal model)
    """
    raw_segments = _load_raw_segments()
    segments: List[Segment] = []
    for item in raw_segments:
        # Only take the fields we care about to avoid errors from extra keys in JSON
        payload = {
            "id": item["id"],
            "trajectory_id": item["trajectory_id"],
            "vessel_id": item.get("vessel_id"),
            "start_time": item["start_time"],
            "end_time": item["end_time"],
            "short_description": item.get("short_description"),
            "points": item.get("points", []),
        }
        segments.append(Segment(**payload))
    return segments




def _build_trajectories() -> List[Trajectory]:
    """
    Aggregate Segment -> Trajectory (internal structure) based on trajectory_id
    """
    segments = _get_all_segments()
    by_traj: Dict[str, List[Segment]] = {}

    for seg in segments:
        by_traj.setdefault(seg.trajectory_id, []).append(seg)

    trajectories: List[Trajectory] = []

    for traj_id, segs in by_traj.items():
        segs_sorted = sorted(segs, key=lambda s: s.start_time)
        vessel_id = next((s.vessel_id for s in segs_sorted if s.vessel_id), None)
        start_time = min(s.start_time for s in segs_sorted)
        end_time = max(s.end_time for s in segs_sorted)
        num_points = sum(len(s.points) for s in segs_sorted)

        trajectories.append(
            Trajectory(
                id=traj_id,
                vessel_id=vessel_id,
                segments=segs_sorted,
                start_time=start_time,
                end_time=end_time,
                num_points=num_points,
            )
        )

    trajectories.sort(key=lambda t: t.start_time)
    return trajectories


# A simple demo mapping: MMSI -> vessel_type
VESSEL_TYPE_BY_MMSI: Dict[str, str] = {
    "219000000": "Cargo",
    "219000111": "Tanker",
    "218999888": "Cargo",
    "220123456": "Cargo",
}


def _to_map_trajectory(traj: Trajectory) -> MapTrajectory:
    """
    Internal Trajectory -> MapTrajectory for the frontend map
    """
    map_segments: List[MapSegment] = []

    for seg in traj.segments:
        coordinates = [[p.lon, p.lat] for p in seg.points]
        if not coordinates:
            # Skip this segment if there are no points to avoid drawing empty polylines
            continue

        vessel_type = (
            VESSEL_TYPE_BY_MMSI.get(seg.vessel_id)
            if seg.vessel_id is not None
            else None
        )

        map_segments.append(
            MapSegment(
                id=seg.id,
                coordinates=coordinates,
                summary=seg.short_description,
                vessel_id=seg.vessel_id,
                vessel_type=vessel_type,
                start_ts=seg.start_time,
                end_ts=seg.end_time,
            )
        )

    return MapTrajectory(id=traj.id, segments=map_segments)


# ==========
# API
# ==========

@router.get(
    "",
    response_model=List[MapTrajectory],
    summary="List trajectories for map",
    description="Return trajectory data for the map: Trajectory → segments → coordinates.",
)
async def list_trajectories(
    vessel_id: Optional[str] = Query(None, description="Filter by vessel_id (MMSI)"),
):
    """
    Simple version: filter by vessel_id on the server side, other filtering logic is done on the frontend.
    """
    all_traj = _build_trajectories()

    if vessel_id:
        all_traj = [t for t in all_traj if t.vessel_id == vessel_id]

    return [_to_map_trajectory(t) for t in all_traj]


@router.get(
    "/{trajectory_id}",
    response_model=MapTrajectory,
    summary="Get single trajectory for map",
    description="Return a single trajectory (map view).",
)
async def get_trajectory(trajectory_id: str):
    for traj in _build_trajectories():
        if traj.id == trajectory_id:
            return _to_map_trajectory(traj)
    raise HTTPException(status_code=404, detail="Trajectory not found")
