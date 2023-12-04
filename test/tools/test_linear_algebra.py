import unittest
import numpy as np
from aslm.tools.linear_algebra import affine_rotation, affine_shear


class TestAffineRotation(unittest.TestCase):
    def test_no_rotation(self):
        result = affine_rotation()
        expected = np.eye(4, 4)
        np.testing.assert_equal(result, expected)

    def test_rotation_x(self):
        result = affine_rotation(x=45).ravel()
        expected = np.array(
            (
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.70710678,
                -0.70710678,
                0.0,
                0.0,
                0.70710678,
                0.70710678,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            )
        )
        np.testing.assert_array_almost_equal(result, expected)

    def test_rotation_y(self):
        result = affine_rotation(y=45)
        expected = np.array(
            [
                [0.70710678, 0.0, 0.70710678, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [-0.70710678, 0.0, 0.70710678, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        np.testing.assert_array_almost_equal(result, expected)

    def test_rotation_z(self):
        result = affine_rotation(z=45)
        expected = np.array(
            [
                [0.70710678, -0.70710678, 0.0, 0.0],
                [0.70710678, 0.70710678, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        np.testing.assert_array_almost_equal(result, expected)

    def test_rotation_xy(self):
        result = affine_rotation(x=10, y=33)
        import numpy as np

        expected = np.array(
            [
                [0.83867057, 0.0, 0.54463904, 0.0],
                [-0.09457558, 0.98480775, 0.14563362, 0.0],
                [-0.53636474, -0.17364818, 0.82592928, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        np.testing.assert_array_almost_equal(result, expected)


class TestAffineShear(unittest.TestCase):
    def test_no_shear(self):
        # Test with zero angles or voxel sizes
        result = affine_shear(0, 0, 0)
        expected = np.eye(4, 4)
        np.testing.assert_array_almost_equal(result, expected)

    def test_shear_xy(self):
        result = affine_shear(1, 1, 1, dimension="XY", angle=45)
        expected = np.eye(4, 4)
        expected[0, 1] = 0.70710678
        np.testing.assert_array_almost_equal(result, expected)

    def test_different_pixe_sizes(self):
        result = affine_shear(167, 167, 333, dimension="XY", angle=45)
        expected = np.eye(4, 4)
        expected[0, 1] = 0.35461511
        np.testing.assert_array_almost_equal(result, expected)

    def test_shear_xz(self):
        # Test shear in XZ dimension
        result = affine_shear(167, 167, 333, dimension="XZ", angle=45)
        expected = np.eye(4, 4)
        expected[0, 2] = 0.35461511
        np.testing.assert_array_almost_equal(result, expected)
