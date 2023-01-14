# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

# Third Party Imports
import pytest


@pytest.mark.hardware
@pytest.fixture(scope="module")
def prepare_cameras(dummy_model):
    from aslm.model.devices.APIs.hamamatsu.HamamatsuAPI import DCAM, camReg
    from aslm.model.devices.camera.camera_hamamatsu import HamamatsuOrca

    def start_camera(idx=0):
        # open camera
        for i in range(10):
            assert camReg.numCameras == idx
            try:
                camera = DCAM(idx)
                if camera.get_camera_handler() != 0:
                    break
                camera.dev_close()
            except:
                continue
            camera = None
        return camera

    model = dummy_model

    temp = {}
    for microscope_name in model.configuration["configuration"]["microscopes"].keys():
        serial_number = model.configuration["configuration"]["microscopes"][
            microscope_name
        ]["camera"]["hardware"]["serial_number"]
        temp[str(serial_number)] = microscope_name

    camera_connections = {}

    camera = start_camera()
    for i in range(camReg.maxCameras):
        if i > 0:
            camera = start_camera(i)
        if str(camera._serial_number) in temp:
            microscope_name = temp[str(camera._serial_number)]
            camera = HamamatsuOrca(microscope_name, camera, model.configuration)
            camera_connections[microscope_name] = camera

    yield camera_connections

    # close all the cameras
    for k in camera_connections:
        camera_connections[k].camera_controller.dev_close()


