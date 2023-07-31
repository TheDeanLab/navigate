# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

import unittest
from unittest.mock import MagicMock, patch
from aslm.model.devices.galvo.galvo_ni import GalvoNI
from nidaqmx.constants import AcquisitionType
from aslm.config import load_configs, get_configuration_paths
from multiprocessing import Manager


class TestGalvoNI(unittest.TestCase):
    """Unit tests for the Galvo NI Device."""

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

        self.galvo = GalvoNI(
            microscope_name=self.microscope_name,
            device_connection=self.device_connection,
            configuration=self.configuration,
            galvo_id=galvo_id,
        )

    def tearDown(self):
        """Tear down the multiprocessing manager."""
        self.manager.shutdown()

    def test_galvo_ni_initialization(self):
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

        # GalvoNI Init
        assert self.galvo.task is None
        assert self.galvo.trigger_source == "/PXI6259/PFI0"
        assert hasattr(self.galvo, "daq")

    def test_initialize_nidaqmx_task(self):
        # Mock the nidaqmx module and its required classes and methods
        self.galvo.device_config["hardware"]["channel"] = "PXI6259/ao0"

        with patch("nidaqmx.Task") as mock_task:
            mock_task_instance = MagicMock()
            mock_task.return_value = mock_task_instance

            mock_ao_channels = MagicMock()
            mock_task_instance.ao_channels = mock_ao_channels

            # Call the initialize_task method
            self.galvo.initialize_task()

            # Assertions to check if the correct methods were called with the
            # expected arguments
            self.assertTrue(mock_task.called)
            mock_ao_channels.add_ao_voltage_chan.assert_called_once_with(
                self.galvo.device_config["hardware"]["channel"]
            )
            mock_task_instance.timing.cfg_samp_clk_timing.assert_called_once_with(
                rate=self.galvo.sample_rate,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=self.galvo.samples,
            )
            mock_task_instance.triggers.start_trigger.cfg_dig_edge_start_trig.assert_called_once_with(
                self.galvo.trigger_source
            )

    def test_stop_task(self):
        # This function does nothing.
        self.galvo.stop_task(force=True)
        self.device_connection.assert_not_called()

        self.galvo.stop_task(force=False)
        self.device_connection.assert_not_called()

    def test_close_task(self):
        # More nothingness.
        self.galvo.close_task()
        self.device_connection.assert_not_called()

    def test_start_task(self):
        self.galvo.start_task()
        self.device_connection.assert_not_called()

    def test_prepare_task(self):
        self.galvo.prepare_task(channel_key="infinity")
        self.device_connection.assert_not_called()

    def test_adjust(self):
        sweep_times = {"channel_1": 0.3, "channel_2": 0.4, "channel_3": 0.5}

        exposure_times = {"channel_1": 0.25, "channel_2": 0.35, "channel_3": 0.45}

        waveforms = self.galvo.adjust(
            exposure_times=exposure_times, sweep_times=sweep_times
        )

        assert type(waveforms) == dict
        self.device_connection.assert_not_called()
