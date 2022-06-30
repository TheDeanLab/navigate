"""
ASLM joy-stick communication classes.

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

# Third Party Imports

# Local Imports
from aslm.model.devices.joystick.joystick_base import JoystickBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class JoystickLogitech(JoystickBase):

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.cfg = parent.cfg
        self.verbose = True

        ''' parent is the window '''
        # Select if Demo mode is enabled, or the Logitech Farm Simulator
        if self.cfg.sidepanel == 'FarmSimulator':
            self.joystick = FarmSimulatorSidePanel()
            # self.joystick.sig_button_pressed.connect(self.button_handler)
            # self.joystick.sig_mode_changed.connect(self.mode_handler)
            # self.joystick.sig_axis_moved.connect(self.axis_handler)
        elif self.cfg.sidepanel == 'Demo':
            self.joystick = Demo_SidePanel()

        ''' '''
        self.SliderChangeCount = 0

    def button_handler(self, button_id):
        if self.verbose:
            print('Button pressed: ', button_id)
        logger.debug(f"Button pressed, {button_id}")

        ''' Laser switching buttons '''
        if button_id == 1:
            self.set_combobox_to_index(self.parent.LaserComboBox, 0)
        if button_id == 2:
            self.set_combobox_to_index(self.parent.LaserComboBox, 1)
        if button_id == 3:
            self.set_combobox_to_index(self.parent.LaserComboBox, 2)
        if button_id == 6:
            self.set_combobox_to_index(self.parent.LaserComboBox, 3)
        if button_id == 7:
            self.set_combobox_to_index(self.parent.LaserComboBox, 4)
        if button_id == 8:
            self.set_combobox_to_index(self.parent.LaserComboBox, 5)

        ''' Load & unload samples '''
        if button_id == 5:
            self.parent.sig_unload_sample.emit()
        if button_id == 10:
            self.parent.sig_load_sample.emit()

        ''' Filter & Zoom Increments & decrements '''
        if button_id == 11:
            self.increment_combobox(self.parent.FilterComboBox)
        if button_id == 12:
            self.decrement_combobox(self.parent.FilterComboBox)
        if button_id == 13:
            self.increment_combobox(self.parent.ZoomComboBox)
        if button_id == 14:
            self.decrement_combobox(self.parent.ZoomComboBox)

        ''' Shutter buttons '''
        if button_id == 17:
            self.set_combobox_to_string(self.parent.ShutterComboBox, 'Both')

        if button_id == 18:
            self.set_combobox_to_string(self.parent.ShutterComboBox, 'Both')

        if button_id == 19:
            self.set_combobox_to_string(self.parent.ShutterComboBox, 'Left')

        if button_id == 20:
            self.set_combobox_to_string(self.parent.ShutterComboBox, 'Right')

        ''' Live button '''
        if button_id == 21:
            current_state = self.parent.get_state_parameter('state')
            if self.verbose:
                print('Current state: ', current_state)
            logger.debug("Current state")
            if current_state == ('live'):
                pass
                # self.parent.StopButton.clicked.emit(True)
            elif current_state == 'idle':
                pass
                # self.parent.LiveButton.clicked.emit(True)

        ''' Increase & decrease laser intensity '''
        if button_id == 26:
            self.increase_slider(self.parent.LaserIntensitySlider, 2)

        if button_id == 27:
            self.decrease_slider(self.parent.LaserIntensitySlider, 2)

        ''' Stop movement button '''
        if button_id == 28:
            # self.parent.sig_stop_movement.emit()

        if button_id == 29:
            pass

    def set_combobox_to_index(self, combobox, index):
        if index < combobox.count():
            combobox.setCurrentIndex(index)

    def set_combobox_to_string(self, combobox, string):
        index = combobox.findText(string)
        if self.verbose:
            print('Index: ', index)
        logger.debug(f"Index, {index}")
        if index != -1:
            combobox.setCurrentIndex(index)

    def increment_combobox(self, combobox):
        index = combobox.currentIndex()
        index += 1
        if index < combobox.count():
            combobox.setCurrentIndex(index)

    def decrement_combobox(self, combobox):
        index = combobox.currentIndex()
        index -= 1
        if index > -1:
            combobox.setCurrentIndex(index)

    def increase_slider(self, slider, event_devider=2):
        self.SliderChangeCount += 1
        ''' To avoid events coming too quickly,
        only every n-th event is causing a change if
        n = event_devider
        '''
        if self.SliderChangeCount % event_devider == 0:
            value = slider.value()
            value = value + 1

            if value != 100:
                slider.setValue(value)
            else:
                slider.setValue(100)

    def decrease_slider(self, slider, event_devider=2):
        ''' To avoid events coming too quickly,
        only every n-th event is causing a change if
        n = event_devider
        '''
        self.SliderChangeCount += 1

        if self.SliderChangeCount % event_devider == 0:
            value = slider.value()
            value = value - 1

            if value != 0:
                slider.setValue(value)
            else:
                slider.setValue(0)

    def mode_handler(self, str):
        '''
        Helper method to handle mode changes of the joystick.
        The FarmSimulatorSidePanel has 6 movement axes, 0 to 2 in "blue"
        LED mode (grey button on the joystick) and 3 to 5 in "red" mode.
        When starting up, the mode is unknown and has to be found out by
        registering which axes produce joystick events.
        '''

        if self.verbose:
            print('New joystick mode: ', str)
        logger.debug("New joystick mode")

        if str == '012':
            self.parent.display_status_message('Joystick Mode: XY Mode')
        elif str == '345':
            self.parent.display_status_message('Joystick Mode: ZF Mode')
        else:
            self.parent.display_status_message('Joystick Mode: Undefined')

    def axis_handler(self, axis_id, value):
        ''' The axis handler deals with joystick movements.
        The FarmSimulatorSidePanel has 6 movement axes, 0 to 2 in "blue"
        LED mode (grey button on the joystick) and 3 to 5 in "red" mode.
        When starting up, the mode is unknown and has to be found out by
        registering which axes produce joystick events.
        '''

        if self.verbose:
            print('Axis: ', axis_id, ',Value: ', value)
        logger.debug(f"Axis: {axis_id}, Value: {value}")

        value = value - 128

        if axis_id == 0:
            pass
            # self.parent.sig_move_relative.emit({'x_rel':value/5})
        elif axis_id == 1:
            pass
            # self.parent.sig_move_relative.emit({'y_rel':value/5})
        elif axis_id == 3:
            ''' Some FarmSimulatorSidePanel have a bug which lets them
            send axis 2 and axis 3 (both rotation motions) at the same time.
            The following is intended to prevent this to affect the microscope:
            '''
            if self.joystick.mode == '123':
                pass
            else:
                pass
                # self.parent.sig_move_relative.emit({'f_rel':value/30})
        elif axis_id == 4:
            pass
            # self.parent.sig_move_relative.emit({'f_rel': value/5})
        elif axis_id == 5:
            pass
            # self.parent.sig_move_relative.emit({'z_rel': value/5})
