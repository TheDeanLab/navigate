# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np

from navigate.controller.sub_controllers.camera_view import (
    BaseViewController,
    MIPViewController,
)


class _Getter:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def test_try_to_display_image_updates_orthogonal_projections(monkeypatch):
    controller = MIPViewController.__new__(MIPViewController)
    controller.image_mode = "z-stack"
    controller.display_enabled = SimpleNamespace(get=lambda: True)
    controller._clear_mip = MagicMock()
    controller.identify_channel_index_and_slice = lambda: (0, 1)
    controller.xy_mip = np.zeros((1, 3, 4), dtype=np.uint16)
    controller.zy_mip = np.zeros((1, 2, 4), dtype=np.uint16)
    controller.zx_mip = np.zeros((1, 2, 3), dtype=np.uint16)

    parent_calls = []

    def _parent_try_to_display_image(self, image):
        parent_calls.append(image.copy())

    monkeypatch.setattr(
        BaseViewController,
        "try_to_display_image",
        _parent_try_to_display_image,
    )

    image_1 = np.array(
        [
            [1, 10, 3, 9],
            [8, 2, 7, 4],
            [6, 5, 12, 11],
        ],
        dtype=np.uint16,
    )
    image_2 = np.array(
        [
            [2, 9, 13, 1],
            [3, 15, 6, 8],
            [10, 4, 5, 14],
        ],
        dtype=np.uint16,
    )

    controller.try_to_display_image(image_1)
    controller.try_to_display_image(image_2)

    np.testing.assert_array_equal(
        controller.xy_mip[0],
        np.maximum(image_1, image_2),
    )
    np.testing.assert_array_equal(
        controller.zy_mip[0, 1],
        np.maximum(np.max(image_1, axis=0), np.max(image_2, axis=0)),
    )
    np.testing.assert_array_equal(
        controller.zx_mip[0, 1],
        np.maximum(np.max(image_1, axis=1), np.max(image_2, axis=1)),
    )
    assert len(parent_calls) == 2
    controller._clear_mip.assert_not_called()


def test_try_to_display_image_clears_and_returns_when_disabled(monkeypatch):
    controller = MIPViewController.__new__(MIPViewController)
    controller.image_mode = "z-stack"
    controller.display_enabled = SimpleNamespace(get=lambda: False)
    controller._is_display_visible = lambda: True
    controller._clear_mip = MagicMock()
    controller.identify_channel_index_and_slice = lambda: (0, 0)
    controller.xy_mip = np.full((1, 2, 2), 99, dtype=np.uint16)
    controller.zy_mip = np.full((1, 2, 2), 99, dtype=np.uint16)
    controller.zx_mip = np.full((1, 2, 2), 99, dtype=np.uint16)

    monkeypatch.setattr(
        BaseViewController,
        "try_to_display_image",
        lambda self, image: (_ for _ in ()).throw(
            AssertionError("BaseViewController.try_to_display_image should not run")
        ),
    )

    image = np.array([[1, 2], [3, 4]], dtype=np.uint16)
    controller.try_to_display_image(image)

    np.testing.assert_array_equal(controller.xy_mip, np.full((1, 2, 2), 99))
    np.testing.assert_array_equal(controller.zy_mip, np.full((1, 2, 2), 99))
    np.testing.assert_array_equal(controller.zx_mip, np.full((1, 2, 2), 99))
    controller._clear_mip.assert_called_once_with()


def test_get_mip_image_uses_correct_projection_and_anisotropic_scaling_zy():
    controller = MIPViewController.__new__(MIPViewController)
    controller.axial_to_lateral_ratio = 2.0
    controller.selected_channels = ["CH1"]
    controller.render_widgets = {
        "perspective": _Getter("ZY"),
        "channel": _Getter("CH1"),
    }
    controller.flip_image = lambda image: image
    controller.down_sample_image = lambda image, *_: image
    controller.xy_mip = np.zeros((1, 2, 3), dtype=np.uint16)
    controller.zy_mip = np.zeros((1, 4, 3), dtype=np.uint16)
    controller.zx_mip = np.array(
        [
            [
                [1, 2],
                [3, 4],
                [5, 6],
                [7, 8],
            ]
        ],
        dtype=np.uint16,
    )

    image = controller.get_mip_image()

    # ZY should source from zx_mip (Z-by-Y), transpose to Y-by-Z, then scale Z width.
    expected = np.array([[1, 3, 5, 7], [2, 4, 6, 8]], dtype=np.uint16)
    expected = np.repeat(expected, 2, axis=1)
    np.testing.assert_array_equal(image, expected)


def test_get_mip_image_uses_correct_projection_and_anisotropic_scaling_zx():
    controller = MIPViewController.__new__(MIPViewController)
    controller.axial_to_lateral_ratio = 1.5
    controller.selected_channels = ["CH1"]
    controller.render_widgets = {
        "perspective": _Getter("ZX"),
        "channel": _Getter("CH1"),
    }
    controller.flip_image = lambda image: image
    controller.down_sample_image = lambda image, *_: image
    controller.xy_mip = np.zeros((1, 2, 3), dtype=np.uint16)
    controller.zy_mip = np.array(
        [
            [
                [10, 11, 12],
                [20, 21, 22],
                [30, 31, 32],
                [40, 41, 42],
            ]
        ],
        dtype=np.uint16,
    )
    controller.zx_mip = np.zeros((1, 4, 2), dtype=np.uint16)

    image = controller.get_mip_image()

    # ZX should source from zy_mip (Z-by-X) and scale Z along image height.
    expected = np.array(
        [
            [10, 11, 12],
            [20, 21, 22],
            [30, 31, 32],
            [40, 41, 42],
        ],
        dtype=np.uint16,
    )
    # 4 * 1.5 -> 6 rows
    expected = np.repeat(expected, [2, 1, 2, 1], axis=0)
    np.testing.assert_array_equal(image, expected)


def test_get_mip_image_multi_perspective_composition():
    controller = MIPViewController.__new__(MIPViewController)
    controller.axial_to_lateral_ratio = 1.0
    controller.multi_view_gap = 1
    controller.selected_channels = ["CH1"]
    controller.render_widgets = {
        "perspective": _Getter("Multi"),
        "channel": _Getter("CH1"),
    }
    controller.flip_image = lambda image: image
    controller.down_sample_image = lambda image, *_: image

    controller.xy_mip = np.array([[[100, 101], [102, 103]]], dtype=np.uint16)
    # ZY source (zx_mip -> transpose => 2x2)
    controller.zx_mip = np.array([[[10, 20], [30, 40]]], dtype=np.uint16)
    # ZX source (zy_mip => 2x2)
    controller.zy_mip = np.array([[[50, 60], [70, 80]]], dtype=np.uint16)

    image = controller.get_mip_image()

    # ratio=1, gap=1, left/top pads=1 -> output shape 6x6.
    assert image.shape == (6, 6)
    # XY center
    np.testing.assert_array_equal(image[1:3, 1:3], np.array([[100, 101], [102, 103]]))
    # YZ right
    np.testing.assert_array_equal(image[1:3, 4:6], np.array([[10, 30], [20, 40]]))
    # ZX bottom
    np.testing.assert_array_equal(image[4:6, 1:3], np.array([[50, 60], [70, 80]]))
