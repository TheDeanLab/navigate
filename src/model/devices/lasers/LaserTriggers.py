"""
Module for enabling single laser lines via NI-DAQmx
Author: Fabian Voigt

#TODO: Make sure that the analog modulation of laser intensity is active.
#TODO: Why isn't this in the daq.waveform module?
"""

import nidaqmx
from nidaqmx.constants import LineGrouping


class LaserTriggers():
    ''' Class for interacting with the laser enable DO lines via NI-DAQmx
    Works only with NI-PXI 6733s with all lasers on 6 output lines.

    This uses the property of NI-DAQmx-outputs to keep their last digital state or
    analog voltage for as long the device is not powered down. This means that
    the NI tasks are closed after calls to "enable", "disable", etc which in turn
    means that this class is not intended for fast switching in complicated waveforms.

    Needs a dictionary which combines laser wavelengths and device outputs
    in the form:
    {'488 nm': 'PXI6259/line0/port0', '515 nm': 'PXI6259/line0/port1'}
    '''

    def __init__(self, laser_dict):
        self.laser_enable_state = 'None'
        self.laser_dict = laser_dict
        self.verbose = True

        # get a value in the laser_dict to get the general device string
        self.laser_enable_device = next(iter(self.laser_dict.values()))

        # strip the line number at the end (e.g. PXI6259/line0/port0)
        self.laser_enable_device = self.laser_enable_device[0:-1]

        # add 0:7 to the device string:
        self.laser_enable_device += '0:7'

        # Make sure that all the Lasers are off upon initialization:
        self.disable_all()
        if self.verbose:
            print('LaserTriggers initialized')

    def check_if_laser_in_laser_dict(self, laser):
        '''
        Checks if the laser designation (string) given as argument exists in the laser_dict
        '''
        if laser in self.laser_dict:
            return True
        else:
            raise ValueError('Laser not in the configuration')

    def build_cmd_int(self, laser):
        '''
        Turns the line number into a command integer via 2^n
        '''
        self.line = self.laser_dict[laser][-1]
        return pow(2, int(self.line))

    def enable(self, laser):
        '''
        Enables a single laser line.
        If another laser was on beforehand, this one is switched off.
        '''
        if self.check_if_laser_in_laser_dict(laser):
            if self.verbose:
                print(self.laser_dict[laser])
            self.cmd = self.build_cmd_int(laser)

            with nidaqmx.Task() as task:
                task.do_channels.add_do_chan(
                    self.laser_enable_device,
                    line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                task.write(self.cmd, auto_start=True)

            self.laser_enable_state = laser
            if self.verbose:
                print('Enabled ' + laser)
        else:
            pass

    def enable_all(self):
        '''
        Enables all laser lines.
        '''
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                self.laser_enable_device,
                line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
            task.write(255, auto_start=True)

        self.laser_enable_state = 'all on'
        if self.verbose:
            print('Enabled all lasers')

    def disable_all(self):
        '''
        Disables all laser lines.
        '''
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(
                self.laser_enable_device,
                line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
            task.write(0, auto_start=True)

        self.laser_enable_state = 'off'
        if self.verbose:
            print('Disabled all')

    def state(self):
        """
        Returns laser line if a laser is on, otherwise "False"
        """
        return self.laser_enable_state


class DemoLaserEnabler:
    def __init__(self, laser_dict):
        self.laser_enable_state = 'None'
        self.laser_dict = laser_dict

    def check_if_laser_in_laser_dict(self, laser):
        if laser in self.laser_dict:
            return True
        else:
            raise ValueError('Laser not in the configuration')

    def enable(self, laser):
        if self.check_if_laser_in_laser_dict(laser):
            self.laser_enable_state = laser
        else:
            pass

    def enable_all(self):
        self.laser_enable_state = 'all on'

    def disable_all(self):
        self.laser_enable_state = 'off'

    def state(self):
        return self.laser_enable_state
