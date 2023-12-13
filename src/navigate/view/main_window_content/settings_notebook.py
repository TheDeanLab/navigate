# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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
#
# Standard Imports
import tkinter as tk
import logging

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.DockableNotebook import DockableNotebook

# Import Sub-Frames
from navigate.view.main_window_content.camera_tab import CameraSettingsTab
from navigate.view.main_window_content.channels_tab import ChannelsTab
from navigate.view.main_window_content.stage_tab import StageControlTab
from navigate.view.main_window_content.multiposition_tab import MultiPositionTab

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class SettingsNotebook(DockableNotebook):
    """Settings Notebook

    This class is the settings notebook. It contains the following tabs:
    - Channels
    - Camera Settings
    - Stage Control
    - Multiposition
    - Robot Control
    """

    def __init__(self, frame_left, root, *args, **kwargs):
        """Initialize the settings notebook

        Parameters
        ----------
        frame_left : tk.Frame
            Left frame of the main window
        root : tk.Tk
            Root window of the main window
        *args : list
            Arguments
        **kwargs : dict
            Keyword arguments
        """

        # Init notebook
        DockableNotebook.__init__(self, frame_left, root, *args, **kwargs)

        # Putting notebook 1 into left frame
        self.grid(row=0, column=0)

        #: ChannelsTab: Channels tab
        self.channels_tab = ChannelsTab(self)

        #: CameraSettingsTab: Camera settings tab
        self.camera_settings_tab = CameraSettingsTab(self)

        #: StageControlTab: Stage control tab
        self.stage_control_tab = StageControlTab(self)

        # MultipositionTab: Multiposition tab
        self.multiposition_tab = MultiPositionTab(self)

        #Creating Robot Control Tab
        self.robot_control_tab = RobotControlTab(self)
        # TODO: Create a robot tab. @UTD

        # Tab list
        tab_list = [
            self.channels_tab,
            self.camera_settings_tab,
            self.stage_control_tab,
            self.multiposition_tab,
            self.robot_control_tab,
            # @UTD
        ]
        self.set_tablist(tab_list)

        # Adding tabs to settings notebook
        self.add(self.channels_tab, text="Channels", sticky=tk.NSEW)
        self.add(self.camera_settings_tab, text="Camera Settings", sticky=tk.NSEW)
        self.add(self.stage_control_tab, text="Stage Control", sticky=tk.NSEW)
        self.add(self.multiposition_tab, text="Multiposition", sticky=tk.NSEW)
        self.add(self.robot_control_tab, text="Robot Control", sticky=tk.NSEW)
        # @UTD
