import os

import pytest
import numpy as np

try:
    from pydantic import ValidationError
    from pydantic_ome_ngff.v04.multiscale import Group

    pydantic = True
except ImportError:
    pydantic = False

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
    microscope_name = model.configuration["experiment"]["MicroscopeState"]["microscope_name"]
    model.configuration["experiment"]["CameraParameters"][microscope_name]["x_pixels"] = x_size
    model.configuration["experiment"]["CameraParameters"][microscope_name]["y_pixels"] = y_size
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
        if stop_early and np.random.rand() > 0.5:
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


@pytest.mark.parametrize("multiposition", [True, False])
@pytest.mark.parametrize("per_stack", [True, False])
@pytest.mark.parametrize("z_stack", [True, False])
@pytest.mark.parametrize("stop_early", [True, False])
@pytest.mark.parametrize("size", [(1024, 2048), (2048, 1024), (2048, 2048)])
def test_zarr_write(multiposition, per_stack, z_stack, stop_early, size):

    fn = "test.zarr"

    ds = zarr_ds(fn, multiposition, per_stack, z_stack, stop_early, size)

    if pydantic:
        try:
            Group.from_zarr(ds.image)
        except ValidationError as e:
            print(e)
            assert False

    file_name = ds.file_name

    close_zarr_ds(ds, file_name=file_name)

    assert True
