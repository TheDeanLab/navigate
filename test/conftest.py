"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
# """

# Standard Library Imports
import tkinter as tk
from pathlib import Path
from multiprocessing import Manager

# Third Party Imports
import pytest

# Local Imports
from test.controller.test_controller import controller  # noqa
from aslm.config.config import load_configs


@pytest.fixture(scope="package")
def dummy_model():
    """Dummy model for testing.

    Returns
    -------
    DummyModel
        Dummy model for testing.
    """
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    return model


@pytest.fixture(scope="session")
def tk_root():
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture(scope="session")
def dummy_view(tk_root):  # noqa
    """Dummy view for testing.

    Creates a dummy view for the controller tests.
     Will be deleted post test session

    Returns:
        tkinter.Tk: Dummy view
    """
    from aslm.view.main_application_window import MainApp

    base_directory = Path(__file__).resolve().parent
    configuration_directory = Path.joinpath(base_directory, "aslm", "src", "config")
    print(configuration_directory)

    config = Path.joinpath(configuration_directory, "configuration.yaml")
    experiment = Path.joinpath(configuration_directory, "experiment.yml")
    waveform_constants = Path.joinpath(
        configuration_directory, "waveform_constants.yml"
    )

    #: Manager: The manager.
    manager = Manager()
    #: dict: The configuration dictionary.
    configuration = load_configs(
        manager,
        configuration=config,
        experiment=experiment,
        waveform_constants=waveform_constants,
    )

    view = MainApp(root=tk_root, configuration=configuration)
    tk_root.update()
    yield view


@pytest.fixture(scope="package")
def dummy_controller(dummy_view):
    """Dummy controller for testing.

    Fixture that will mock controller functions called by sub controllers

    Returns
    -------
    DummyController
        Dummy controller for testing.
    """
    from aslm.model.dummy import DummyController

    return DummyController(dummy_view)


# @pytest.fixture(scope="package")
# def root():
#     import tkinter as tk

#     root = tk.Tk()
#     yield root
#     root.destroy()


# @pytest.fixture(scope="package")
# def splash_screen(root):
#     from aslm.view.splash_screen import SplashScreen

#     splash_screen = SplashScreen(root, "./icon/splash_screen_image.png")

#     return splash_screen


# @pytest.fixture(scope="package")
# def controller(root, splash_screen):
#     from types import SimpleNamespace
#     from pathlib import Path

#     from aslm.controller.controller import Controller

#     # Use configuration files that ship with the code base
#     configuration_directory = Path.joinpath(
#         Path(__file__).resolve().parent.parent, "src", "aslm", "config"
#     )
#     configuration_path = Path.joinpath(configuration_directory, "configuration.yaml")
#     experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
#     waveform_constants_path = Path.joinpath(configuration_directory,
#                                       "waveform_constants.yml")
#     rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")

#     controller = Controller(
#         root,
#         splash_screen,
#         configuration_path,
#         experiment_path,
#         waveform_constants_path,
#         rest_api_path,
#         False,
#         SimpleNamespace(synthetic_hardware=True),
#     )

#     yield controller
#     controller.execute("exit")

# @pytest.fixture(scope="package")
# def model(controller):
#     return controller.model


class IgnoreObj:
    def __init__(self):
        pass

    def __getattr__(self, __name: str):
        return self

    def __call__(self, *args, **kwargs):
        pass

    def __setattr__(self, __name: str, __value):
        pass

    def __getitem__(self, __key: str):
        return self

    def __setitem__(self, __key: str, __value):
        pass


@pytest.fixture(scope="package")
def ignore_obj():
    return IgnoreObj()
