from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture(scope="session")
def controller_root():
    import tkinter as tk

    root = tk.Tk()
    yield root
    root.destroy()


class DummySplashScreen:
    def destroy(self):
        pass


@pytest.fixture(scope="session")
def controller(controller_root):
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
    use_gpu = False
    args = SimpleNamespace(synthetic_hardware=True)

    controller = Controller(
        controller_root,
        DummySplashScreen(),
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        use_gpu,
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
