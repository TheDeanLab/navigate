# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

MMCORE_PLUGIN_INSTALL_SPEC = (
    "git+https://github.com/TheDeanLab/navigate-mmcore-plugin.git"
)
MMCORE_PLUGIN_PACKAGE = "navigate_mmcore_plugin"
MMCORE_PLUGIN_DISPLAY_NAME = "MMCore Plugin"


def _run_command(command):
    """Run a command and show full output on failure."""
    completed_process = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed_process.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            f"  {' '.join(command)}\n\n"
            f"stdout:\n{completed_process.stdout}\n\n"
            f"stderr:\n{completed_process.stderr}"
        )


def _ensure_importable(module_name):
    """Install a module with pip if it is not importable."""
    import_check = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if import_check.returncode == 0:
        return
    _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--upgrade",
            module_name,
        ]
    )


@pytest.fixture(scope="module")
def installed_mmcore_plugin():
    """Install mmcore plugin from GitHub for integration testing."""
    if os.environ.get("NAVIGATE_RUN_PLUGIN_INTEGRATION") != "1":
        pytest.skip(
            "Set NAVIGATE_RUN_PLUGIN_INTEGRATION=1 to run external plugin "
            "integration tests."
        )

    _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--no-deps",
            "--upgrade",
            MMCORE_PLUGIN_INSTALL_SPEC,
        ]
    )
    _ensure_importable("pymmcore")
    return MMCORE_PLUGIN_PACKAGE


def test_mmcore_plugin_package_is_discoverable(installed_mmcore_plugin):
    """MMCore plugin package should register the navigate entry point."""
    from navigate.controller.sub_controllers.plugins import PluginPackageManager

    plugins = PluginPackageManager.get_plugins()
    assert installed_mmcore_plugin in plugins

    plugin_config = PluginPackageManager.load_config(installed_mmcore_plugin)
    assert plugin_config["name"] == MMCORE_PLUGIN_DISPLAY_NAME
    assert plugin_config["view"] == "Popup"

    plugin_view = PluginPackageManager.load_view(
        installed_mmcore_plugin, plugin_config["name"]
    )
    plugin_controller = PluginPackageManager.load_controller(
        installed_mmcore_plugin, plugin_config["name"]
    )
    assert plugin_view is not None
    assert plugin_controller is not None


def test_mmcore_plugin_loads_in_plugins_controller(installed_mmcore_plugin, tmp_path):
    """navigate controller-side plugin bootstrap should include MMCore plugin."""
    from navigate.controller.sub_controllers.plugins import PluginsController

    navigate_home = tmp_path / "navigate_home"
    (navigate_home / "config").mkdir(parents=True)

    parent_controller = MagicMock()
    parent_controller.view = MagicMock()
    parent_controller.view.menubar = MagicMock()
    parent_controller.view.menubar.menu_plugins = MagicMock()
    parent_controller.add_acquisition_mode = MagicMock()

    plugins_controller = PluginsController(
        view=parent_controller.view, parent_controller=parent_controller
    )
    with patch(
        "navigate.controller.sub_controllers.plugins.get_navigate_path",
        return_value=str(navigate_home),
    ):
        plugins_controller.load_plugins()

    loaded_labels = [
        call.kwargs.get("label")
        for call in parent_controller.view.menubar.menu_plugins.add_command.call_args_list
    ]
    assert installed_mmcore_plugin in loaded_labels


def test_mmcore_plugin_loads_in_plugins_model(installed_mmcore_plugin, tmp_path):
    """navigate model-side plugin bootstrap should register MMCore device hooks."""
    from navigate.model.plugins_model import PluginsModel

    navigate_home = tmp_path / "navigate_home"
    (navigate_home / "config").mkdir(parents=True)

    with patch(
        "navigate.model.plugins_model.get_navigate_path",
        return_value=str(navigate_home),
    ):
        model = PluginsModel()
        devices_dict, plugin_acquisition_modes = model.load_plugins()

    assert (navigate_home / "feature_lists").exists()
    assert "multiple_devices" in devices_dict, (
        "MMCore plugin devices were not registered. "
        f"Registered device keys: {list(devices_dict.keys())}. "
        "This commonly occurs when plugin runtime dependencies (for example, "
        "`pymmcore`) are unavailable."
    )
    assert devices_dict["multiple_devices"]["ref_list"] == ["type"]
    assert callable(devices_dict["multiple_devices"]["load_device"])
    assert callable(devices_dict["multiple_devices"]["start_device"])
    assert isinstance(plugin_acquisition_modes, dict)
