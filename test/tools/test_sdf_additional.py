import numpy as np

from navigate.tools.sdf import volume_from_sdf


def test_volume_from_sdf_respects_pixel_size_and_z_subsampling():
    volume = volume_from_sdf(lambda points: points[2], N=4, pixel_size=2, subsample_z=2)

    assert volume.shape == (2, 4, 4)
    np.testing.assert_array_equal(volume[0], np.full((4, 4), -3.0))
    np.testing.assert_array_equal(volume[1], np.full((4, 4), 1.0))
