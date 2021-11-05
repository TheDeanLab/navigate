"""
mesoSPIM Module for controlling Sutter Lambda Filter Wheels
Author: Kevin Dean,
Command byte = (wheel * 128) + (speed * 16) + position
https://www.sutter.com/manuals/LB10-3_OpMan.pdf

TODO: Independent control of multiple filter wheels?
"""

import serial
import time

class Lambda10B:
    def __init__(self,number_of_filter_wheels, comport, filterdict, baudrate=9600, read_on_init=True):
        super().__init__()

        ''' Load the Default Parameters '''
        self.COMport = comport
        self.baudrate = baudrate
        self.filterdict = filterdict
        self.number_of_filter_wheels = number_of_filter_wheels
        self.verbose = True

        ''' Delay in s for the wait until done function '''
        self.wait_until_done_delay = 0.25

        # Open Serial Port
        try:
            if self.verbose:
                print('Opening Serial Port')
            self.serial = serial.Serial(self.COMport, self.baudrate, timeout=.25)
        except serial.SerialException:
            raise UserWarning('Could not communicate with Sutter Lambda 10-B.')

        # Place Controller Into 'Online' Mode
        if self.verbose:
            print('Putting Controller Into Online Mode')
        self.serial.write(bytes.fromhex('ee'))

        # Check to see if the initialization sequence has finished.
        if read_on_init:
            self.read(2)  # class 'bytes'
            self.init_finished = True
            if self.verbose:
                print('Done initializing filter wheel.')
        else:
            self.init_finished = False

        if self.verbose:
            print('Setting Filter to Default Filter Position')
        self.set_filter('Empty-Alignment')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.verbose:
            print('Closing the Filter Wheel Serial Port')
        self.close()

    def _check_if_filter_in_filterdict(self, filterposition):
        # Checks if the filter designation (string) given as argument exists in the filterdict
        if filterposition in self.filterdict:
            return True
        else:
            raise ValueError('Filter designation not in the configuration')

    def set_filter(self, filterposition=0, speed=2, wait_until_done=False):
        # Confirm that the filter is present in the filter dictionary
        if self._check_if_filter_in_filterdict(filterposition) is True:

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
                ''' Loop through each filter, and send the binary sequence via serial to move to the desired filter 
                wheel position
                When number_of_filter_wheels = 1, loop executes once, and only wheel A changes.
                When number_of_filter_wheels = 2, loop executes twice, with both wheel A and B moving to the same position sequentially
                Filter Wheel Command Byte Encoding = wheel + (speed*16) + position = command byte'''

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
        self.set_filter()
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
    except serial.SerialException:
        print("Failed: ", comport)

