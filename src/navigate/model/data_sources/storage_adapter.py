# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ARTIFACT_KINDS = (
    "image_collection",
    "label_collection",
    "table",
    "metadata_blob",
)


@dataclass(frozen=True)
class ArtifactRef:
    """Logical reference to data materialized inside an OME-Zarr store."""

    kind: str
    artifact_id: str

    def __post_init__(self) -> None:
        if self.kind not in ARTIFACT_KINDS:
            raise ValueError(f"Unsupported artifact kind {self.kind!r}.")


class OMEZarrStorageAdapter:
    """Maps logical artifact references to canonical OME-Zarr paths."""

    row_name = "A"
    column_name = "1"
    well_path = f"{row_name}/{column_name}"
    metadata_root = "navigate/metadata"
    metadata_blob_names = {
        "artifacts": f"{metadata_root}/artifacts.json",
        "acquisition": f"{metadata_root}/acquisition.json",
        "configuration": f"{metadata_root}/configuration.json",
    }

    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)

    def field_group_path(self, position_index: int) -> str:
        return f"{self.well_path}/{position_index}"

    def image_array_path(self, position_index: int, level: int) -> str:
        return f"{self.field_group_path(position_index)}/{level}"

    def metadata_blob_path(self, artifact_id: str) -> str:
        try:
            return self.metadata_blob_names[artifact_id]
        except KeyError as exc:
            raise ValueError(f"Unknown metadata blob {artifact_id!r}.") from exc

    def resolve(self, ref: ArtifactRef) -> str:
        if ref.kind == "image_collection":
            if not ref.artifact_id.startswith("field:"):
                raise ValueError(f"Unsupported image collection ref {ref.artifact_id!r}.")
            return self.field_group_path(int(ref.artifact_id.split(":", maxsplit=1)[1]))
        if ref.kind == "metadata_blob":
            return self.metadata_blob_path(ref.artifact_id)
        if ref.kind in {"label_collection", "table"}:
            raise NotImplementedError(
                f"Artifact kind {ref.kind!r} is reserved but not materialized by "
                "Navigate acquisition."
            )
        raise ValueError(f"Unknown artifact kind {ref.kind!r}.")

    def absolute_path(self, relative_path: str) -> Path:
        return self.root_path / relative_path

    @classmethod
    def metadata_blob_refs(cls) -> tuple[ArtifactRef, ...]:
        return tuple(
            ArtifactRef(kind="metadata_blob", artifact_id=artifact_id)
            for artifact_id in cls.metadata_blob_names
        )

    def image_collection_refs(self, positions: Iterable[int]) -> list[ArtifactRef]:
        return [
            ArtifactRef(kind="image_collection", artifact_id=f"field:{position}")
            for position in sorted(set(positions))
        ]

    def artifact_manifest(self, positions: Iterable[int]) -> dict:
        refs = self.image_collection_refs(positions) + list(self.metadata_blob_refs())
        return {
            "artifacts": [
                {
                    "kind": ref.kind,
                    "artifact_id": ref.artifact_id,
                    "path": self.resolve(ref),
                }
                for ref in refs
            ]
        }
