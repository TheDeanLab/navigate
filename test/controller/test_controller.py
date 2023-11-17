from pathlib import Path
from types import SimpleNamespace

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
    from aslm.controller.controller import Controller

    base_directory = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "src", "aslm"
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


def test_change_microscope(controller):
    microscopes = controller.configuration["configuration"]["microscopes"]
    for microscope_name in microscopes.keys():
        zoom = microscopes[microscope_name]["zoom"]["position"].keys()[0]
        controller.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
        controller.change_microscope(microscope_name)
        assert (
            controller.configuration["experiment"]["MicroscopeState"]["microscope_name"]
            == microscope_name
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
