import numpy as np

from navigate.tools.linear_algebra import affine_rotation, affine_shear


def test_affine_rotation_xyz_combines_all_three_axes():
    x_angle, y_angle, z_angle = 10, 20, 30

    cx, sx = np.cos(np.deg2rad(x_angle)), np.sin(np.deg2rad(x_angle))
    cy, sy = np.cos(np.deg2rad(y_angle)), np.sin(np.deg2rad(y_angle))
    cz, sz = np.cos(np.deg2rad(z_angle)), np.sin(np.deg2rad(z_angle))

    x_transform = np.array(
        [[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]]
    )
    y_transform = np.array(
        [[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]]
    )
    z_transform = np.array(
        [[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    )
    expected = np.matmul(np.matmul(x_transform.T, y_transform).T, z_transform)

    np.testing.assert_array_almost_equal(
        affine_rotation(x=x_angle, y=y_angle, z=z_angle), expected
    )


def test_affine_shear_yz_and_zy_share_same_branch():
    expected = np.eye(4, 4)
    expected[1, 2] = 0.5

    np.testing.assert_array_almost_equal(
        affine_shear(2, 4, 8, dimension="YZ", angle=45), expected
    )
    np.testing.assert_array_almost_equal(
        affine_shear(2, 4, 8, dimension="ZY", angle=45), expected
    )
