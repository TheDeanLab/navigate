import os
import numpy as np

import pytest


@pytest.mark.parametrize("ext", ["h5", "n5", "tiff"])
def test_bdv_metadata(ext):
    from aslm.model.metadata_sources.bdv_metadata import BigDataViewerMetadata

    md = BigDataViewerMetadata()

    views = []
    for _ in range(10):
        views.append(
            {
                "x": np.random.randint(-1000, 1000),
                "y": np.random.randint(-1000, 1000),
                "z": np.random.randint(-1000, 1000),
                "theta": np.random.randint(-1000, 1000),
                "f": np.random.randint(-1000, 1000),
            }
        )

    for view in views:
        arr = md.stage_positions_to_affine_matrix(**view)
        assert arr[0, 3] == view["y"] / md.dy
        assert arr[1, 3] == view["x"] / md.dx
        assert arr[2, 3] == view["z"] / md.dz

    md.write_xml(f"test_bdv.{ext}", views)

    os.remove("test_bdv.xml")

    # Test defaults for shear transform.
    assert md.rotate_data is False
    assert md.shear_data is False
    assert np.shape(md.rotate_transform) == (3, 4)
    assert np.shape(md.shear_transform) == (3, 4)

    # Confirm that the shear/rotation transforms are identity matrices by default
    assert np.all(md.shear_transform == np.eye(3, 4))
    assert np.all(md.rotate_transform == np.eye(3, 4))

    # Confirm that the shear/rotation transforms are identity matrices by default
    # even after calling calculate_shear_transform and calculate_rotate_transform
    md.calculate_shear_transform()
    md.calculate_rotate_transform()
    assert np.all(md.shear_transform == np.eye(3, 4))
    assert np.all(md.rotate_transform == np.eye(3, 4))

    # Test that the shear/rotation transforms are correctly calculated.
    md.shear_data = True
    md.shear_dimension = "XZ"
    md.shear_angle = 15
    md.dx, md.dy, md.dz = 1, 1, 1
    md.calculate_shear_transform()
    assert md.shear_transform[0, 2] == np.cos(np.deg2rad(15))

    md.rotate_data = True
    md.rotate_angle_x = 15
    md.rotate_angle_y = 0
    md.rotate_angle_z = 0
    md.calculate_rotate_transform()
    assert md.rotate_transform[1, 1] == np.cos(np.deg2rad(15))
    assert md.rotate_transform[1, 2] == -np.sin(np.deg2rad(15))
    assert md.rotate_transform[2, 1] == np.sin(np.deg2rad(15))
    assert md.rotate_transform[2, 2] == np.cos(np.deg2rad(15))

    # Make sure we can still write the data.
    md.write_xml(f"test_bdv.{ext}", views)
    os.remove("test_bdv.xml")
