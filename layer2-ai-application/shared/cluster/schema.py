"""
Pattern 6 — Treasure Map · Output schema.

    "what suffering tribe is this 😭"

Phenotype clustering — groups cases by similarity in feature space.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


ClusterMethod = Literal["kmeans", "hdbscan", "agglomerative"]


class TreasureMapOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pattern: Literal["treasure_map_cluster"] = "treasure_map_cluster"
    case_id: str
    cluster_id: int = Field(..., ge=0)
    cluster_label: str = Field(..., description=(
        "human-readable phenotype name, e.g. 'elderly_polypharm_chest_pain'"
    ))
    cluster_size: int = Field(..., ge=0)
    distance_to_centroid: float = Field(..., ge=0)
    silhouette: float | None = Field(None, description="cluster quality, range [-1, 1]")
    nearest_neighbors: list[str] = Field(default_factory=list, description=(
        "encounter_ids of K closest cases within the same cluster"
    ))
    method: ClusterMethod
    k: int = Field(..., description="number of clusters in the model")
    warnings: list[str] = Field(default_factory=list)
