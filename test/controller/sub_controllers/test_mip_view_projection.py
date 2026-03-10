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
    CameraViewController,
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


def test_try_to_display_image_casts_frame_dtype_for_opencv_max(monkeypatch):
    controller = MIPViewController.__new__(MIPViewController)
    controller.image_mode = "z-stack"
    controller.display_enabled = SimpleNamespace(get=lambda: True)
    controller._clear_mip = MagicMock()
    controller.identify_channel_index_and_slice = lambda: (0, 0)
    controller.number_of_channels = 1
    controller.number_of_slices = 2
    controller.original_image_height = 2
    controller.original_image_width = 3
    controller.xy_mip = np.zeros((1, 2, 3), dtype=np.uint16)
    controller.zy_mip = np.zeros((1, 2, 3), dtype=np.uint16)
    controller.zx_mip = np.zeros((1, 2, 2), dtype=np.uint16)
    controller._zy_reduce_buf = np.empty((1, 3), dtype=np.uint16)
    controller._zx_reduce_buf = np.empty((2, 1), dtype=np.uint16)

    monkeypatch.setattr(BaseViewController, "try_to_display_image", lambda *_: None)

    image = np.array([[1.2, 2.8, 3.1], [4.9, 5.0, 6.7]], dtype=np.float32)
    controller.try_to_display_image(image)

    np.testing.assert_array_equal(controller.xy_mip[0], image.astype(np.uint16))
    assert controller.xy_mip.dtype == np.uint16


def test_try_to_display_image_reallocates_mip_buffers_when_shape_changes(monkeypatch):
    controller = MIPViewController.__new__(MIPViewController)
    controller.image_mode = "z-stack"
    controller.display_enabled = SimpleNamespace(get=lambda: True)
    controller._clear_mip = MagicMock()
    controller.identify_channel_index_and_slice = lambda: (0, 1)
    controller.number_of_channels = 1
    controller.number_of_slices = 2
    controller.original_image_height = 2
    controller.original_image_width = 2
    controller.xy_mip = np.zeros((1, 2, 2), dtype=np.uint16)
    controller.zy_mip = np.zeros((1, 2, 2), dtype=np.uint16)
    controller.zx_mip = np.zeros((1, 2, 2), dtype=np.uint16)
    controller._zy_reduce_buf = np.empty((1, 2), dtype=np.uint16)
    controller._zx_reduce_buf = np.empty((2, 1), dtype=np.uint16)

    monkeypatch.setattr(BaseViewController, "try_to_display_image", lambda *_: None)

    image = np.arange(200, 212, dtype=np.uint16).reshape(3, 4)
    controller.try_to_display_image(image)

    assert controller.xy_mip.shape == (1, 3, 4)
    assert controller.zy_mip.shape == (1, 2, 4)
    assert controller.zx_mip.shape == (1, 2, 3)
    np.testing.assert_array_equal(controller.xy_mip[0], image)


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

    # gap=1 with no outer padding -> output shape 5x5.
    assert image.shape == (5, 5)
    # XY upper-left
    np.testing.assert_array_equal(image[0:2, 0:2], np.array([[100, 101], [102, 103]]))
    # YZ right
    np.testing.assert_array_equal(image[0:2, 3:5], np.array([[10, 30], [20, 40]]))
    # ZX bottom
    np.testing.assert_array_equal(image[3:5, 0:2], np.array([[50, 60], [70, 80]]))


def test_overlay_channel_defaults_follow_imagej_order():
    controller = MIPViewController.__new__(MIPViewController)
    controller.selected_channels = ["CH1", "CH2", "CH3", "CH4"]
    controller.overlay_channel_settings = {}
    controller.min_counts = 0
    controller.max_counts = 65535

    controller._ensure_overlay_channel_settings()

    assert controller.overlay_channel_settings["CH1"]["lut_name"] == "Green"
    assert controller.overlay_channel_settings["CH2"]["lut_name"] == "Red"
    assert controller.overlay_channel_settings["CH3"]["lut_name"] == "Magenta"
    assert controller.overlay_channel_settings["CH4"]["lut_name"] == "Cyan"


def test_compose_overlay_from_channels_adds_colorized_channels():
    controller = MIPViewController.__new__(MIPViewController)
    controller.selected_channels = ["CH1", "CH2"]
    controller.overlay_channel_settings = {
        "CH1": {
            "lut_name": "Red",
            "autoscale": False,
            "min_counts": 0.0,
            "max_counts": 255.0,
        },
        "CH2": {
            "lut_name": "Green",
            "autoscale": False,
            "min_counts": 0.0,
            "max_counts": 255.0,
        },
    }
    controller._overlay_colormap_cache = {}
    controller._overlay_bgr_buf = None
    controller.min_counts = 0.0
    controller.max_counts = 255.0
    controller._prepare_zoom_window = lambda: (slice(None), slice(None))
    controller._crop_image_with_zoom = lambda image, y_slice, x_slice: image[
        y_slice, x_slice
    ]
    controller.down_sample_image = lambda image: image
    controller.add_crosshair = lambda image: image

    image = controller._compose_overlay_from_channels(
        {
            "CH1": np.full((3, 3), 100, dtype=np.uint8),
            "CH2": np.full((3, 3), 50, dtype=np.uint8),
        }
    )

    assert image.shape == (3, 3, 3)
    np.testing.assert_array_equal(image[0, 0], np.array([100, 50, 0], dtype=np.uint8))
    assert controller._last_frame_display_max == 100.0


