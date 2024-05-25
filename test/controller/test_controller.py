from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# @pytest.fixture(scope="session")
# def controller_root():
#     import tkinter as tk

#     root = tk.Tk()
#     yield root
#     root.destroy()


class DummySplashScreen:
    def destroy(self):
        pass


@pytest.fixture(scope="session")
def controller(tk_root):
    from navigate.controller.controller import Controller

    base_directory = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "src", "navigate"
    )
    configuration_directory = Path.joinpath(base_directory, "config")

    configuration_path = Path.joinpath(configuration_directory, "configuration.yaml")
    experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
    waveform_constants_path = Path.joinpath(
        configuration_directory, "waveform_constants.yml"
    )
    rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")
    waveform_templates_path = Path.joinpath(
        configuration_directory, "waveform_templates.yml"
    )
    args = SimpleNamespace(synthetic_hardware=True)

    controller = Controller(
        tk_root,
        DummySplashScreen(),
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        args,
    )
    # To make sure the testcases won't hang on because of the model.event_queue
    # The changes here won't affect other testcases,
    # because the testcases from other files use DummyController
    # and DummyModel instead of this controller fixture
    controller.model = MagicMock()
    controller.threads_pool = MagicMock()
    controller.model.get_offset_variance_maps.return_value = (None, None)

    yield controller

    try:
        controller.execute("exit")
    except SystemExit:
        pass


def test_update_buffer(controller):
    camera_parameters = controller.configuration["experiment"]["CameraParameters"]
    controller.update_buffer()
    assert controller.img_width == camera_parameters["img_x_pixels"]
    assert controller.img_height == camera_parameters["img_y_pixels"]

    # Make sure that the get_data_buffer method is not called.
    assert controller.model.get_data_buffer.called is False

    # Change the buffer size
    controller.configuration["experiment"]["CameraParameters"]["img_x_pixels"] = 100
    controller.configuration["experiment"]["CameraParameters"]["img_y_pixels"] = 100
    controller.update_buffer()

    # Make sure that the get_data_buffer method is called.
    assert controller.model.get_data_buffer.called is True

    # Confirm that the buffer size has been updated.
    assert controller.img_width == 100
    assert controller.img_height == 100

    assert True


def test_change_microscope(controller):
    # Get the microscopes from the configuration file
    microscopes = controller.configuration["configuration"]["microscopes"]

    # Iterate through the microscopes and change the microscope
    for microscope_name in microscopes.keys():

        # Patch the configuration_controller
        controller.configuration_controller.change_microscope = MagicMock()

        # Default zoom is '0.63x'
        zoom = microscopes[microscope_name]["zoom"]["position"].keys()[0]
        controller.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom

        # Change the microscope without passing the zoom
        controller.change_microscope(microscope_name)
        assert (
            controller.configuration["experiment"]["MicroscopeState"]["microscope_name"]
            == microscope_name
        )

        # Confirm that the zoom has not changed.
        assert controller.configuration["experiment"]["MicroscopeState"]["zoom"] == zoom

        # Call it and pass the zoom
        zoom = microscopes[microscope_name]["zoom"]["position"].keys()[-1]
        controller.change_microscope(microscope_name, zoom)
        assert controller.configuration["experiment"]["MicroscopeState"]["zoom"] == zoom

        # Make sure that the configuration_controller has been called.
        assert controller.configuration_controller.change_microscope.called is True

        # Have configuration controller return False
        controller.configuration_controller.change_microscope.return_value = False

        # Patch the stage controller, channels_tab_controller...
        controller.stage_controller.initialize = MagicMock()
        controller.channels_tab_controller.initialize = MagicMock()
        camera_setting_controller = controller.camera_setting_controller
        camera_setting_controller.update_camera_device_related_setting = MagicMock()
        camera_setting_controller.calculate_physical_dimensions = MagicMock()
        controller.camera_view_controller.update_snr = MagicMock()

        # Call change microscope, assert patched methods are not called
        controller.change_microscope(microscope_name)
        assert controller.stage_controller.initialize.called is False
        assert controller.channels_tab_controller.initialize.called is False
        assert (
            camera_setting_controller.update_camera_device_related_setting.called
            is False
        )
        assert camera_setting_controller.calculate_physical_dimensions.called is False
        assert controller.camera_view_controller.update_snr.called is False

        # Have configuration controller return True
        controller.configuration_controller.change_microscope.return_value = True

        # Call change microscope, assert patched methods are called
        controller.change_microscope(microscope_name)
        assert controller.stage_controller.initialize.called is True
        assert controller.channels_tab_controller.initialize.called is True
        assert (
            camera_setting_controller.update_camera_device_related_setting.called
            is True
        )
        assert camera_setting_controller.calculate_physical_dimensions.called is True
        assert controller.camera_view_controller.update_snr.called is True

        # Test waveform popup controller.
        controller.waveform_popup_controller = MagicMock()
        controller.change_microscope(microscope_name)
        assert (
            controller.waveform_popup_controller.populate_experiment_values.called
            is True
        )

        assert True


