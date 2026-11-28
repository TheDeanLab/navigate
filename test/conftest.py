"""Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
#"""

# Standard Library Imports
import logging
import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk

# Third Party Imports
import pytest

# Local Imports
from test.profile_isolation import ProfileWriteGuard

_PROFILE_GUARD = pytest.StashKey[ProfileWriteGuard]()


def pytest_configure(config: pytest.Config) -> None:
    """Isolate profile paths before collecting/importing any application tests."""
    protected = [Path.home() / ".navigate"]
    if os.environ.get("LOCALAPPDATA"):
        protected.append(Path(os.environ["LOCALAPPDATA"]) / ".navigate")
    previous_profile = os.environ.get("NAVIGATE_HOME")
    if previous_profile:
        protected.append(Path(previous_profile).expanduser())
    source_config = Path(__file__).resolve().parents[1] / "src/navigate/config"
    protected.extend(source_config.glob("*.y*ml"))

    # Do not reuse an externally supplied profile, even for hardware tests.
    # The environment override also reaches spawn/fork and exec subprocesses.
    sandbox = tempfile.TemporaryDirectory(prefix="navigate-pytest-")
    os.environ["NAVIGATE_HOME"] = str(Path(sandbox.name) / ".navigate")
    guard = ProfileWriteGuard(protected)
    config.stash[_PROFILE_GUARD] = guard
    audit_mode = os.environ.get("NAVIGATE_AUDIT_DIAGNOSTIC", "normal")
    if audit_mode == "traceable":
        guard.__cantrace__ = True
    if audit_mode != "skip":
        sys.addaudithook(guard)

    def cleanup() -> None:
        # Windows cannot remove profile logs while FileHandlers still own them.
        # Close them after pytest teardown and before deleting the sandbox.
        logging.shutdown()
        guard.enabled = False
        if previous_profile is None:
            os.environ.pop("NAVIGATE_HOME", None)
        else:
            os.environ["NAVIGATE_HOME"] = previous_profile
        sandbox.cleanup()

    config.add_cleanup(cleanup)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail even if application code swallowed a forbidden-write exception."""
    guard = session.config.stash[_PROFILE_GUARD]
    if guard.violations:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_sep("=", "Blocked writes to protected profiles")
            for message in sorted(set(guard.violations)):
                reporter.write_line(message)


@pytest.fixture(scope="package")
def dummy_model():
    """Dummy model for testing.

    Returns
    -------
    DummyModel
        Dummy model for testing.
    """
    from test.model.dummy import DummyModel

    model = DummyModel()
    return model


@pytest.fixture(scope="session")
def tk_root():
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture(scope="session")
def dummy_view(tk_root):
    """Dummy view for testing.

    Creates a dummy view for the controller tests.
     Will be deleted post test session

    Returns:
        tkinter.Tk: Dummy view
    """
    from navigate.view.main_application_window import MainApp

    view = MainApp(tk_root)
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
    from test.model.dummy import DummyController

    controller = DummyController(dummy_view)
    return controller


# @pytest.fixture(scope="package")
# def root():
#     import tkinter as tk

#     root = tk.Tk()
#     yield root
#     root.destroy()


# @pytest.fixture(scope="package")
# def splash_screen(root):
#     from navigate.view.splash_screen import SplashScreen

#     splash_screen = SplashScreen(root, "./icon/splash_screen_image.png")

#     return splash_screen


# @pytest.fixture(scope="package")
# def controller(root, splash_screen):
#     from types import SimpleNamespace
#     from pathlib import Path

#     from navigate.controller.controller import Controller

#     # Use configuration files that ship with the code base
#     configuration_directory = Path.joinpath(
#         Path(__file__).resolve().parent.parent, "src", "navigate", "config"
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


def pytest_collection_modifyitems(config, items):
    """Skip hardware-marked tests on GitHub Actions runners.

    Set ``NAVIGATE_RUN_HARDWARE_TESTS=1`` to opt in on self-hosted runners
    that actually have hardware attached.
    """
    if os.getenv("GITHUB_ACTIONS", "").lower() != "true":
        return
    if os.getenv("NAVIGATE_RUN_HARDWARE_TESTS", "0") == "1":
        return

    skip_hardware = pytest.mark.skip(
        reason="Hardware tests are disabled on GitHub Actions runners."
    )
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip_hardware)
