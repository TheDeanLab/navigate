import os
import xml.etree.ElementTree as ET

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
                assert subgroup.dtype == "uint16"
        else:
            print("Unknown how to handle:", key, subgroup_type)


def bdv_ds(
    fn,
    multiposition,
    per_stack,
    z_stack,
    stop_early,
    size,
    z_steps=2,
    timepoints=2,
):
    from test.model.dummy import DummyModel
    from navigate.model.data_sources.bdv_data_source import BigDataViewerDataSource

    print(
        f"Conditions are multiposition: {multiposition} per_stack: {per_stack} "
        f"z_stack: {z_stack} stop_early: {stop_early}"
    )

    # Set up model with explicit dimensions so test outcomes do not depend on
    # random shape choices.
    model = DummyModel()
    rng = np.random.default_rng(0)

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
    model.configuration["experiment"]["BDVParameters"] = {
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
            "down_sample": False,
            "axial_down_sample": 1,
            "lateral_down_sample": 1,
        },
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
    ds = BigDataViewerDataSource(fn)
    ds.set_metadata_from_configuration_experiment(model.configuration)

    # Populate one image per channel per timepoint
    n_images = ds.shape_c * ds.shape_z * ds.shape_t * ds.positions
    print(
        f"x: {ds.shape_x} y: {ds.shape_y} z: {ds.shape_z} c: {ds.shape_c} "
        f"t: {ds.shape_t} positions: {ds.positions} per_stack: {ds.metadata.per_stack}"
    )
    data = (rng.random((n_images, ds.shape_y, ds.shape_x)) * 2**16).astype("uint16")
    dbytes = np.sum(
        ds.shapes.prod(1) * ds.shape_t * ds.shape_c * ds.positions * 2
    )  # 2 bytes per pixel (16-bit)
    assert dbytes == ds.nbytes
    data_positions = (rng.random((n_images, 5)) * 50e3).astype(float)
    for i in range(n_images):
        ds.write(
            data[i, ...].squeeze(),
            x=data_positions[i, 0],
            y=data_positions[i, 1],
            z=data_positions[i, 2],
            theta=data_positions[i, 3],
            f=data_positions[i, 4],
        )
        if stop_early and i >= max(0, n_images // 2 - 1):
            break

    return ds


def close_bdv_ds(ds, file_name=None):
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


def dynamic_setup_values(file_name, ext):
    with h5py.File(file_name, "r") as image:
        return [
            int(image[f"t00000/s{setup_id:02}/0/cells"][0, 0, 0])
            for setup_id in range(4)
        ]


@pytest.mark.parametrize("ext", ["h5", "n5"])
def test_bdv_dynamic_position_growth_preserves_setup_mapping(tmp_path, ext):
    from navigate.model.data_sources.bdv_data_source import BigDataViewerDataSource

    file_name = tmp_path / f"dynamic.{ext}"
    ds = BigDataViewerDataSource(str(file_name))
    ds.set_metadata({"c": 2, "z": 1, "t": 1, "p": 1, "is_dynamic": True})

    for value, x_position in [(10, 0), (20, 0), (30, 100), (40, 100)]:
        ds.write(
            np.array([[value]], dtype="uint16"),
            x=x_position,
            y=0,
            z=0,
            theta=0,
            f=0,
        )
    ds.close()

    if ext == "h5":
        assert dynamic_setup_values(str(file_name), ext) == [10, 20, 30, 40]
    else:
        assert all(
            (
                file_name
                / f"setup{setup_id}"
                / "timepoint0"
                / "s0"
                / "0"
                / "0"
                / "0"
            ).is_file()
            for setup_id in range(4)
        )

    root = ET.parse(file_name.with_suffix(".xml")).getroot()
    view_setups = {
        int(setup.findtext("id")): (
            int(setup.findtext("attributes/channel")),
            int(setup.findtext("attributes/tile")),
        )
        for setup in root.findall("./SequenceDescription/ViewSetups/ViewSetup")
    }
    assert view_setups == {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (1, 1)}

    registrations = {
        int(registration.attrib["setup"])
        for registration in root.findall("./ViewRegistrations/ViewRegistration")
    }
    assert registrations == {0, 1, 2, 3}


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
    assert ds[0, ...].shape == (
        ds.positions,
        ds.shape_t,
        ds.shape_z,
        ds.shape_c,
        ds.shape_y,
        1,
    )
    assert ds[:, 0, ...].shape == (
        ds.positions,
        ds.shape_t,
        ds.shape_z,
        ds.shape_c,
        1,
        ds.shape_x,
    )
    assert ds[:, :, 0, ...].shape == (
        ds.positions,
        ds.shape_t,
        ds.shape_z,
        1,
        ds.shape_y,
        ds.shape_x,
    )
    assert ds[:, :, :, 0, ...].shape == (
        ds.positions,
        ds.shape_t,
        1,
        ds.shape_c,
        ds.shape_y,
        ds.shape_x,
    )
    assert ds[:, :, :, :, 0, ...].shape == (
        ds.positions,
        1,
        ds.shape_z,
        ds.shape_c,
        ds.shape_y,
        ds.shape_x,
    )
    assert ds[:, :, :, :, :, 0].shape == (
        1,
        ds.shape_t,
        ds.shape_z,
        ds.shape_c,
        ds.shape_y,
        ds.shape_x,
    )

    # Check slicing
    sx = 5
    assert ds[:sx, ...].shape == (
        ds.positions,
        ds.shape_t,
        ds.shape_z,
        ds.shape_c,
        ds.shape_y,
        min(ds.shape_x, sx),
    )
    assert ds[:, :sx, ...].shape == (
        ds.positions,
        ds.shape_t,
        ds.shape_z,
        ds.shape_c,
        min(ds.shape_y, sx),
        ds.shape_x,
    )
    assert ds[:, :, :sx, ...].shape == (
        ds.positions,
        ds.shape_t,
        ds.shape_z,
        min(ds.shape_c, sx),
        ds.shape_y,
        ds.shape_x,
    )
    assert ds[:, :, :, :sx, ...].shape == (
        ds.positions,
        ds.shape_t,
        min(ds.shape_z, sx),
        ds.shape_c,
        ds.shape_y,
        ds.shape_x,
    )
    assert ds[:, :, :, :, :sx, ...].shape == (
        ds.positions,
        min(ds.shape_t, sx),
        ds.shape_z,
        ds.shape_c,
        ds.shape_y,
        ds.shape_x,
    )
    assert ds[:, :, :, :, :, :sx].shape == (
        min(ds.positions, sx),
        ds.shape_t,
        ds.shape_z,
        ds.shape_c,
        ds.shape_y,
        ds.shape_x,
    )

    close_bdv_ds(ds)

    assert True
