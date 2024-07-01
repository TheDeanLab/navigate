from multiprocessing import Manager

import random
import unittest
from unittest.mock import patch

from navigate.config import load_configs, get_configuration_paths
from navigate.model.devices.lasers.laser_ni import LaserNI


class TestLaserNI(unittest.TestCase):
    """Unit tests for the Laser NI Device."""

    def setUp(self) -> None:
        """Set up the configuration, experiment, etc."""

        self.manager = Manager()
        self.parent_dict = {}

        (
            configuration_path,
            experiment_path,
            waveform_constants_path,
            rest_api_path,
            waveform_templates_path,
        ) = get_configuration_paths()

        self.configuration = load_configs(
            self.manager,
            configuration=configuration_path,
            experiment=experiment_path,
            waveform_constants=waveform_constants_path,
            rest_api_config=rest_api_path,
            waveform_templates=waveform_templates_path,
        )

        self.microscope_name = self.configuration["configuration"][
            "microscopes"
        ].keys()[0]
        self.device_connection = None
        laser_id = 0

        with patch("nidaqmx.Task") as self.mock_task:
            # self.mock_task_instance = MagicMock()
            # self.mock_task.return_value = self.mock_task_instance
            self.laser = LaserNI(
                microscope_name=self.microscope_name,
                device_connection=self.device_connection,
                configuration=self.configuration,
                laser_id=laser_id,
            )

    def tearDown(self):
        """Tear down the multiprocessing manager."""
        self.manager.shutdown()

    def test_set_power(self):
        self.current_intensity = random.randint(1, 100)
        scaled_intensity = (int(self.current_intensity) / 100) * self.laser.laser_max_ao
        self.laser.set_power(self.current_intensity)

        self.laser.laser_ao_task.write.assert_called_once_with(
            scaled_intensity, auto_start=True
        )
        assert self.laser._current_intensity == self.current_intensity

    def test_turn_on(self):
        self.laser.on_off_type = "digital"
        self.laser.turn_on()
        self.laser.laser_do_task.write.assert_called_with(True, auto_start=True)

        self.laser.on_off_type = "analog"
        self.laser.turn_on()
        self.laser.laser_do_task.write.assert_called_with(
            self.laser.laser_max_do, auto_start=True
        )

    def test_turn_off(self):
        self.current_intensity = random.randint(1, 100)
        self.laser._current_intensity = self.current_intensity

        self.laser.on_off_type = "digital"
        self.laser.turn_off()
        self.laser.laser_do_task.write.assert_called_with(False, auto_start=True)

        assert self.laser._current_intensity == self.current_intensity

        self.laser.on_off_type = "analog"
        self.laser.turn_off()
        self.laser.laser_do_task.write.assert_called_with(
            self.laser.laser_min_do, auto_start=True
        )

        assert self.laser._current_intensity == self.current_intensity
