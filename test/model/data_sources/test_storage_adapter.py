from pathlib import Path

import pytest

from navigate.model.data_sources.storage_adapter import (
    ArtifactRef,
    OMEZarrStorageAdapter,
)


def test_storage_adapter_resolves_artifacts():
    adapter = OMEZarrStorageAdapter("data_store.ome.zarr")

    assert adapter.resolve(ArtifactRef("image_collection", "field:2")) == "A/1/2"
    assert adapter.resolve(ArtifactRef("metadata_blob", "artifacts")) == (
        "navigate/metadata/artifacts.json"
    )
    assert adapter.absolute_path("A/1/0") == Path("data_store.ome.zarr") / "A/1/0"


def test_storage_adapter_reserved_artifacts_raise():
    adapter = OMEZarrStorageAdapter("data_store.ome.zarr")

    with pytest.raises(NotImplementedError):
        adapter.resolve(ArtifactRef("label_collection", "segmentation"))

    with pytest.raises(NotImplementedError):
        adapter.resolve(ArtifactRef("table", "measurements"))


def test_storage_adapter_manifest():
    adapter = OMEZarrStorageAdapter("data_store.ome.zarr")

    manifest = adapter.artifact_manifest([0, 1])
    manifest_paths = {
        (artifact["kind"], artifact["artifact_id"]): artifact["path"]
        for artifact in manifest["artifacts"]
    }

    assert manifest_paths[("image_collection", "field:0")] == "A/1/0"
    assert manifest_paths[("image_collection", "field:1")] == "A/1/1"
    assert manifest_paths[("metadata_blob", "artifacts")] == (
        "navigate/metadata/artifacts.json"
    )
