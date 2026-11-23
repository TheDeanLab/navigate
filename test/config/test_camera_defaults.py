"""Startup and experiment reload preserve per-microscope camera preferences."""

import pytest

from navigate.config.config import verify_experiment_config
from navigate.config.preload import preload_configuration
from navigate.tools.common_functions import copy_proxy_object
from test.config.test_preload import loaded_configuration
from test.model.devices.camera.test_hamamatsu_outputs import selections


@pytest.mark.parametrize("loader", [preload_configuration, verify_experiment_config])
@pytest.mark.parametrize("explicit_experiment", [False, True])
def test_real_loaders_seed_camera_defaults_without_overriding_experiment(
    loaded_configuration, loader, explicit_experiment
):
    manager, configuration = loaded_configuration
    preload_configuration(manager, configuration)
    microscopes = configuration["configuration"]["microscopes"]
    parameters = configuration["experiment"]["CameraParameters"]
    names = list(microscopes.keys())
    for index, name in enumerate(names):
        defaults = {
            "output_triggers": selections(),
            "scan_speed": 2,
            "bit_depth": 12,
            "defect_correction": 1,
            "hot_pixel_correction": 2,
            "cooling": "On",
        }
        defaults["output_triggers"]["connectors"]["3"]["pulse_width_s"] = (
            0.003 + index * 0.001
        )
        microscopes[name]["camera"]["advanced_settings"] = defaults
        if explicit_experiment:
            parameters[name]["output_triggers"] = selections()
            parameters[name]["scan_speed"] = 1
    loader(manager, configuration)
    for index, name in enumerate(names):
        stored = copy_proxy_object(parameters[name])
        expected_width = 0.004 if explicit_experiment else 0.003 + index * 0.001
        assert (
            stored["output_triggers"]["connectors"]["3"]["pulse_width_s"]
            == expected_width
        )
        assert stored["scan_speed"] == (1 if explicit_experiment else 2)
        assert stored["bit_depth"] == 12
        assert stored["cooling"] == "On"
