import os

import pytest
import numpy as np
import h5py

from navigate.tools.file_functions import delete_folder


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

def bdv_ds(fn, multiposition, per_stack, z_stack, stop_early, size):
    from test.model.dummy import DummyModel
    from navigate.model.data_sources.bdv_data_source import BigDataViewerDataSource

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
    ds = BigDataViewerDataSource(fn)
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
    
def close_bdv_ds(ds, file_name = None): 
    ds.close()

    if file_name is None:
        file_name = ds.file_name

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

@pytest.mark.parametrize("multiposition", [True, False])
@pytest.mark.parametrize("per_stack", [True, False])
@pytest.mark.parametrize("z_stack", [True, False])
@pytest.mark.parametrize("stop_early", [True, False])
@pytest.mark.parametrize("size", [(1024, 2048), (2048, 1024), (2048, 2048)])
@pytest.mark.parametrize("ext", ["h5", "n5"])
def test_bdv_write(multiposition, per_stack, z_stack, stop_early, size, ext):

    fn = f"test.{ext}"

    ds = bdv_ds(fn, multiposition, per_stack, z_stack, stop_early, size)

    file_name = ds.file_name
    ds.close()

    # check datatypes
    # todo: extend to n5
    if ext == "h5":
        ds = h5py.File(f"test.{ext}", "r")
        for key in ds.keys():
            recurse_dtype(ds[key])

    close_bdv_ds(ds, file_name=file_name)

    assert True

@pytest.mark.parametrize("multiposition", [True, False])
@pytest.mark.parametrize("per_stack", [True, False])
@pytest.mark.parametrize("z_stack", [True, False])
@pytest.mark.parametrize("size", [(1024, 2048), (2048, 1024), (2048, 2048)])
def test_bdv_getitem(multiposition, per_stack, z_stack, size):
    ds = bdv_ds("test.h5", multiposition, per_stack, z_stack, False, size)

    # Check indexing
    assert ds[0,...].shape == (ds.positions, ds.shape_t, ds.shape_z, ds.shape_c, ds.shape_y, 1)
    assert ds[:,0,...].shape == (ds.positions, ds.shape_t, ds.shape_z, ds.shape_c, 1, ds.shape_x)
    assert ds[:,:,0,...].shape == (ds.positions, ds.shape_t, ds.shape_z, 1, ds.shape_y, ds.shape_x)
    assert ds[:,:,:,0,...].shape == (ds.positions, ds.shape_t, 1, ds.shape_c, ds.shape_y, ds.shape_x)
    assert ds[:,:,:,:,0,...].shape == (ds.positions, 1, ds.shape_z, ds.shape_c, ds.shape_y, ds.shape_x)
    assert ds[:,:,:,:,:,0].shape == (1, ds.shape_t, ds.shape_z, ds.shape_c, ds.shape_y, ds.shape_x)


    # Check slicing
    sx = 5
    assert ds[:sx,...].shape == (ds.positions, ds.shape_t, ds.shape_z, ds.shape_c, ds.shape_y, min(ds.shape_x, sx))
    assert ds[:,:sx,...].shape == (ds.positions, ds.shape_t, ds.shape_z, ds.shape_c, min(ds.shape_y, sx), ds.shape_x)
    assert ds[:,:,:sx,...].shape == (ds.positions, ds.shape_t, ds.shape_z, min(ds.shape_c, sx), ds.shape_y, ds.shape_x)
    assert ds[:,:,:,:sx,...].shape == (ds.positions, ds.shape_t, min(ds.shape_z, sx), ds.shape_c, ds.shape_y, ds.shape_x)
    assert ds[:,:,:,:,:sx,...].shape == (ds.positions, min(ds.shape_t,sx), ds.shape_z, ds.shape_c, ds.shape_y, ds.shape_x)
    assert ds[:,:,:,:,:,:sx].shape == (min(ds.positions, sx), ds.shape_t, ds.shape_z, ds.shape_c, ds.shape_y, ds.shape_x)

    close_bdv_ds(ds)

    assert True