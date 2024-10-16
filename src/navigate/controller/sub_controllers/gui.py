# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import logging
from typing import Any

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GUIController:
    """Base class for GUI controllers"""

    def __init__(self, view: Any, parent_controller=None) -> None:
        """Initializes GUI controller

        Parameters
        ----------
        view : Any
            GUI view
        parent_controller : Controller
            parent controller
        """
        #: tkinter.Tk: GUI view
        self.view = view

        #: Controller: parent controller
        self.parent_controller = parent_controller

        # register events
        for event_label, event_handler in self.custom_events.items():
            self.register_event_listener(event_label, event_handler)
        if hasattr(self, "event_listeners"):
            for event_label, event_label in self.event_listeners.items():
                self.register_event_listener(event_label, event_handler)

    def initialize(self):
        """This function is called when the controller is initialized

        This function initializes GUI based on configuration setting parameter:
        configuration_controller set range value for entry or spinbox widgets;
        add values to combobox get other necessary information for configuration.yml
        """
        pass

    def set_experiment_values(self):
        """Sets values of widgets based on experiment setting

        setting_dict is a dictionary
        """
        pass

    def update_experiment_values(self):
        """Collects all the values of widgets

        setting_dict is a reference of experiment dictionary
        update the dictionary directly
        """
        pass

    def execute(self, command, *args):
        """This function is called when a command is passed from a child process.

        Parameters
        ----------
        command : str
            command name
        args : tuple
            command arguments
        """

        self.show_verbose_info("command passed from child:", command)
        pass

    def show_verbose_info(self, *info):
        """Prints verbose information to the console

        Parameters
        ----------
        info : tuple
            information to be printed
        """
        logger.info(f"{self.__class__.__name__} : {info}")

    def register_event_listener(self, event_name, event_handler):
        """Register event listener in the parent_controller

        Parameters
        ----------
        event_name : str
            event name
        event_handler : function
            event handler
        """
        if not hasattr(self.parent_controller, "event_listeners"):
            self.parent_controller.event_listeners = {}
        self.parent_controller.event_listeners[event_name] = event_handler

    @property
    def custom_events(self):
        """Custom events for the controller"""
        return {}
