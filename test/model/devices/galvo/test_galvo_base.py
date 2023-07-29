import unittest
from unittest.mock import MagicMock
from aslm.model.devices.galvo.galvo_base import GalvoBase
from aslm.config import load_configs, get_configuration_paths
from multiprocessing import Manager
import numpy as np


class TestGalvoBase(unittest.TestCase):
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

        self.microscope_name = "Mesoscale"
        self.device_connection = MagicMock()
        galvo_id = 0

        self.galvo = GalvoBase(
            microscope_name=self.microscope_name,
            device_connection=self.device_connection,
            configuration=self.configuration,
            galvo_id=galvo_id,
        )

        self.exposure_times = {"channel_1": 0.11, "channel_2": 0.2, "channel_3": 0.3}
        self.sweep_times = {"channel_1": 0.115, "channel_2": 0.2, "channel_3": 0.3}

    def tearDown(self):
        """Tear down the multiprocessing manager."""
        self.manager.shutdown()

    def test_galvo_base_initialization(self):
        # Parent Class Super Init
        assert self.galvo.microscope_name == "Mesoscale"
        assert self.galvo.galvo_name == "Galvo 0"
        assert self.galvo.sample_rate == 100000
        assert self.galvo.sweep_time == 0.2
        assert self.galvo.camera_delay_percent == 10
        assert self.galvo.galvo_max_voltage == 5
        assert self.galvo.galvo_min_voltage == -5
        assert self.galvo.remote_focus_ramp_falling == 2.5
        assert self.galvo.galvo_waveform == "sawtooth"
        assert self.galvo.waveform_dict == {}

    def test_adjust_with_valid_input(self):
        # Test the method with valid input data
        for waveform in ["sawtooth", "sine"]:
            self.galvo.galvo_waveform = waveform
            result = self.galvo.adjust(self.exposure_times, self.sweep_times)

            # Assert that the result is a dictionary
            self.assertIsInstance(result, dict)

            # Assert that the keys in the result dictionary are the same as in the input
            # dictionaries
            self.assertSetEqual(set(result.keys()), set(self.exposure_times.keys()))

            # Assert that the values in the result dictionary are not None
            for value in result.values():
                self.assertIsNotNone(value)

    def test_adjust_with_invalid_input(self):
        # Test the method with invalid input data
        invalid_exposure_times = {"channel_1": 0.1}  # Missing channel 2 and 3 keys
        invalid_sweep_times = {"channel_1": 0.1}  # Missing channel 2 and 3 keys

        # Test if the method raises an exception or returns None with invalid input
        with self.assertRaises(KeyError):
            _ = self.galvo.adjust(invalid_exposure_times, invalid_sweep_times)

    def test_with_improper_waveform(self):
        self.galvo.galvo_waveform = "banana"
        result = self.galvo.adjust(self.exposure_times, self.sweep_times)
        assert result == self.galvo.waveform_dict

    def test_waveform_clipping(self):
        self.galvo.galvo_waveform = "sawtooth"
        result = self.galvo.adjust(self.exposure_times, self.sweep_times)
        for channel in "channel_1", "channel_2", "channel_3":
            assert np.all(result[channel] <= self.galvo.galvo_max_voltage)
            assert np.all(result[channel] >= self.galvo.galvo_min_voltage)
