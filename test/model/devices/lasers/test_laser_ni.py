from multiprocessing import Manager

import random
import unittest
from unittest.mock import MagicMock, patch

from aslm.config import load_configs, get_configuration_paths


class TestLaserNI(unittest.TestCase):
    """Unit tests for the Laser NI Device."""

    def setUp(self) -> None:
        """Set up the configuration, experiment, etc."""
        from aslm.model.devices.lasers.laser_ni import LaserNI

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

        self.microscope_name = "Mesoscale"
        self.device_connection = MagicMock()
        laser_id = 0

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
        with patch("nidaqmx.Task") as mock_task:
            mock_task_instance = MagicMock()
            mock_task.return_value = mock_task_instance
            self.laser.set_power(self.current_intensity)

            mock_task.laser_ao_task.assert_called_once_with(
                data=scaled_intensity, auto_start=True
            )
            assert self.laser._current_intensity == self.current_intensity

    def test_turn_on(self):
        with patch("nidaqmx.Task") as mock_task:
            mock_task_instance = MagicMock()
            mock_task.return_value = mock_task_instance

            self.laser.on_off_type = "digital"
            self.laser.turn_on()
            mock_task.laser_do_task.assert_called_once_with(data=True, auto_start=True)

            self.laser.on_off_type = "analog"
            self.laser.turn_on()
            mock_task.laser_do_task.assert_called_once_with(
                data=self.laser.laser_max_do, auto_start=True
            )
