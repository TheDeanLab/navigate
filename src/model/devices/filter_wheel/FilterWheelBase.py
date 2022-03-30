"""
Filterwheel Base Class
"""


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
