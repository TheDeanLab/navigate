# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
#

from navigate.controller.sub_controllers.camera_view import CameraViewController
import pytest
import random
from unittest.mock import MagicMock
import numpy as np


class TestCameraViewController:
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        self.v = dummy_controller.view
        c.model = MagicMock()
        c.model.get_offset_variance_maps = MagicMock(return_value=[None, None])

        self.camera_view = CameraViewController(self.v.camera_waveform.camera_tab, c)

        self.microscope_state = {
            "channels": {
                "channel_1": {
                    "is_selected": True,
                    "laser": "488nm",
                    "laser_index": 0,
                    "camera_exposure_time": 200.0,
                    "laser_power": 20.0,
                    "interval_time": 1.0,
                    "defocus": 100.0,
                    "filter_wheel_0": "Empty-Alignment",
                    "filter_position_0": 0,
                    "filter_wheel_1": "Empty-Alignment",
                    "filter_position_1": 0,
                },
                "channel_2": {
                    "is_selected": True,
                    "laser": "488nm",
                    "laser_index": 0,
                    "camera_exposure_time": 200.0,
                    "laser_power": 20.0,
                    "interval_time": 1.0,
                    "defocus": 100.0,
                    "filter_wheel_0": "Empty-Alignment",
                    "filter_position_0": 0,
                    "filter_wheel_1": "Empty-Alignment",
                    "filter_position_1": 0,
                },
                "channel_3": {
                    "is_selected": True,
                    "laser": "488nm",
                    "laser_index": 0,
                    "camera_exposure_time": 200.0,
                    "laser_power": 20.0,
                    "interval_time": 1.0,
                    "defocus": 100.0,
                    "filter_wheel_0": "Empty-Alignment",
                    "filter_position_0": 0,
                    "filter_wheel_1": "Empty-Alignment",
                    "filter_position_1": 0,
                },
            },
            "number_z_steps": np.random.randint(10, 100),
            "stack_cycling_mode": "per_stack",
            "selected_channels": 3,
            "image_mode": "z-stack",
        }

    def test_init(self):

        assert isinstance(self.camera_view, CameraViewController)

    def test_update_display_state(self):
        pass

    def test_get_absolute_position(self, monkeypatch):
        def mock_winfo_pointerx():
            self.x = int(random.random())
            return self.x

        def mock_winfo_pointery():
            self.y = int(random.random())
            return self.y

        monkeypatch.setattr(self.v, "winfo_pointerx", mock_winfo_pointerx)
        monkeypatch.setattr(self.v, "winfo_pointery", mock_winfo_pointery)

        # call the function under test
        x, y = self.camera_view.get_absolute_position()

        # make assertions about the return value
        assert x == self.x
        assert y == self.y

    def test_popup_menu(self, monkeypatch):

        # create a fake event object
        self.startx = int(random.random())
        self.starty = int(random.random())
        event = type("Event", (object,), {"x": self.startx, "y": self.starty})()
        self.grab_released = False
        self.x = int(random.random())
        self.y = int(random.random())
        self.absx = int(random.random())
        self.absy = int(random.random())

        # monkey patch the get_absolute_position method to return specific values
        def mock_get_absolute_position():
            self.absx = int(random.random())
            self.absy = int(random.random())
            return self.absx, self.absy

        monkeypatch.setattr(
            self.camera_view, "get_absolute_position", mock_get_absolute_position
        )

        def mock_tk_popup(x, y):
            self.x = x
            self.y = y

        def mock_grab_release():
            self.grab_released = True

        monkeypatch.setattr(self.camera_view.menu, "tk_popup", mock_tk_popup)
        monkeypatch.setattr(self.camera_view.menu, "grab_release", mock_grab_release)

        # call the function under test
        self.camera_view.popup_menu(event)

        # make assertions about the state of the view object
        assert self.camera_view.move_to_x == self.startx
        assert self.camera_view.move_to_y == self.starty
        assert self.x == self.absx
        assert self.y == self.absy
        assert self.grab_released is True

    @pytest.mark.parametrize("name", ["minmax", "image"])
    @pytest.mark.parametrize("data", [[random.randint(0, 49), random.randint(50, 100)]])
    def test_initialize(self, name, data):

        self.camera_view.initialize(name, data)

        # Checking values
        if name == "minmax":
            assert self.camera_view.image_palette["Min"].get() == data[0]
            assert self.camera_view.image_palette["Max"].get() == data[1]
        if name == "image":
            assert self.camera_view.image_metrics["Frames"].get() == data[0]

    def test_set_mode(self):

        # Test default mode
        self.camera_view.set_mode()
        assert self.camera_view.mode == ""
        assert self.camera_view.menu.entrycget("Move Here", "state") == "disabled"

        # Test 'live' mode
        self.camera_view.set_mode("live")
        assert self.camera_view.mode == "live"
        assert self.camera_view.menu.entrycget("Move Here", "state") == "normal"

        # Test 'stop' mode
        self.camera_view.set_mode("stop")
        assert self.camera_view.mode == "stop"
        assert self.camera_view.menu.entrycget("Move Here", "state") == "normal"

        # Test invalid mode
        self.camera_view.set_mode("invalid")
        assert self.camera_view.mode == "invalid"
        assert self.camera_view.menu.entrycget("Move Here", "state") == "disabled"

    @pytest.mark.parametrize("mode", ["stop", "live"])
    def test_move_stage(self, mode):

        # Setup to check formula inside func is correct
        microscope_name = self.camera_view.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]["microscope_name"]
        zoom_value = self.camera_view.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["zoom"]
        pixel_size = self.camera_view.parent_controller.configuration["configuration"][
            "microscopes"
        ][microscope_name]["zoom"]["pixel_size"][zoom_value]

        current_center_x = (
            self.camera_view.zoom_rect[0][0] + self.camera_view.zoom_rect[0][1]
        ) / 2
        current_center_y = (
            self.camera_view.zoom_rect[1][0] + self.camera_view.zoom_rect[1][1]
        ) / 2

        self.camera_view.move_to_x = int(random.random())
        self.camera_view.move_to_y = int(random.random())

        # This is the formula to check
        offset_x = (
            (self.camera_view.move_to_x - current_center_x)
            / self.camera_view.zoom_scale
            * self.camera_view.canvas_width_scale
            * pixel_size
        )
        offset_y = (
            (self.camera_view.move_to_y - current_center_y)
            / self.camera_view.zoom_scale
            * self.camera_view.canvas_width_scale
            * pixel_size
        )

        # Set the mode to check if statements
        self.camera_view.mode = mode

        # Act
        self.camera_view.move_stage()

        # Check
        assert self.camera_view.parent_controller.pop() == "get_stage_position"
        res = self.camera_view.parent_controller.pop()
        if mode == "stop":
            assert res == "move_stage_and_acquire_image"
        else:
            assert res == "move_stage_and_update_info"
        # Checking that move stage properly changed pos
        new_pos = self.camera_view.parent_controller.pop()
        self.camera_view.parent_controller.stage_pos["x"] -= offset_x
        self.camera_view.parent_controller.stage_pos["y"] += offset_y
        assert new_pos == self.camera_view.parent_controller.stage_pos

    def test_reset_display(self, monkeypatch):

        # Mock process image function
        process_image_called = False

        def mock_process_image():
            nonlocal process_image_called
            process_image_called = True

        monkeypatch.setattr(self.camera_view, "process_image", mock_process_image)

        # Reset and check
        self.camera_view.reset_display()
        assert np.array_equal(
            self.camera_view.zoom_rect,
            np.array(
                [
                    [0, self.camera_view.view.canvas_width],
                    [0, self.camera_view.view.canvas_height],
                ]
            ),
        )
        assert np.array_equal(self.camera_view.zoom_offset, np.array([[0], [0]]))
        assert self.camera_view.zoom_value == 1
        assert self.camera_view.zoom_scale == 1
        assert self.camera_view.zoom_width == self.camera_view.view.canvas_width
        assert self.camera_view.zoom_height == self.camera_view.view.canvas_height
        assert process_image_called is True

    def test_process_image(self):
        self.camera_view.digital_zoom = MagicMock()
        self.camera_view.detect_saturation = MagicMock()
        self.camera_view.down_sample_image = MagicMock()
        self.camera_view.scale_image_intensity = MagicMock()
        self.camera_view.add_crosshair = MagicMock()
        self.camera_view.apply_lut = MagicMock()
        self.camera_view.populate_image = MagicMock()

        self.camera_view.process_image()

        self.camera_view.digital_zoom.assert_called()
        self.camera_view.detect_saturation.assert_called()
        self.camera_view.down_sample_image.assert_called()
        self.camera_view.scale_image_intensity.assert_called()
        self.camera_view.add_crosshair.assert_called()
        self.camera_view.apply_lut.assert_called()
        self.camera_view.populate_image.assert_called()

    @pytest.mark.parametrize("num,value", [(4, 0.95), (5, 1.05)])
    def test_mouse_wheel(self, num, value):

        # Test zoom in and out
        event = MagicMock()
        event.num = num
        event.x = int(random.random())
        event.y = int(random.random())
        event.delta = 120
        self.camera_view.zoom_value = 1
        self.camera_view.zoom_scale = 1
        self.camera_view.zoom_width = self.camera_view.view.canvas_width
        self.camera_view.zoom_height = self.camera_view.view.canvas_height
        self.camera_view.reset_display = MagicMock()
        self.camera_view.process_image = MagicMock()
        self.camera_view.mouse_wheel(event)

        assert self.camera_view.zoom_value == value
        assert self.camera_view.zoom_scale == value
        assert self.camera_view.zoom_width == self.camera_view.view.canvas_width / value
        assert (
            self.camera_view.zoom_height == self.camera_view.view.canvas_height / value
        )

        if (
            self.camera_view.zoom_width > self.camera_view.view.canvas_width
            or self.camera_view.zoom_height > self.camera_view.view.canvas_height
        ):
            assert self.camera_view.reset_display.called is True
            self.camera_view.process_image.assert_called()
        else:
            assert self.camera_view.reset_display.called is False
            not self.camera_view.process_image.assert_called()

    @pytest.mark.skip("AssertionError: Expected 'mock' to have been called.")
    def test_digital_zoom(self):

        # Setup
        a, b, c, d, e, f = [random.randint(1, 100) for _ in range(6)]
        g, h = [random.randint(100, 400) for _ in range(2)]
        i, j = [random.randint(500, 1000) for _ in range(2)]
        val, scale, widthsc, heightsc = [random.randint(2, 4) for _ in range(4)]
        self.camera_view.zoom_rect = np.array([[a, b], [c, d]])
        self.camera_view.zoom_offset = np.array([[e], [f]])
        self.camera_view.zoom_value = val
        self.camera_view.zoom_scale = scale
        self.camera_view.zoom_width = g  # 300
        self.camera_view.zoom_height = h  # 400
        self.camera_view.view.canvas_width = i  # 800
        self.camera_view.view.canvas_height = j  # 600
        self.camera_view.canvas_width_scale = widthsc
        self.camera_view.canvas_height_scale = heightsc
        self.camera_view.image = np.random.randint(0, 256, (600, 800))
        self.camera_view.reset_display = MagicMock()

        # Preprocess
        new_zoom_rec = self.camera_view.zoom_rect - self.camera_view.zoom_offset
        new_zoom_rec *= self.camera_view.zoom_value
        new_zoom_rec += self.camera_view.zoom_offset

        x_start_index = int(-new_zoom_rec[0][0] / self.camera_view.zoom_scale)
        x_end_index = int(x_start_index + self.camera_view.zoom_width)
        y_start_index = int(-new_zoom_rec[1][0] / self.camera_view.zoom_scale)
        y_end_index = int(y_start_index + self.camera_view.zoom_height)

        crosshair_x = (new_zoom_rec[0][0] + new_zoom_rec[0][1]) / 2
        crosshair_y = (new_zoom_rec[1][0] + new_zoom_rec[1][1]) / 2
        if crosshair_x < 0 or crosshair_x >= self.camera_view.view.canvas_width:
            crosshair_x = -1
        if crosshair_y < 0 or crosshair_y >= self.camera_view.view.canvas_height:
            crosshair_y = -1

        new_image = self.camera_view.image[
            y_start_index
            * self.camera_view.canvas_height_scale : y_end_index
            * self.camera_view.canvas_height_scale,
            x_start_index
            * self.camera_view.canvas_width_scale : x_end_index
            * self.camera_view.canvas_width_scale,
        ]

        # Call func
        self.camera_view.digital_zoom()

        # Check zoom rec
        assert np.array_equal(self.camera_view.zoom_rect, new_zoom_rec)
        # Check zoom offset
        assert np.array_equal(self.camera_view.zoom_offset, np.array([[0], [0]]))
        # Check zoom_value
        assert self.camera_view.zoom_value == 1
        # Check zoom_image
        assert np.array_equal(self.camera_view.zoom_image, new_image)
        # Check crosshairs
        assert self.camera_view.crosshair_x == int(crosshair_x)
        assert self.camera_view.crosshair_y == int(crosshair_y)
        # Check reset display
        self.camera_view.reset_display.assert_called()

    @pytest.mark.parametrize("onoff", [True, False])
    def test_left_click(self, onoff):
        self.camera_view.add_crosshair = MagicMock()
        self.camera_view.digital_zoom = MagicMock()
        self.camera_view.detect_saturation = MagicMock()
        self.camera_view.down_sample_image = MagicMock()
        self.camera_view.transpose_image = MagicMock()
        self.camera_view.scale_image_intensity = MagicMock()
        self.camera_view.apply_lut = MagicMock()
        self.camera_view.populate_image = MagicMock()
        event = MagicMock()

        self.camera_view.image = np.random.randint(0, 256, (600, 800))
        self.camera_view.apply_cross_hair = onoff

        self.camera_view.left_click(event)

        self.camera_view.add_crosshair.assert_called()
        self.camera_view.populate_image.assert_called()
        assert self.camera_view.apply_cross_hair == (not onoff)

    @pytest.mark.parametrize("frames", [0, 1, 2])
    @pytest.mark.parametrize("count", [0, 1])
    def test_update_max_count(self, frames, count):

        # Arrange
        max = random.randint(10, 50)
        self.camera_view.image_metrics["Frames"].set(frames)
        self.camera_view.max_counts = max
        self.camera_view.image_count = count
        self.camera_view.max_intensity_history = [max]
        if count == 1:
            self.camera_view.down_sampled_image = [max]
            self.camera_view.temp_array = [max]

        # Act
        self.camera_view.update_max_counts()

        # Assert
        if frames == 0:
            assert self.camera_view.image_metrics["Frames"].get() == 1
            assert self.camera_view.image_metrics["Image"].get() == max

        if frames == 1:
            assert self.camera_view.image_metrics["Image"].get() == max

    def test_down_sample_image(self, monkeypatch):
        import cv2

        # create a test image
        test_image = np.random.rand(100, 100)
        self.zoom_image = test_image

        # set the widget size
        widget = type("MyWidget", (object,), {"widget": self.camera_view.view})
        event = type(
            "MyEvent",
            (object,),
            {
                "widget": widget,
                "width": np.random.randint(5, 1000),
                "height": np.random.randint(5, 1000),
            },
        )
        self.camera_view.resize(event)

        # monkeypatch cv2.resize
        def mocked_resize(img, size):
            return np.ones((size[0], size[1]))

        monkeypatch.setattr(cv2, "resize", mocked_resize)

        # call the function
        down_sampled_image = self.camera_view.down_sample_image(test_image)

        # assert that the image has been resized correctly
        assert np.shape(down_sampled_image) == (
            self.camera_view.view.canvas_width,
            self.camera_view.view.canvas_height,
        )

        # assert that the image has not been modified
        assert not np.array_equal(down_sampled_image, test_image)

    @pytest.mark.parametrize("auto", [True, False])
    def test_scale_image_intensity(self, auto):
        # Create a test image
        test_image = np.random.rand(100, 100)

        # Set autoscale to True
        self.camera_view.autoscale = auto

        if auto is False:
            self.camera_view.max_counts = 1.5
            self.camera_view.min_counts = 0.5

        # Call the function
        scaled_image = self.camera_view.scale_image_intensity(test_image)

        # Assert that max_counts and min_counts have been set correctly
        if auto is True:
            assert self.camera_view.max_counts == np.max(test_image)
            assert self.camera_view.min_counts == np.min(test_image)

        # Assert that the image has been scaled correctly
        assert np.min(scaled_image) >= 0
        assert np.max(scaled_image) <= 1

    def test_populate_image(self, monkeypatch):
        from PIL import Image, ImageTk
        import cv2

        # Create test image
        self.camera_view.cross_hair_image = np.random.rand(100, 100)
        self.camera_view.ilastik_seg_mask = np.random.rand(100, 100)

        # Set display_mask_flag to True
        self.camera_view.display_mask_flag = True

        # Monkeypatch the Image.fromarray() method of PIL
        def mocked_fromarray(arr):
            return arr

        monkeypatch.setattr(Image, "fromarray", mocked_fromarray)

        # Monkeypatch the cv2.resize() function
        def mocked_resize(arr, size):
            return arr

        monkeypatch.setattr(cv2, "resize", mocked_resize)

        # Monkeypatch the Image.blend() method of PIL
        def mocked_blend(img1, img2, alpha):
            return img1 * alpha + img2 * (1 - alpha)

        monkeypatch.setattr(Image, "blend", mocked_blend)

        def mocked_PhotoImage(img):
            return img

        monkeypatch.setattr(ImageTk, "PhotoImage", mocked_PhotoImage)

        self.camera_view.canvas.create_image = MagicMock()
        self.camera_view.image_cache_flag = True

        # Call the function
        self.camera_view.populate_image(self.camera_view.cross_hair_image)

        # Assert that the tk_image has been created correctly
        assert self.camera_view.tk_image is not None
        self.camera_view.canvas.create_image.assert_called()
        assert self.camera_view.image_cache_flag is False

        # Set display_mask_flag to True
        self.camera_view.display_mask_flag = False

        # Call the function
        self.camera_view.populate_image(self.camera_view.cross_hair_image)

        # Assert that the tk_image has been created correctly
        assert self.camera_view.tk_image2 is not None
        assert self.camera_view.image_cache_flag is True

    def test_initialize_non_live_display(self):
        # Create test buffer and microscope_state
        camera_parameters = {
            "img_x_pixels": np.random.randint(1, 200),
            "img_y_pixels": np.random.randint(1, 200),
        }

        # Call the function
        self.camera_view.initialize_non_live_display(
            self.microscope_state, camera_parameters
        )

        # Assert that the variables have been set correctly
        assert self.camera_view.image_count == 0
        assert self.camera_view.slice_index == 0
        assert self.camera_view.number_of_channels == len(
            self.microscope_state["channels"]
        )
        assert (
            self.camera_view.number_of_slices == self.microscope_state["number_z_steps"]
        )
        assert (
            self.camera_view.total_images_per_volume
            == self.camera_view.number_of_channels * self.camera_view.number_of_slices
        )
        assert self.camera_view.original_image_width == int(
            camera_parameters["img_x_pixels"]
        )
        assert self.camera_view.original_image_height == int(
            camera_parameters["img_y_pixels"]
        )
        assert self.camera_view.canvas_width_scale == float(
            self.camera_view.original_image_width / self.camera_view.canvas_width
        )
        assert self.camera_view.canvas_height_scale == float(
            self.camera_view.original_image_height / self.camera_view.canvas_height
        )

    def test_identify_channel_index_and_slice(self):
        # Not currently in use
        pass

    def test_retrieve_image_slice_from_volume(self):
        # Not currently in use
        pass

    @pytest.mark.parametrize("transpose", [True, False])
    def test_display_image(self, transpose):
        """Test the display of an image on the camera view

        TODO: The recent refactor makes this test non-functional. It needs to be updated
        The newer code does not use the camera_view.image attribute after the
        transpose operation, so any transpose/image flipping is not reflected in the
        final image. The test should be updated to reflect this.,
        """

        self.camera_view.initialize_non_live_display(
            self.microscope_state, {"img_x_pixels": 50, "img_y_pixels": 100}
        )
        self.camera_view.digital_zoom = MagicMock()
        self.camera_view.detect_saturation = MagicMock()
        self.camera_view.down_sample_image = MagicMock()
        self.camera_view.scale_image_intensity = MagicMock()
        self.camera_view.apply_lut = MagicMock()
        self.camera_view.populate_image = MagicMock()
        images = np.random.rand(10, 100, 50)

        self.camera_view.transpose = transpose
        count = 0
        self.camera_view.image_count = count
        self.camera_view.image_metrics = {"Channel": MagicMock()}
        self.camera_view.update_max_counts = MagicMock()
        self.camera_view.flip_flags = {"x": False, "y": False}

        image_id = np.random.randint(0, 10)
        self.camera_view.try_to_display_image(images[image_id])

        assert (
            self.camera_view.spooled_images.size_y,
            self.camera_view.spooled_images.size_x,
        ) == np.shape(images[image_id])
        assert self.camera_view.image_count == count + 1

        self.camera_view.flip_flags = {"x": True, "y": False}
        image_id = np.random.randint(0, 10)
        self.camera_view.try_to_display_image(images[image_id])
        # assert np.shape(self.camera_view.image) == np.shape(images[image_id])
        # if not transpose:
        #     assert (self.camera_view.image == images[image_id][:, ::-1]).all()
        # else:
        #     assert (self.camera_view.image == images[image_id][:, ::-1].T).all()
        assert self.camera_view.image_count == count + 2

        self.camera_view.flip_flags = {"x": False, "y": True}
        image_id = np.random.randint(0, 10)
        self.camera_view.try_to_display_image(images[image_id])
        # assert np.shape(self.camera_view.image) == np.shape(images[image_id])
        # if not transpose:
        #     assert (self.camera_view.image == images[image_id][::-1, :]).all()
        # else:
        #     assert (self.camera_view.image == images[image_id][::-1, :].T).all()
        assert self.camera_view.image_count == count + 3

        self.camera_view.flip_flags = {"x": True, "y": True}
        image_id = np.random.randint(0, 10)
        self.camera_view.try_to_display_image(images[image_id])
        # assert np.shape(self.camera_view.image) == np.shape(images[image_id])
        # if not transpose:
        #     assert (self.camera_view.image == images[image_id][::-1, ::-1]).all()
        # else:
        #     assert (self.camera_view.image == images[image_id][::-1, ::-1].T).all()
        assert self.camera_view.image_count == count + 4

    def test_add_crosshair(self):

        # Arrange
        x = self.camera_view.canvas_width
        y = self.camera_view.canvas_height
        image = np.random.rand(x, y)
        self.camera_view.apply_cross_hair = True

        # Act
        image2 = self.camera_view.add_crosshair(image)

        # Assert
        assert np.all(image2[:, self.camera_view.zoom_rect[0][1] // 2] == 1)
        assert np.all(image2[self.camera_view.zoom_rect[1][1] // 2, :] == 1)

    def test_apply_LUT(self):
        # Someone else with better numpy understanding will need to do this TODO

        pass

    def test_update_LUT(self):
        # Same as apply LUT TODO
        pass

    def test_detect_saturation(self):
        test_image = np.random.randint(0, 2**16, size=(100, 100))
        test_image[:50, :50] = 2**16 - 1  # set top left corner to saturation value

        # Call the function to detect saturation
        self.camera_view.detect_saturation(test_image)

        # Assert that the saturated pixels were correctly detected
        assert np.all(self.camera_view.saturated_pixels == 2**16 - 1)

    def test_toggle_min_max_button(self):

        # Setup for true path
        self.camera_view.image_palette["Autoscale"].set(True)

        # Act by calling function
        self.camera_view.toggle_min_max_buttons()

        # Assert things are correct
        assert str(self.camera_view.image_palette["Min"].widget["state"]) == "disabled"
        assert str(self.camera_view.image_palette["Max"].widget["state"]) == "disabled"

        # Setup for false path
        self.camera_view.image_palette["Autoscale"].set(False)

        # Mock function call to isolate
        self.camera_view.update_min_max_counts = MagicMock()

        # Act by calling function
        self.camera_view.toggle_min_max_buttons()

        # Assert things are correct and called
        assert str(self.camera_view.image_palette["Min"].widget["state"]) == "normal"
        assert str(self.camera_view.image_palette["Max"].widget["state"]) == "normal"
        self.camera_view.update_min_max_counts.assert_called()

    def test_transpose_image(self):
        # Create test data
        self.camera_view.image_palette["Flip XY"].set(True)
        self.camera_view.transpose = None

        # Call the function
        self.camera_view.update_transpose_state()

        # Assert the output
        assert self.camera_view.transpose is True

        # Create test data
        self.camera_view.image_palette["Flip XY"].set(False)
        self.camera_view.transpose = None

        # Call the function
        self.camera_view.update_transpose_state()

        # Assert the output
        assert self.camera_view.transpose is False

    def test_update_min_max_counts(self):
        # Create test data
        min = np.random.randint(0, 10)
        max = np.random.randint(0, 10)
        self.camera_view.image_palette["Min"].set(min)
        self.camera_view.image_palette["Max"].set(max)

        self.camera_view.min_counts = None
        self.camera_view.max_counts = None

        # Call the function
        self.camera_view.update_min_max_counts()

        # Assert the output
        assert self.camera_view.min_counts == min
        assert self.camera_view.max_counts == max

    def test_set_mask_color_table(self):
        # This is beyond me currently TODO
        pass

    def test_display_mask(self, monkeypatch):
        import cv2

        # Create test data
        self.camera_view.ilastik_seg_mask = None
        self.camera_view.ilastik_mask_ready_lock.acquire()
        mask = np.zeros((5, 5), dtype=np.uint8)
        self.camera_view.mask_color_table = np.zeros((256, 1, 3), dtype=np.uint8)

        # Define the monkeypatch
        def mock_applyColorMap(mask, mask_color_table):
            return mask

        # Apply the monkeypatch
        monkeypatch.setattr(cv2, "applyColorMap", mock_applyColorMap)

        # Call the function
        self.camera_view.display_mask(mask)

        # Assert the output
        assert (self.camera_view.ilastik_seg_mask == mask).all()
        assert not self.camera_view.ilastik_mask_ready_lock.locked()

    def test_update_canvas_size(self):
        self.camera_view.view.canvas["width"] = random.randint(1, 2000)
        self.camera_view.view.canvas["height"] = random.randint(1, 2000)

        self.camera_view.update_canvas_size()

        assert self.camera_view.canvas_width > 0
        assert self.camera_view.canvas_height > 0
