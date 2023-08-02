import os

import pytest
import numpy as np

from aslm.tools.file_functions import delete_folder


@pytest.mark.parametrize("multiposition", [True, False])
@pytest.mark.parametrize("per_stack", [True, False])
@pytest.mark.parametrize("z_stack", [True, False])
@pytest.mark.parametrize("stop_early", [True, False])
@pytest.mark.parametrize("ext", ["h5", "n5"])
def test_bdv_write(multiposition, per_stack, z_stack, stop_early, ext):
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
    data = (np.random.rand(n_images, ds.shape_x, ds.shape_y) * 2**8).astype("uint16")
    bytes = np.sum(
        ds.shapes.prod(1) * ds.shape_t * ds.shape_c * ds.positions * 2
    )  # 16 bits, 8 bits per byte
    assert bytes == ds.size
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

    try:
        xml_fn = os.path.splitext(ds.file_name)[0] + ".xml"
        if os.path.isdir(ds.file_name):
            # n5 is a directory
            delete_folder(ds.file_name)
        else:
            os.remove(ds.file_name)
        os.remove(xml_fn)
    except PermissionError:
        # Windows seems to think these files are still open
        pass

    assert True
