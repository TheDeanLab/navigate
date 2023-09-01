import os

import pytest
import numpy as np
import h5py

from aslm.tools.file_functions import delete_folder


def recurse_dtype(group):
    for key, subgroup in group.items():
        subgroup_type = type(subgroup)
        if subgroup_type == h5py._hl.group.Group:
            recurse_dtype(subgroup)
        elif subgroup_type == h5py._hl.dataset.Dataset:
            if key == "resolutions":
                assert subgroup.dtype == "float64"
            elif key == "subdivisions":
                assert subgroup.dtype == "int32"
            elif key == "cells":
                assert subgroup.dtype == "int16"
        else:
            print("Unknown how to handle:", key, subgroup_type)


@pytest.mark.parametrize("multiposition", [True, False])
@pytest.mark.parametrize("per_stack", [True, False])
@pytest.mark.parametrize("z_stack", [True, False])
@pytest.mark.parametrize("stop_early", [True, False])
@pytest.mark.parametrize("size", [(1024, 2048), (2048, 1024), (2048, 2048)])
@pytest.mark.parametrize("ext", ["h5", "n5"])
def test_bdv_write(multiposition, per_stack, z_stack, stop_early, size, ext):
    from aslm.model.dummy import DummyModel
    from aslm.model.data_sources.bdv_data_source import BigDataViewerDataSource

    print(
        f"Conditions are multiposition: {multiposition} per_stack: {per_stack} "
        f"z_stack: {z_stack} stop_early: {stop_early}"
    )

    # Set up model with a random number of z-steps to modulate the shape
    model = DummyModel()
    z_steps = np.random.randint(1, 3)
    timepoints = np.random.randint(1, 3)

    x_size, y_size = size
    model.configuration["experiment"]["CameraParameters"]["x_pixels"] = x_size
    model.configuration["experiment"]["CameraParameters"]["y_pixels"] = y_size
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
    ds = BigDataViewerDataSource(f"test.{ext}")
    ds.set_metadata_from_configuration_experiment(model.configuration)

    # Populate one image per channel per timepoint
    n_images = ds.shape_c * ds.shape_z * ds.shape_t * ds.positions
    print(
        f"x: {ds.shape_x} y: {ds.shape_y} z: {ds.shape_z} c: {ds.shape_c} "
        f"t: {ds.shape_t} positions: {ds.positions} per_stack: {ds.metadata.per_stack}"
    )
    # TODO: Why does 2**16 make ImageJ crash??? But 2**8 works???
    data = (np.random.rand(n_images, ds.shape_y, ds.shape_x) * 2**8).astype("uint16")
    dbytes = np.sum(
        ds.shapes.prod(1) * ds.shape_t * ds.shape_c * ds.positions * 2
    )  # 16 bits, 8 bits per byte
    assert dbytes == ds.size
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
    ds.close()

    file_name = ds.file_name

    # check datatypes
    # todo: extend to n5
    if ext == "h5":
        ds = h5py.File(f"test.{ext}", "r")
        for key in ds.keys():
            recurse_dtype(ds[key])
    ds.close()

    # Delete
    try:
        xml_fn = os.path.splitext(file_name)[0] + ".xml"
        if os.path.isdir(file_name):
            # n5 is a directory
            delete_folder(file_name)
        else:
            os.remove(file_name)
        os.remove(xml_fn)
    except PermissionError:
        # Windows seems to think these files are still open
        pass

    assert True