def test_should_use_overlay_mode_requires_multiple_channels():
    controller = MIPViewController.__new__(MIPViewController)
    controller.display_mode_widgets = {"mode": _Getter("Overlay")}
    controller.selected_channels = ["CH1"]
    assert not controller._should_use_overlay_mode()

    controller.selected_channels = ["CH1", "CH2"]
    assert controller._should_use_overlay_mode()


def test_get_mip_image_uses_compact_active_channel_for_multichannel_single_mode():
    controller = MIPViewController.__new__(MIPViewController)
    controller.selected_channels = ["CH1", "CH2"]
    controller.render_widgets = {
        "perspective": _Getter("XY"),
        "channel": _Getter("CH1"),
    }
    controller._get_multichannel_active_channel = lambda: "CH2"
    controller.flip_image = lambda image: image
    controller.down_sample_image = lambda image, *_: image
    controller.xy_mip = np.array(
        [
            [[1, 2], [3, 4]],
            [[10, 20], [30, 40]],
        ],
        dtype=np.uint16,
    )
    controller.zy_mip = np.zeros((2, 2, 2), dtype=np.uint16)
    controller.zx_mip = np.zeros((2, 2, 2), dtype=np.uint16)

    image = controller.get_mip_image()

    np.testing.assert_array_equal(
        image,
        np.array([[10, 20], [30, 40]], dtype=np.uint16),
    )


def test_collect_mip_overlay_channels_returns_perspective_signatures():
    controller = MIPViewController.__new__(MIPViewController)
    controller.selected_channels = ["CH1", "CH2"]
    controller.render_widgets = {"perspective": _Getter("ZX")}
    controller._mip_channel_revision = {"CH1": 3, "CH2": 7}
    controller._get_mip_projection_for_channel = lambda idx, mode: np.full(
        (2, 2), idx + 1, dtype=np.uint16
    )

    channel_images, channel_signatures = controller._collect_mip_overlay_channels()

    np.testing.assert_array_equal(
        channel_images["CH1"], np.full((2, 2), 1, dtype=np.uint16)
    )
    np.testing.assert_array_equal(
        channel_images["CH2"], np.full((2, 2), 2, dtype=np.uint16)
    )
    assert channel_signatures["CH1"] == ("mip", 0, "ZX", 3)
    assert channel_signatures["CH2"] == ("mip", 1, "ZX", 7)


def test_render_single_multichannel_frame_applies_channel_alpha():
    controller = MIPViewController.__new__(MIPViewController)
    controller.selected_channels = ["CH1"]
    controller.overlay_channel_settings = {
        "CH1": {
            "lut_name": "Red",
            "autoscale": False,
            "min_counts": 0.0,
            "max_counts": 255.0,
            "visible": True,
            "alpha": 0.5,
        }
    }
    controller._overlay_colormap_cache = {}
    controller._colorized_channel_cache = {}
    controller.min_counts = 0.0
    controller.max_counts = 255.0
    controller.canvas_width = 3
    controller.canvas_height = 3
    controller._prepare_zoom_window = lambda: (slice(None), slice(None))
    controller._crop_image_with_zoom = lambda image, y_slice, x_slice: image[
        y_slice, x_slice
    ]
    controller.down_sample_image = lambda image: image
    controller.add_crosshair = lambda image: image

    out = controller._render_single_multichannel_frame(
        "CH1",
        np.full((3, 3), 100, dtype=np.uint8),
        channel_signature=("mip", 0, "XY", 1),
    )

    assert out.shape == (3, 3, 3)
    np.testing.assert_array_equal(out[0, 0], np.array([50, 0, 0], dtype=np.uint8))
    assert controller._last_frame_display_max == 100.0


def test_render_single_multichannel_frame_applies_gamma_mapping():
    controller = MIPViewController.__new__(MIPViewController)
    controller.selected_channels = ["CH1"]
    controller.overlay_channel_settings = {
        "CH1": {
            "lut_name": "Red",
            "autoscale": False,
            "min_counts": 0.0,
            "max_counts": 255.0,
            "visible": True,
            "alpha": 1.0,
            "gamma": 2.0,
        }
    }
    controller._overlay_colormap_cache = {}
    controller._gamma_lut_cache = {}
    controller._colorized_channel_cache = {}
    controller.min_counts = 0.0
    controller.max_counts = 255.0
    controller.canvas_width = 2
    controller.canvas_height = 2
    controller._prepare_zoom_window = lambda: (slice(None), slice(None))
    controller._crop_image_with_zoom = lambda image, y_slice, x_slice: image[
        y_slice, x_slice
    ]
    controller.down_sample_image = lambda image: image
    controller.add_crosshair = lambda image: image

    out = controller._render_single_multichannel_frame(
        "CH1",
        np.full((2, 2), 128, dtype=np.uint8),
        channel_signature=("mip", 0, "XY", 2),
    )

    # gamma=2 maps 128 -> round((128/255)^2*255) = 64, Red LUT => RGB [64, 0, 0]
    np.testing.assert_array_equal(out[0, 0], np.array([64, 0, 0], dtype=np.uint8))


