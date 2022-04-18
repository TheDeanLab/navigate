"""
Class for digital and analog modulation of laser devices.
Goal is to set the DC value of the laser intensity with the analog voltage, and then rapidly turn it on and off
with the digital signal.
Lasers should be configured to operate in a mixed modulation mode.
"""

import nidaqmx
from nidaqmx.constants import LineGrouping


class LaserTriggerBase:
    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        # Number of Lasers
        # TODO: Make it so that we can iterate through each laser and create a
        # task.
        self.number_of_lasers = self.model.LaserParameters['number_of_lasers']

        # Minimum and Maximum Laser Voltages
        self.laser_min_do = self.model.LaserParameters['laser_min_do']
        self.laser_max_do = self.model.LaserParameters['laser_max_do']
        self.laser_min_ao = self.model.LaserParameters['laser_min_ao']
        self.laser_max_ao = self.model.LaserParameters['laser_max_ao']

        # Digital Ports
        self.switching_port = self.model.DAQParameters['laser_port_switcher']
        self.laser_0_do_port = self.model.DAQParameters['laser_0_do']
        self.laser_1_do_port = self.model.DAQParameters['laser_1_do']
        self.laser_2_do_port = self.model.DAQParameters['laser_2_do']

        # Analog Ports
        self.laser_0_ao_port = self.model.DAQParameters['laser_0_ao']
        self.laser_1_ao_port = self.model.DAQParameters['laser_1_ao']
        self.laser_2_ao_port = self.model.DAQParameters['laser_2_ao']

        # Digital Output Default State
        self.switching_state = False
        self.laser_0_do_state = False
        self.laser_1_do_state = False
        self.laser_2_do_state = False

        # Analog Output Default Voltage
        self.laser_0_ao_voltage = 0
        self.laser_1_ao_voltage = 0
        self.laser_2_ao_voltage = 0

    def __del__(self):
        if self.verbose:
            print("Not Implemented in LaserTriggerBase")

    def enable_low_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """
        if self.verbose:
            print("Not Implemented in LaserTriggerBase")

    def enable_high_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """
        if self.verbose:
            print("Not Implemented in LaserTriggerBase")

    def trigger_digital_laser(self, current_laser_index):
        if self.verbose:
            print("Not Implemented in LaserTriggerBase")

    def turn_off_lasers(self):
        if self.verbose:
            print("Not Implemented in LaserTriggerBase")

    def set_laser_analog_voltage(
            self,
            current_laser_index,
            current_laser_intensity):
        """
        # Sets the constant voltage on the DAQ according to the laser index and intensity, which is a percentage.
        """
        if self.verbose:
            print("Not Implemented in LaserTriggerBase")


class LaserTriggers(LaserTriggerBase):
    def __init__(self, model, experiment, verbose=False):
        super().__init__(model, experiment, verbose)

        # Initialize Digital Tasks
        self.switching_task = nidaqmx.Task()
        self.laser_0_do_task = nidaqmx.Task()
        self.laser_1_do_task = nidaqmx.Task()
        self.laser_2_do_task = nidaqmx.Task()

        # Initialize Analog Tasks
        self.laser_0_ao_task = nidaqmx.Task()
        self.laser_1_ao_task = nidaqmx.Task()
        self.laser_2_ao_task = nidaqmx.Task()

        # Add Ports to each Digital Task
        self.switching_task.do_channels.add_do_chan(
            self.switching_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.laser_0_do_task.do_channels.add_do_chan(
            self.laser_0_do_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.laser_1_do_task.do_channels.add_do_chan(
            self.laser_1_do_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.laser_2_do_task.do_channels.add_do_chan(
            self.laser_2_do_port, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)

        # Add Ports to each Analog Task - Set Voltage Limits
        self.laser_0_ao_task.ao_channels.add_ao_voltage_chan(
            self.laser_0_ao_port, min_val=self.laser_min_ao, max_val=self.laser_max_ao)
        self.laser_1_ao_task.ao_channels.add_ao_voltage_chan(
            self.laser_1_ao_port, min_val=self.laser_min_ao, max_val=self.laser_max_ao)
        self.laser_2_ao_task.ao_channels.add_ao_voltage_chan(
            self.laser_2_ao_port, min_val=self.laser_min_ao, max_val=self.laser_max_ao)

        # Write Tasks
        self.switching_task.write(self.switching_state, auto_start=True)
        self.laser_0_do_task.write(self.laser_0_do_state, auto_start=True)
        self.laser_1_do_task.write(self.laser_1_do_state, auto_start=True)
        self.laser_2_do_task.write(self.laser_2_do_state, auto_start=True)

        self.laser_0_ao_task.write(self.laser_0_ao_voltage, auto_start=True)
        self.laser_1_ao_task.write(self.laser_1_ao_voltage, auto_start=True)
        self.laser_2_ao_task.write(self.laser_2_ao_voltage, auto_start=True)

    def __del__(self):
        """
        # Close the laser switching task, digital output tasks, and analog output tasks.
        """
        self.switching_task.close()

        self.laser_0_do_task.close()
        self.laser_1_do_task.close()
        self.laser_2_do_task.close()

        self.laser_0_ao_task.close()
        self.laser_1_ao_task.close()
        self.laser_2_ao_task.close()

    def enable_low_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """

        self.switching_state = False
        self.switching_task.write(self.switching_state, auto_start=True)
        print("Low Resolution Laser Path Enabled")

    def enable_high_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """

        self.switching_state = True
        self.switching_task.write(self.switching_state, auto_start=True)
        print("High Resolution Laser Path Enabled")

    def trigger_digital_laser(self, current_laser_index):
        self.turn_off_lasers()
        if current_laser_index == 0:
            self.laser_0_do_task.write(True, auto_start=True)
        elif current_laser_index == 1:
            self.laser_1_do_task.write(True, auto_start=True)
        elif current_laser_index == 2:
            self.laser_2_do_task.write(True, auto_start=True)

    def turn_off_lasers(self):
        self.laser_0_do_task.write(False, auto_start=True)
        self.laser_1_do_task.write(False, auto_start=True)
        self.laser_2_do_task.write(False, auto_start=True)

    def set_laser_analog_voltage(
            self,
            current_laser_index,
            current_laser_intensity):
        """
        # Sets the constant voltage on the DAQ according to the laser index and intensity, which is a percentage.
        """
        scaled_laser_voltage = (
            int(current_laser_intensity) / 100) * self.laser_max_ao
        if current_laser_index == 0:
            self.laser_0_ao_task.write(scaled_laser_voltage, auto_start=True)
        elif current_laser_index == 1:
            self.laser_1_ao_task.write(scaled_laser_voltage, auto_start=True)
        elif current_laser_index == 2:
            self.laser_2_ao_task.write(scaled_laser_voltage, auto_start=True)


class SyntheticLaserTriggers(LaserTriggerBase):
    def __init__(self, model, experiment, verbose=False):
        super().__init__(model, experiment, verbose)

    def __del__(self):
        pass

    def enable_low_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """
        self.switching_state = False
        if self.verbose:
            print("Low Resolution Laser Path Enabled")

    def enable_high_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """
        self.switching_state = True
        if self.verbose:
            print("High Resolution Laser Path Enabled")

    def trigger_digital_laser(self, current_laser_index):
        self.turn_off_lasers()
        pass

    def turn_off_lasers(self):
        pass

    def set_laser_analog_voltage(
            self,
            current_laser_index,
            current_laser_intensity):
        """
        # Sets the constant voltage on the DAQ according to the laser index and intensity, which is a percentage.
        """
        pass