@pytest.mark.hardware
class TestHamamatsuOrca:
    r"""Unit Test for HamamamatsuOrca Class"""
    model = None

    @pytest.fixture(autouse=True)
    def _prepare_test(self, dummy_model, prepare_cameras):
        self.num_of_tests = 10
        self.model = dummy_model
        self.cameras = prepare_cameras

        self.microscope_name = self.model.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        self.camera = self.cameras[self.microscope_name]

    def is_in_range(self, value, target, precision=100):
        target_min = target - target / precision
        target_max = target + target / precision
        return value > target_min and value < target_max

    def test_hamamatsu_camera_attributes(self):
        from aslm.model.devices.camera.camera_hamamatsu import HamamatsuOrca

        attributes = dir(HamamatsuOrca)
        desired_attributes = [
            "serial_number",
            "report_settings",
            "close_camera",
            "set_sensor_mode",
            "set_readout_direction",
            "calculate_light_sheet_exposure_time",
            "calculate_readout_time",
            "set_exposure_time",
            "set_line_interval",
            "set_binning",
            "set_ROI",
            "initialize_image_series",
            "close_image_series",
            "get_new_frame",
            "get_minimum_waiting_time",
        ]

        for da in desired_attributes:
            assert da in attributes

    def test_init_camera(self):
        for microscope_name in self.model.configuration["configuration"][
            "microscopes"
        ].keys():

            camera = self.cameras[microscope_name]

            assert camera != None, f"Should start the camera {microscope_name}"

            camera_controller = camera.camera_controller
            camera_configs = self.model.configuration["configuration"]["microscopes"][
                microscope_name
            ]["camera"]

            # serial number
            assert str(camera_controller._serial_number) == str(
                camera_configs["hardware"]["serial_number"]
            ), f"the camera serial number isn't right for {microscope_name}!"
            assert str(camera.serial_number) == str(
                camera_configs["hardware"]["serial_number"]
            ), f"the camera serial number isn't right for {microscope_name}!"

            # verify camera is initialized with the attributes from configuration.yaml
            parameters = [
                "defect_correct_mode",
                "readout_speed",
                "trigger_active",
                "trigger_mode",
                "trigger_polarity",
                "trigger_source",
            ]
            for parameter in parameters:
                value = camera_controller.get_property_value(parameter)
                assert value == camera_configs[parameter]

            # sensor mode
            sensor_mode = camera_controller.get_property_value("sensor_mode")
            expected_value = 1 if camera_configs["sensor_mode"] == "Normal" else 12
            assert sensor_mode == expected_value, "Sensor mode isn't right!"

            # exposure time
            exposure_time = camera_controller.get_property_value("exposure_time")
            assert self.is_in_range(
                exposure_time, camera_configs["exposure_time"] / 1000, 10
            ), "Exposure time isn't right!"

            # binning
            binning = camera_controller.get_property_value("binning")
            assert int(binning) == int(
                camera_configs["binning"][0]
            ), "Binning isn't right!"

            # image width and height
            width = camera_controller.get_property_value("image_width")
            assert width == camera_configs["x_pixels"], "image width isn't right"
            height = camera_controller.get_property_value("image_height")
            assert height == camera_configs["y_pixels"], "image height isn't right"

    def test_set_sensor_mode(self):
        modes = {"Normal": 1, "Light-Sheet": 12, "RandomMode": None}
        for mode in modes:
            pre_value = self.camera.camera_controller.get_property_value("sensor_mode")
            self.camera.set_sensor_mode(mode)
            value = self.camera.camera_controller.get_property_value("sensor_mode")
            if modes[mode] != None:
                assert value == modes[mode], f"sensor mode {mode} isn't right!"
            else:
                assert value == pre_value, f"sensor mode shouldn't be set!"

    def test_set_readout_direction(self):
        readout_directions = {"Top-to-Bottom": 1, "Bottom-to-Top": 2}
        for direction in readout_directions:
            self.camera.set_readout_direction(direction)
            value = self.camera.camera_controller.get_property_value(
                "readout_direction"
            )
            assert (
                value == readout_directions[direction]
            ), f"readout direction setting isn't right for {direction}"

    # def test_calculate_readout_time(self):
    #     pass

    def test_set_exposure_time(self):
        import random

        modes_dict = {
            "Normal": 10000,
            "Light-Sheet": 20,
        }
        for mode in modes_dict:
            self.camera.set_sensor_mode(mode)
            for i in range(self.num_of_tests):
                exposure_time = random.randint(1, modes_dict[mode])
                self.camera.set_exposure_time(exposure_time)
                value = self.camera.camera_controller.get_property_value(
                    "exposure_time"
                )
                assert self.is_in_range(
                    value, exposure_time / 1000, 10
                ), f"exposure time({exposure_time}) isn't right!"
        self.camera.set_sensor_mode("Normal")

    def test_set_line_interval(self):
        import random

        self.camera.set_sensor_mode("Light-Sheet")
        for i in range(self.num_of_tests):
            line_interval = random.random() / 10.0
            r = self.camera.set_line_interval(line_interval)
            if r is True:
                value = self.camera.camera_controller.get_property_value(
                    "internal_line_interval"
                )
                assert self.is_in_range(
                    value, line_interval
                ), f"line interval {line_interval} isn't right! {value}"
        self.camera.set_sensor_mode("Normal")

    def test_set_binning(self):
        import random

        binning_dict = {
            "1x1": 1,
            "2x2": 2,
            "4x4": 4,
            # '8x8': 8,
            # '16x16': 16,
            # '1x2': 102,
            # '2x4': 204
        }
        for binning_string in binning_dict:
            self.camera.set_binning(binning_string)
            value = self.camera.camera_controller.get_property_value("binning")
            assert (
                int(value) == binning_dict[binning_string]
            ), f"binning {binning_string} isn't right!"

        for i in range(self.num_of_tests):
            x = random.randint(1, 20)
            y = random.randint(1, 20)
            binning_string = f"{x}x{y}"
            assert self.camera.set_binning(binning_string) == (
                binning_string in binning_dict
            )

    def test_set_ROI(self):
        import random

        self.camera.set_binning("1x1")
        width = self.camera.camera_parameters["x_pixels"]
        height = self.camera.camera_parameters["x_pixels"]
        w = self.camera.camera_controller.get_property_value("image_width")
        h = self.camera.camera_controller.get_property_value("image_height")
        assert width == w, f"maximum width should be the same {width} - {w}"
        assert height == h, f"maximum height should be the same {height} -{h}"

        for i in range(self.num_of_tests):
            pre_x, pre_y = self.camera.x_pixels, self.camera.y_pixels
            x = random.randint(1, self.camera.camera_parameters["x_pixels"])
            y = random.randint(1, self.camera.camera_parameters["y_pixels"])
            r = self.camera.set_ROI(y, x)
            if x % 2 == 1 or y % 2 == 1:
                assert r == False
                assert self.camera.x_pixels == pre_x, "width shouldn't be chaged!"
                assert self.camera.y_pixels == pre_y, "height shouldn't be changed!"
            else:
                top = (height - y) / 2
                bottom = top + y - 1
                if top % 2 == 1 or bottom % 2 == 0:
                    assert r == False
                else:
                    assert (
                        r == True
                    ), f"try to set{x}x{y}, but get {self.camera.x_pixels}x{self.camera.y_pixels}"
                    assert (
                        self.camera.x_pixels == x
                    ), f"trying to set {x}x{y}. width should be changed to {x}"
                    assert self.camera.y_pixels == y, f"height should be chagned to {y}"

        self.camera.set_ROI(512, 512)
        assert self.camera.x_pixels == 512
        assert self.camera.y_pixels == 512

        self.camera.set_ROI(
            self.camera.camera_parameters["x_pixels"],
            self.camera.camera_parameters["y_pixels"],
        )
        assert self.camera.x_pixels == self.camera.camera_parameters["x_pixels"]
        assert self.camera.y_pixels == self.camera.camera_parameters["y_pixels"]

        self.camera.set_ROI(
            self.camera.camera_parameters["x_pixels"] + 100,
            self.camera.camera_parameters["y_pixels"] + 100,
        )
        assert self.camera.x_pixels == self.camera.camera_parameters["x_pixels"]
        assert self.camera.y_pixels == self.camera.camera_parameters["y_pixels"]

    def test_acquire_image(self):
        import random
        import time
        from aslm.model.concurrency.concurrency_tools import SharedNDArray

        # set software trigger
        self.camera.camera_controller.set_property_value("trigger_source", 3)

        assert self.camera.is_acquiring == False

        number_of_frames = 100
        data_buffer = [
            SharedNDArray(shape=(2048, 2048), dtype="uint16")
            for i in range(number_of_frames)
        ]

        # initialize without release/close the camera
        self.camera.initialize_image_series(data_buffer, number_of_frames)
        assert self.camera.is_acquiring == True

        self.camera.initialize_image_series(data_buffer, number_of_frames)
        assert self.camera.is_acquiring == True

        exposure_time = self.camera.camera_controller.get_property_value(
            "exposure_time"
        )
        readout_time = self.camera.camera_controller.get_property_value("readout_time")

        for i in range(self.num_of_tests):
            triggers = random.randint(1, 100)
            for j in range(triggers):
                self.camera.camera_controller.fire_software_trigger()
                time.sleep(exposure_time + readout_time)

            time.sleep(0.01)
            frames = self.camera.get_new_frame()
            assert len(frames) == triggers

        self.camera.close_image_series()
        assert self.camera.is_acquiring == False

        for i in range(self.num_of_tests):
            self.camera.initialize_image_series(data_buffer, number_of_frames)
            assert self.camera.is_acquiring == True
            self.camera.close_image_series()
            assert self.camera.is_acquiring == False

        # close a closed camera
        self.camera.close_image_series()
        self.camera.close_image_series()
        assert self.camera.is_acquiring == False