def test_collect_camera_overlay_channels_requires_all_selected_channels():
    controller = CameraViewController.__new__(CameraViewController)
    controller.selected_channels = ["CH1", "CH2"]
    controller.display_state = "Live"
    controller._latest_channel_idx = 0
    controller._latest_slice_idx = 0
    controller._channel_slice_revision = {(0, 0): 1}
    controller._get_overlay_target_slice = lambda: 0
    controller.flip_image = lambda image: image

    def _load_image(channel, slice_index):
        assert slice_index == 0
        return None if channel == 1 else np.full((2, 2), 99, dtype=np.uint16)

    controller.spooled_images = SimpleNamespace(load_image=_load_image)
    channel_images, channel_signatures, all_available = (
        controller._collect_camera_overlay_channels(np.full((2, 2), 7, dtype=np.uint16))
    )

    assert not all_available
    np.testing.assert_array_equal(
        channel_images["CH1"], np.full((2, 2), 7, dtype=np.uint16)
    )
    assert "CH2" not in channel_images
    assert channel_signatures["CH1"] == ("camera", 0, 0, 1)


def test_camera_display_image_overlay_skips_partial_channel_frames():
    controller = CameraViewController.__new__(CameraViewController)
    controller._should_use_overlay_mode = lambda: True
    controller._sync_overlay_cache_from_controls = lambda *_args, **_kwargs: None
    controller._collect_camera_overlay_channels = lambda image: (
        {"CH1": image},
        {"CH1": ("camera", 0, 0, 1)},
        False,
    )
    controller._compose_overlay_from_channels = lambda *_args, **_kwargs: (
        _ for _ in ()
    ).throw(AssertionError("should not compose overlay from incomplete channels"))
    controller.overlay_mask = lambda image: image
    controller.populate_image = MagicMock()
    controller.update_max_counts = MagicMock()
    controller.view = SimpleNamespace(after=lambda *_args, **_kwargs: None)

    controller.display_image(np.full((2, 2), 7, dtype=np.uint16))

    controller.populate_image.assert_not_called()
    controller.update_max_counts.assert_not_called()


def test_move_crosshair_uses_active_display_pipeline_for_selected_channels():
    controller = CameraViewController.__new__(CameraViewController)
    controller.selected_channels = ["CH1", "CH2"]
    controller.zoom_rect = np.array([[0.0, 100.0], [0.0, 50.0]])
    controller.zoom_scale = 1.0
    controller.move_to_x = 25.0
    controller.move_to_y = 10.0
    controller._refresh_after_display_mode_change = MagicMock()
    controller.process_image = MagicMock()

    controller.move_crosshair()

    assert controller.offset_crosshair is True
    assert controller.crosshair_x == 0.25
    assert controller.crosshair_y == 0.2
    controller._refresh_after_display_mode_change.assert_called_once_with()
    controller.process_image.assert_not_called()


def test_reset_display_uses_active_pipeline_for_selected_channels():
    controller = CameraViewController.__new__(CameraViewController)
    controller.selected_channels = ["CH1"]
    controller.canvas_width = 256
    controller.canvas_height = 128
    controller.zoom_width = 20
    controller.zoom_height = 10
    controller.zoom_rect = np.array([[3.0, 11.0], [2.0, 7.0]])
    controller.zoom_offset = np.array([[2.0], [1.0]])
    controller.zoom_value = 1.7
    controller.zoom_scale = 2.5
    controller._refresh_after_display_mode_change = MagicMock()
    controller.process_image = MagicMock()
    controller.offset_crosshair = True
    controller.crosshair_x = 0.1
    controller.crosshair_y = 0.2

    controller.reset_display(display_flag=True, reset_crosshair=False)

    assert controller.zoom_width == 256
    assert controller.zoom_height == 128
    np.testing.assert_array_equal(controller.zoom_rect, np.array([[0, 256], [0, 128]]))
    np.testing.assert_array_equal(controller.zoom_offset, np.array([[0], [0]]))
    assert controller.zoom_value == 1
    assert controller.zoom_scale == 1
    controller._refresh_after_display_mode_change.assert_called_once_with()
    controller.process_image.assert_not_called()


def test_reset_display_without_selected_channels_uses_process_image():
    controller = CameraViewController.__new__(CameraViewController)
    controller.selected_channels = None
    controller.canvas_width = 64
    controller.canvas_height = 64
    controller.image = np.zeros((2, 2), dtype=np.uint16)
    controller._refresh_after_display_mode_change = MagicMock()
    controller.process_image = MagicMock()

    controller.reset_display(display_flag=True, reset_crosshair=True)

    controller.process_image.assert_called_once_with()
    controller._refresh_after_display_mode_change.assert_not_called()
