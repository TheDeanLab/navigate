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