def test_initialize_cam_view(controller):
    minmax_values = [0, 2**16 - 1]
    image_metrics = [1, 0, 0]
    controller.initialize_cam_view()

    assert (
        controller.camera_view_controller.image_palette["Min"].get() == minmax_values[0]
    )
    assert (
        controller.camera_view_controller.image_palette["Max"].get() == minmax_values[1]
    )
    assert (
        controller.camera_view_controller.image_metrics["Frames"].get()
        == image_metrics[0]
    )

    assert True


def test_populate_experiment_setting(controller):
    controller.populate_experiment_setting(in_initialize=False)
    assert True


def test_prepare_acquire_data(controller):

    # Test without warning message
    controller.set_mode_of_sub = MagicMock()
    assert controller.prepare_acquire_data() is True
    assert controller.set_mode_of_sub.called is True

    # Test with warning message. Challenging since controller is local.
    # with patch('controller.tkinter.messagebox.showerror') as mock_showerror:
    #     controller.update_experiment_setting.return_value = "Warning!"
    #     assert controller.prepare_acquire_data() is False
    #     mock_showerror.assert_called_once()

    assert True


def test_set_mode_of_sub(controller):
    # Patch the sub controllers
    controller.channels_tab_controller.set_mode = MagicMock()
    controller.camera_view_controller.set_mode = MagicMock()
    controller.camera_setting_controller.set_mode = MagicMock()
    controller.waveform_tab_controller.set_mode = MagicMock()
    controller.acquire_bar_controller.stop_acquire = MagicMock()

    # Test with mode = "live"
    mode = "live"
    controller.set_mode_of_sub(mode)
    assert controller.channels_tab_controller.set_mode.called is True
    assert controller.camera_setting_controller.set_mode.called is True
    assert controller.waveform_tab_controller.set_mode.called is True
    assert controller.acquire_bar_controller.stop_acquire.called is False

    # Test with mode = "stop"
    mode = "stop"
    controller.acquire_bar_controller.stop_acquire.reset_mock()
    controller.set_mode_of_sub(mode)
    assert controller.acquire_bar_controller.stop_acquire.called is True

    assert True


def test_execute_joystick_toggle(controller):
    # joystick_toggle
    controller.threads_pool.createThread = MagicMock()
    controller.stage_controller.joystick_is_on = False
    controller.execute("joystick_toggle")
    assert controller.threads_pool.createThread.called is False

    controller.stage_controller.joystick_is_on = True
    controller.execute("joystick_toggle")
    assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_stop_stage(controller):
    controller.threads_pool.createThread = MagicMock()
    controller.execute(command="stop_stage")
    assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_move_stage_and_update_info(controller):
    positions = {"x": 51, "y": 52.0, "z": -530.3, "theta": 1, "f": 0}

    controller.execute("move_stage_and_update_info", positions)
    for axis, value in positions.items():
        assert (
            float(controller.stage_controller.widget_vals[axis].get())
            == positions[axis]
        )

    assert True


@pytest.mark.parametrize(
    "acquisition_mode, sensor_mode, readout_direction, template_name, "
    "expected_template_name",
    [
        ("live", "Normal", "", "Bidirectional", "Default"),
        ("z-stack", "Normal", "", "Bidirectional", "Default"),
        ("customized", "Normal", "", "Bidirectional", "Bidirectional"),
        ("live", "Light-Sheet", "Top-To-Bottom", "Bidirectional", "Default"),
        ("live", "Light-Sheet", "Bidirectional", "Bidirectional", "Bidirectional"),
        (
            "customized",
            "Light-Sheet",
            "Bidirectional",
            "Bidirectional",
            "Bidirectional",
        ),
        ("z-stack", "Light-Sheet", "Bidirectional", "Default", "Bidirectional"),
        ("z-stack", "Light-Sheet", "Top-To-Bottom", "Default", "Default"),
    ],
)
def test_waveform_template(
    controller,
    acquisition_mode,
    sensor_mode,
    readout_direction,
    template_name,
    expected_template_name,
):
    controller.configuration["experiment"]["MicroscopeState"][
        "waveform_template"
    ] = template_name
    controller.configuration["experiment"]["MicroscopeState"][
        "image_mode"
    ] = acquisition_mode
    controller.configuration["experiment"]["CameraParameters"]["number_of_pixels"] = 10
    controller.populate_experiment_setting(in_initialize=True)

    controller.camera_setting_controller.mode_widgets["Readout"].set(readout_direction)
    controller.camera_setting_controller.mode_widgets["Sensor"].set(sensor_mode)
    controller.update_experiment_setting()

    assert (
        controller.configuration["experiment"]["MicroscopeState"]["waveform_template"]
        == expected_template_name
    )

    assert True
