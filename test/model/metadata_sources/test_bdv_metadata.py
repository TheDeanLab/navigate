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
