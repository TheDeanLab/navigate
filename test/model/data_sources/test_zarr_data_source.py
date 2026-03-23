import json
import os
from pathlib import Path

import numpy as np
import pytest
import zarr
from ome_zarr_models.v05.hcs import HCS
from ome_zarr_models.v05.image import Image
from ome_zarr_models.v05.well import Well

from navigate.tools.file_functions import delete_folder


def zarr_ds(fn, multiposition, per_stack, z_stack, stop_early, size):
    from test.model.dummy import DummyModel
    from navigate.model.data_sources.zarr_data_source import OMEZarrDataSource

    print(
        f"Conditions are multiposition: {multiposition} per_stack: {per_stack} "
        f"z_stack: {z_stack} stop_early: {stop_early}"
    )

    # Set up model with a random number of z-steps to modulate the shape
    model = DummyModel()
    z_steps = np.random.randint(1, 3)
    timepoints = np.random.randint(1, 3)

    x_size, y_size = size
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    model.configuration["experiment"]["CameraParameters"][microscope_name][
        "x_pixels"
    ] = x_size
    model.configuration["experiment"]["CameraParameters"][microscope_name][
        "y_pixels"
    ] = y_size
    model.img_width = x_size
    model.img_height = y_size

    model.configuration["experiment"]["MicroscopeState"]["image_mode"] = (
        "z-stack" if z_stack else "single"
    )
    model.configuration["experiment"]["MicroscopeState"]["number_z_steps"] = z_steps
    model.configuration["experiment"]["MicroscopeState"][
        "is_multiposition"
    ] = multiposition
    model.configuration["experiment"]["MicroscopeState"]["timepoints"] = timepoints

    model.configuration["experiment"]["OMEZarrParameters"] = {
        "shear": {
            "shear_data": True,
            "shear_dimension": "YZ",
            "shear_angle": 45,
        },
        "rotate": {
            "rotate_data": False,
            "X": 0,
            "Y": 0,
            "Z": 0,
        },
        "down_sample": {
            "enabled": True,
            "scale_factors": [2, 4],
        },
        "chunk_shape": [1, 1, 8, 256, 256],
        "shard_shape": [1, 1, 32, 256, 256],
        "compression": "zstd-bitshuffle-fast",
    }

    if per_stack:
        model.configuration["experiment"]["MicroscopeState"][
            "stack_cycling_mode"
        ] = "per_stack"
    else:
        model.configuration["experiment"]["MicroscopeState"][
            "stack_cycling_mode"
        ] = "per_slice"

    # Establish a BDV data source
    ds = OMEZarrDataSource(fn)
    ds.set_metadata_from_configuration_experiment(model.configuration)

    # Populate one image per channel per timepoint
    n_images = ds.shape_c * ds.shape_z * ds.shape_t * ds.positions
    print(
        f"x: {ds.shape_x} y: {ds.shape_y} z: {ds.shape_z} c: {ds.shape_c} "
        f"t: {ds.shape_t} positions: {ds.positions} per_stack: {ds.metadata.per_stack}"
    )
    data = (np.random.rand(n_images, ds.shape_y, ds.shape_x) * 2**16).astype("uint16")
    dbytes = np.sum(
        ds.shapes.prod(1) * ds.shape_t * ds.shape_c * ds.positions * 2
    )  # 2 bytes per pixel (16-bit)
    assert dbytes == ds.nbytes
    data_positions = (np.random.rand(n_images, 5) * 50e3).astype(float)
    for i in range(n_images):
        ds.write(
            data[i, ...].squeeze(),
            x=data_positions[i, 0],
            y=data_positions[i, 1],
            z=data_positions[i, 2],
            theta=data_positions[i, 3],
            f=data_positions[i, 4],
        )
        if stop_early and i >= max(1, n_images // 3):
            break

    return ds


def close_zarr_ds(ds, file_name=None):
    ds.close()

    if file_name is None:
        file_name = ds.file_name

    # Delete
    try:
        if os.path.isdir(file_name):
            # zarr is a directory
            delete_folder(file_name)
        else:
            os.remove(file_name)
    except PermissionError:
        # Windows seems to think these files are still open
        pass


def assert_hcs_store(ds):
    store_path = Path(ds.file_name)
    root = zarr.open_group(store_path, mode="r")
    HCS.from_zarr(root)

    well_group = root["A/1"]
    Well.from_zarr(well_group)

    field_names = sorted(name for name in list(well_group.keys()) if name.isdigit())
    assert field_names == [str(position) for position in range(ds.positions)]

    for field_name in field_names:
        field_group = well_group[field_name]
        Image.from_zarr(field_group)
        level0 = field_group["0"]
        assert level0.shape == (
            ds.shape_t,
            ds.shape_c,
            ds.shape_z,
            ds.shape_y,
            ds.shape_x,
        )
        if len(ds.scale_factors) > 1:
            for level_index in range(1, len(ds.scale_factors)):
                assert str(level_index) in field_group

    artifacts_path = store_path / "navigate" / "metadata" / "artifacts.json"
    acquisition_path = store_path / "navigate" / "metadata" / "acquisition.json"
    configuration_path = store_path / "navigate" / "metadata" / "configuration.json"
    metadata_xml_path = store_path / "OME" / "METADATA.ome.xml"

    assert artifacts_path.exists()
    assert acquisition_path.exists()
    assert configuration_path.exists()
    assert metadata_xml_path.exists()

    with open(artifacts_path, encoding="utf-8") as handle:
        artifact_manifest = json.load(handle)
    with open(acquisition_path, encoding="utf-8") as handle:
        acquisition = json.load(handle)
    with open(configuration_path, encoding="utf-8") as handle:
        configuration = json.load(handle)

    manifest_paths = {
        (artifact["kind"], artifact["artifact_id"]): artifact["path"]
        for artifact in artifact_manifest["artifacts"]
    }
    assert manifest_paths[("metadata_blob", "artifacts")] == (
        "navigate/metadata/artifacts.json"
    )
    for position in range(ds.positions):
        assert manifest_paths[("image_collection", f"field:{position}")] == f"A/1/{position}"

    assert acquisition["field_names"] == field_names
    assert "microscopes" in configuration


@pytest.mark.parametrize("multiposition", [True, False])
@pytest.mark.parametrize("per_stack", [True, False])
@pytest.mark.parametrize("z_stack", [True, False])
@pytest.mark.parametrize("stop_early", [True, False])
@pytest.mark.parametrize("size", [(1024, 2048), (2048, 1024), (2048, 2048)])
def test_zarr_write(multiposition, per_stack, z_stack, stop_early, size):

    fn = "test.zarr"

    ds = zarr_ds(fn, multiposition, per_stack, z_stack, stop_early, size)
    file_name = ds.file_name
    ds.close()
    assert_hcs_store(ds)

    close_zarr_ds(ds, file_name=file_name)

    assert True
