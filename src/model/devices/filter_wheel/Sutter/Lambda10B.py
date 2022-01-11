"""
Module for controlling Sutter Lambda Filter Wheels
Author: Kevin Dean,

Command byte = (wheel * 128) + (speed * 16) + position
https://www.sutter.com/manuals/LB10-3_OpMan.pdf

TODO: Currently moves multiple filter wheels to the same position.  In the future, it may be nice to have
      a way to move multiple filter wheels to different positions independently.
"""
# Standard Imports
import serial
import time

# Local Imports
from model.devices.filter_wheel.FilterWheelBase import FilterWheelBase

class FilterWheel(FilterWheelBase):
    def __init__(self, model, verbose):
        '''
        Load the Default Parameters
        '''
        self.comport = model.FilterWheelParameters['filter_wheel_port']
        self.baudrate = model.FilterWheelParameters['baudrate']
        self.filterdict = model.FilterWheelParameters['available_filters']
        self.number_of_filter_wheels = model.FilterWheelParameters['number_of_filter_wheels']
        self.read_on_init = True
        self.verbose = verbose
        self.wait_until_done_delay = 0.25 # Delay in s for the wait until done function

        # Open Serial Port
        try:
            if self.verbose:
                print('Opening Filter Wheel on Serial Port', self.comport)
            self.serial = serial.Serial(self.comport, self.baudrate, timeout=.25)
        except serial.SerialException:
            raise UserWarning('Could not communicate with Sutter Lambda 10-B.')

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

    def check_if_filter_in_filterdict(self, filterposition):
        '''
        Checks if the filter designation (string) given as argument
        exists in the filterdict
        '''
        if filterposition in self.filterdict:
            return True
        else:
            raise ValueError('Filter designation not in the configuration')

    def set_filter(self, filterposition=0, speed=2, wait_until_done=False):
        '''
        Change the filter wheel to the filter designated by the filterposition argument.
        '''
        if self.check_if_filter_in_filterdict(filterposition) is True:
            # Identify the Filter Number from the Filter Dictionary
            self.wheel_position = self.filterdict[filterposition]
            # Make sure you are moving it to a reasonable filter position
            assert self.wheel_position in range(10)
            # Make sure you are moving it at a reasonable speed
            assert speed in range(8)

            # If previously we did not confirm that the initialization was complete, check now.
            if not self.init_finished:
                self.read(2)
                self.init_finished = True
                if self.verbose:
                    print('Done initializing filter wheel.')

            for wheel_idx in range(self.number_of_filter_wheels):
                ''' 
                Loop through each filter, and send the binary sequence via serial to move to the desired filter wheel position
                When number_of_filter_wheels = 1, loop executes once, and only wheel A changes.
                When number_of_filter_wheels = 2, loop executes twice, with both wheel A and B moving to the same position sequentially
                Filter Wheel Command Byte Encoding = wheel + (speed*16) + position = command byte
                '''

                if self.verbose:
                    print("Moving Filter Wheel:", wheel_idx)
                outputcommand = wheel_idx*128+self.wheel_position + 16 * speed
                outputcommand = outputcommand.to_bytes(1, 'little')

                if self.verbose:
                    print('Sending Filter Wheel Command:', outputcommand)
                self.serial.write(outputcommand)
                if wait_until_done:
                    time.sleep(self.wait_until_done_delay)

    def read(self, num_bytes):
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            if num_waiting == num_bytes:
                break
            time.sleep(0.02)
        else:
            raise UserWarning("The serial port to the Sutter Lambda 10-B is on, but it isn't responding as expected.")
        return self.serial.read(num_bytes)

    def close(self):
        if self.verbose:
            print('Closing the Filter Wheel Serial Port')
        self.set_filter('Empty-Alignment')
        self.serial.close()

# Filter Wheel Testing.
if (__name__ == "__main__"):
    number_of_filter_wheels = 2
    comport = 'COM9'
    print("Attempting: ", comport)
    filterdict = {'Empty-Alignment': 0,
                  'GFP - FF01-515/30-32': 1,
                  'RFP - FF01-595/31-32': 2,
                  'Far-Red - BLP01-647R/31-32': 3,
                  'Blocked1': 4,
                  'Blocked2': 5,
                  'Blocked3': 6,
                  'Blocked4': 7,
                  'Blocked5': 8,
                  'Blocked6': 9}
    try:
        filter = Lambda10B(number_of_filter_wheels, comport, filterdict)
        filter.set_filter('GFP - FF01-515/30-32')
        filter.close()
        print('Success!')
    except serial.SerialException:
        print("Failed: ", comport)

