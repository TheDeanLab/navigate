"""
Filter Wheel Base Class
"""
#  Standard Library Imports
import time
import serial

# Third Party Imports
import numpy as np

# Local Imports

class FilterWheelBase:
    def __init__(self, model, verbose):
        self.comport = model.FilterWheelParameters['filter_wheel_port']
        self.baudrate = model.FilterWheelParameters['baudrate']
        self.filter_dictionary = model.FilterWheelParameters['available_filters']
        self.number_of_filter_wheels = model.FilterWheelParameters['number_of_filter_wheels']
        self.wheel_position = 0
        self.verbose = verbose

    def check_if_filter_in_filterdict(self, filterposition):
        """
        # Checks if the filter designation (string) given as argument
        # exists in the filterdict
        """
        print("FilterWheelBase: Not Implemented")

    def filter_change_delay(self, filter_name):
        print("FilterWheelBase: Not Implemented")

    def set_filter(self, filter_name, wait_until_done=True):
        """
        # Change the filter wheel to the filter designated by the filterposition argument.
        """
        print("FilterWheelBase: Not Implemented")

    def read(self, num_bytes):
        """
        # Reads the specified number of bytes from the serial port.
        """
        print("FilterWheelBase: Not Implemented")

    def close(self):
        """
        # Closes the serial port.
        """
        print("FilterWheelBase: Not Implemented")


class SyntheticFilterWheel(FilterWheelBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)

    def check_if_filter_in_filterdict(self, filter):
        """
        # Checks if the filter designation (string) given as argument
        # exists in the filterdict
        """
        if filter in self.filterdict.keys():
            return True
        else:
            raise ValueError('Filter designation not in the configuration')

    def set_filter(self, filter, speed=2, wait_until_done=False):
        """
        # Change the filter wheel to the filter designated by the filterposition argument.
        """
        if self.check_if_filter_in_filterdict(filter) is True:
            if self.verbose:
                print('Filter set to: ', str(filter))
            if wait_until_done:
                time.sleep(0.03)

    def read(self, num_bytes):
        """
        # Reads the specified number of bytes from the serial port.
        """
        pass

    def close(self):
        """
        # Closes the serial port.
        """
        pass


class SutterFilterWheel(FilterWheelBase):
    """
    Module for controlling Sutter Lambda Filter Wheels

    Command byte = (wheel * 128) + (self.speed * 16) + position
    https://www.sutter.com/manuals/LB10-3_OpMan.pdf

    TODO: Currently moves multiple filter wheels to the same position.  In the future, it may be nice to have
          a way to move multiple filter wheels to different positions independently.
    """

    def __init__(self, model, verbose):
        super().__init__(model, verbose)

        # Sutter Lambda 10-B Specific Initializations
        self.verbose = verbose
        self.read_on_init = True
        self.wait_until_done = True
        self.wait_until_done_delay = 0.25
        self.speed = 2

        # Delay in s for the wait until done function
        self.delay_matrix = np.matrix([[0, 0.031, 0.051, 0.074, 0.095, 0.115],
                                       [0, 0.040, 0.065, 0.095, 0.120, 0.148],
                                       [0, 0.044, 0.075, 0.105, 0.136, 0.168],
                                       [0, 0.050, 0.088, 0.127, 0.165, 0.205],
                                       [0, 0.060, 0.108, 0.156, 0.205, 0.250],
                                       [0, 0.068, 0.123, 0.178, 0.235, 0.290],
                                       [0, 0.124, 0.235, 0.350, 0.460, 0.580],
                                       [0, 0.230, 0.440, 0.650, 0.860, 1.100]])

        # Open Serial Port
        try:
            if self.verbose:
                print('Opening Filter Wheel on Serial Port', self.comport)
            self.serial = serial.Serial(self.comport, self.baudrate, timeout=.25)
        except serial.SerialException:
            raise UserWarning('Could not communicate with Sutter Lambda 10-B via COMPORT', self.comport)

        # Place Controller Into 'Online' Mode
        if self.verbose:
            print('Putting Sutter Lambda 10-B Into Online Mode')
        self.serial.write(bytes.fromhex('ee'))

        # Check to see if the initialization sequence has finished.
        if self.read_on_init:
            self.read(2)  # class 'bytes'
            self.init_finished = True
            if self.verbose:
                print('Done initializing the Sutter Lambda 10-B filter wheel.')
        else:
            self.init_finished = False

        if self.verbose:
            print('Setting Sutter Lambda 10-B Filter to Default Filter Position')
        self.set_filter('Empty-Alignment')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.verbose:
            print('Closing the Filter Wheel Serial Port')
        self.close()

    def check_if_filter_in_filter_dictionary(self, filter_name):
        """
        # Checks if the filter designation (string) given as argument
        # exists in the filter dictionary
        """
        if filter_name in self.filter_dictionary:
            return True
        else:
            raise ValueError('Filter designation not in the configuration')

    def filter_change_delay(self, filter_name):
        """
        # The Sutter Filter wheels require ~40 ms to change between adjacent filter positions
        # See page 38: https://www.sutter.com/manuals/LB10-3_OpMan.pdf
        """
        # Old Position
        old_position = self.wheel_position

        # New Position
        self.wheel_position = self.filter_dictionary[filter_name]
        delta_position = int(abs(old_position-self.wheel_position))

        # Calculate Delay
        self.wait_until_done_delay = (self.delay_matrix[self.speed, delta_position])

    def set_filter(self, filter_name, wait_until_done=True):
        """
        # Change the filter wheel to the filter designated by the filter position argument.
        """
        if self.check_if_filter_in_filter_dictionary(filter_name) is True:
            # Calculate the Delay Needed to Change the Positions
            self.filter_change_delay(filter_name)

            # Make sure you are moving it to a reasonable filter position
            assert self.wheel_position in range(10)

            # Make sure you are moving it at a reasonable self.speed
            assert self.speed in range(8)

            # If previously we did not confirm that the initialization was complete, check now.
            if not self.init_finished:
                self.read(2)
                self.init_finished = True
                if self.verbose:
                    print('Done initializing filter wheel.')

            for wheel_idx in range(self.number_of_filter_wheels):
                """ 
                # Loop through each filter, and send the binary sequence via serial to 
                # move to the desired filter wheel position
                # When number_of_filter_wheels = 1, loop executes once, and only wheel A changes.
                # When number_of_filter_wheels = 2, loop executes twice, with both wheel A and 
                # B moving to the same position sequentially
                # Filter Wheel Command Byte Encoding = wheel + (self.speed*16) + position = command byte
                """

                if self.verbose:
                    print("Moving Filter Wheel:", wheel_idx)

                output_command = wheel_idx*128+self.wheel_position + 16 * self.speed
                output_command = output_command.to_bytes(1, 'little')

                if self.verbose:
                    print('Sending Filter Wheel Command:', output_command)
                self.serial.write(output_command)

            #  Wheel Position Change Delay
            if wait_until_done:
                time.sleep(self.wait_until_done_delay)

    def read(self, num_bytes):
        """
        # Reads the specified number of bytes from the serial port.
        """
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            raise UserWarning("The serial port to the Sutter Lambda 10-B is on, but it isn't responding as expected.")
        return self.serial.read(num_bytes)

    def close(self):
        """
        # Closes the serial port.
        """
        if self.verbose:
            print('Closing the Filter Wheel Serial Port')
        self.set_filter('Empty-Alignment')
        self.serial.close()

if __name__ == "__main__":
    pass
