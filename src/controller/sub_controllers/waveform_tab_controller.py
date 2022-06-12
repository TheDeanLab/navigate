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
from controller.sub_controllers.gui_controller import GUI_Controller
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[0]
logger = logging.getLogger(p)


class Waveform_Tab_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)
        self.remote_focus_waveform = 0
        self.etl_r_waveform = 0
        self.galvo_l_waveform = 0
        self.galvo_r_waveform = 0
        self.laser_ao_waveforms = 0

        #TODO: Update waveforms according to the current model?
        #TODO: How do you detect changes to the model to rerun the code?
        #TODO: Concatenate each channel into a consecutive waveform as the microscope actually will.

    def update_waveforms(self):
        self.etl_l_waveform = self.parent_controller.model.daq.etl_l_waveform
        self.etl_r_waveform = self.parent_controller.model.daq.etl_r_waveform
        self.galvo_l_waveform = self.parent_controller.model.daq.galvo_l_waveform
        self.galvo_r_waveform = self.parent_controller.model.daq.galvo_r_waveform
        self.laser_ao_waveforms = self.parent_controller.model.daq.laser_ao_waveforms

    def plot_waveforms(self):
        self.parent_controller.model.daq.create_waveforms()
        self.update_waveforms()
        self.view.fig = Figure(figsize=(8, 4), dpi=100)

        self.view.plot1 = self.view.fig.add_subplot(511)
        self.view.plot1.plot(self.etl_l_waveform, label='ETL L')

        self.view.plot2 = self.view.fig.add_subplot(512)
        self.view.plot2.plot(self.galvo_l_waveform, label='GALVO L')

        self.view.plot3 = self.view.fig.add_subplot(513)
        self.view.plot3.plot(self.laser_ao_waveforms, label='LASER')

        self.view.plot4 = self.view.fig.add_subplot(514)
        self.view.plot4.plot(self.galvo_r_waveform, label='GALVO R')

        self.view.canvas = FigureCanvasTkAgg(self.view.fig, master=self.view)
        self.view.canvas.get_tk_widget().pack()

    def plot_waveforms2(self, waveform_dict):
        self.view.fig = Figure(figsize=(8, 2), dpi=100)
        self.view.plot_etl = self.view.fig.add_subplot(511)
        self.view.plot_galvo = self.view.fig.add_subplot(512)

        for k in waveform_dict.keys():
            self.view.plot_etl.plot(waveform_dict[k]['etl_waveform'], label=k)
            self.view.plot_galvo.plot(waveform_dict[k]['galvo_waveform'], label=k)
        self.view.canvas = FigureCanvasTkAgg(self.view.fig, master=self.view)
        self.view.canvas.get_tk_widget().pack()
