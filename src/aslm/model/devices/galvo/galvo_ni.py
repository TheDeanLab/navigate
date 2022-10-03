"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

#  Standard Library Imports
import logging

# Third Party Imports
import nidaqmx
from nidaqmx.constants import AcquisitionType

# Local Imports
from aslm.model.devices.galvo.galvo_base import GalvoBase

# # Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GalvoNI(GalvoBase):
    r"""GalvoNI Class

     """

    def __init__(self, microscope_name, device_connection, configuration, galvo_id=0):
        super().__init__(microscope_name, device_connection, configuration, galvo_id)

        self.task = None

        self.trigger_source = configuration['configuration']['microscopes'][microscope_name]['daq']['trigger_source']

        self.initialize_task()

    def initialize_task(self):
        # TODO: make sure the task is reusable, Or need to create and close each time.
        self.task = nidaqmx.Task()
        channel = self.device_config['hardware']['channel']
        self.task.ao_channels.add_ao_voltage_chan(channel)
        self.task.timing.cfg_samp_clk_timing(rate=self.sample_rate,
                                             sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=self.samples)
        self.task.triggers.start_trigger.cfg_dig_edge_start_trig(self.trigger_source)

    def __del__(self):
        self.stop_task()
        self.close_task()

    def adjust(self, readout_time):
        self.stop_task()
        self.close_task()

        waveform_dict = super().adjust(readout_time)

        self.initialize_task()

        return waveform_dict

    def prepare_task(self, channel_key):
        # write waveform
        self.task.write(self.waveform_dict[channel_key])

    def start_task(self):
        self.task.start()

    def stop_task(self, force=False):
        if not force:
            self.task.wait_until_done()
        self.task.stop()
    
    def close_task(self):
        self.task.close()
