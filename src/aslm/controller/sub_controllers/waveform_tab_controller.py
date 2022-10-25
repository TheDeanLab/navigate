"""
ASLM sub-controller for the waveform display.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import logging
from random import sample

# Third Party Imports
import numpy as np
from tkinter import NSEW

# Local Imports
from aslm.controller.sub_controllers.gui_controller import GUIController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class WaveformTabController(GUIController):
    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)
        self.remote_focus_waveform = 0
        self.etl_r_waveform = 0
        self.galvo_l_waveform = 0
        self.galvo_r_waveform = 0
        self.laser_ao_waveforms = 0
        
        self.initialize_plots()

        microscope_name = self.parent_controller.configuration['experiment']['MicroscopeState']['microscope_name']
        self.view.waveform_settings.inputs['sample_rate'].set(self.parent_controller.configuration['configuration']['microscopes'][microscope_name]['daq']['sample_rate'])
        self.view.waveform_settings.inputs['sample_rate'].get_variable().trace_add('write', self.update_sample_rate)

        self.view.bind('<Enter>', self.plot_waveforms)  # TODO: This means we have to move our mouse off and then back
                                                        #       on to the plot to see an update. Better event to bind?

    def update_sample_rate(self, *args):
        sample_rate = self.view.waveform_settings.inputs['sample_rate'].get()
        if sample_rate == '':
            return
        microscope_name = self.parent_controller.configuration['experiment']['MicroscopeState']['microscope_name']
        self.parent_controller.configuration['configuration']['microscopes'][microscope_name]['daq']['sample_rate'] = int(sample_rate)
        self.sample_rate = int(sample_rate)

    def update_waveforms(self, waveform_dict, sample_rate):
        self.waveform_dict = waveform_dict
        self.sample_rate = sample_rate

    def initialize_plots(self):
        self.view.plot_etl = self.view.fig.add_subplot(211)
        self.view.plot_galvo = self.view.fig.add_subplot(212)

        self.view.canvas.get_tk_widget().grid(row=5, column=0, columnspan=3, sticky=(NSEW), padx=(5,5), pady=(5,5))

    def plot_waveforms(self, event):

        self.view.plot_etl.clear()
        self.view.plot_galvo.clear()

        last_etl = 0
        last_galvo = 0
        last_camera = 0
        for k in self.waveform_dict['camera_waveform'].keys():
            if self.waveform_dict['etl_waveform'][k] is None:
                continue
            etl_waveform = self.waveform_dict['etl_waveform'][k]
            # TODO: multiple galvos
            galvo_waveform = self.waveform_dict['galvo_waveform'][0][k]
            camera_waveform = self.waveform_dict['camera_waveform'][k]
            self.view.plot_etl.plot(np.arange(len(etl_waveform))/self.sample_rate + last_etl, etl_waveform, label=k)
            self.view.plot_galvo.plot(np.arange(len(galvo_waveform))/self.sample_rate + last_galvo, galvo_waveform, label=k)
            self.view.plot_etl.plot(np.arange(len(camera_waveform))/self.sample_rate + last_camera, camera_waveform, c='k', linestyle='--')
            self.view.plot_galvo.plot(np.arange(len(camera_waveform)) / self.sample_rate + last_camera, camera_waveform, c='k', linestyle='--')
            last_etl += len(etl_waveform)/self.sample_rate
            last_galvo += len(galvo_waveform)/self.sample_rate
            last_camera += len(camera_waveform)/self.sample_rate

        self.view.plot_etl.set_title('ETL Waveform')
        self.view.plot_galvo.set_title('Galvo Waveform')

        self.view.plot_etl.set_xlabel('Duration (s)')
        self.view.plot_galvo.set_xlabel('Duration (s)')

        self.view.plot_etl.set_ylabel('Amplitude')
        self.view.plot_galvo.set_ylabel('Amplitude')

        self.view.plot_etl.legend()

        self.view.fig.tight_layout()

        self.view.canvas.draw_idle()
