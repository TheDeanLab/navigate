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
<<<<<<<< HEAD:src/aslm/view/main_window_content/channel_settings/channel_settings_frames/stack_cycling_settings.py
import tkinter as tk
from tkinter import ttk
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class stack_cycling_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, *args, **kwargs):
        #Init Frame
        text_label = 'Laser Cycling Settings'
        ttk.Labelframe.__init__(stack_acq, settings_tab, text=text_label, *args, **kwargs)
        
        # Formatting
        tk.Grid.columnconfigure(stack_acq, 'all', weight=1)
        tk.Grid.rowconfigure(stack_acq, 'all', weight=1)

        #Laser Cycling Frame (Vertically oriented)
        stack_acq.cycling_frame = ttk.Frame(stack_acq)
        stack_acq.cycling_options = tk.StringVar()
        stack_acq.cycling_pull_down = ttk.Combobox(stack_acq, textvariable=stack_acq.cycling_options)
        stack_acq.cycling_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        stack_acq.cycling_pull_down.grid(row=0, column=1, sticky=(tk.NSEW), padx=4, pady=(4,6))

        #Gridding Each Holder Frame
        stack_acq.cycling_frame.grid(row=0, column=0, sticky=(tk.NSEW))
========

# Standard Library Imports
import unittest
from pathlib import Path

# Third Party Imports

# Local Imports
from aslm.model.devices.shutter.laser_shutter_base import ShutterBase
from aslm.model.aslm_model_config import Session as session

>>>>>>>> develop:test/model/devices/shutter/test_laser_shutter_base.py

class TestLaserBase(unittest.TestCase):
    r"""Unit Test for ShutterBase Class"""

    def test_shutter_base_attributes(self):
        base_directory = Path(__file__).resolve().parent.parent.parent.parent.parent
        configuration_directory = Path.joinpath(base_directory, 'src', 'aslm', 'config')
        configuration_path = Path.joinpath(configuration_directory, 'configuration.yml')
        experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')

        configuration = session(file_path=configuration_path,
                                verbose=False)
        experiment = session(file_path=experiment_path,
                             verbose=False)

        shutter = ShutterBase(configuration,
                              experiment,
                              False)

        assert hasattr(shutter, 'configuration')
        assert hasattr(shutter, 'experiment')
        assert hasattr(shutter, 'verbose')
        assert hasattr(shutter, 'shutter_right')
        assert hasattr(shutter, 'shutter_right_state')
        assert hasattr(shutter, 'shutter_left')
        assert hasattr(shutter, 'shutter_left_state')


if __name__ == '__main__':
    unittest.main()