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


def test_populate_experiment_setting(controller):
    controller.populate_experiment_setting(in_initialize=False)
    assert True


def test_prepare_acquire_data(controller):
    controller.prepare_acquire_data()
    assert True


def test_execute(controller):
    controller.execute("acquire", "single")
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
