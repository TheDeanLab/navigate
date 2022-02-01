"""
Filterwheel Base Class
"""

class FilterWheelBase():
    def __init__(self, model, verbose):
        self.comport = model.FilterWheelParameters['filter_wheel_port']
        self.baudrate = model.FilterWheelParameters['baudrate']
        self.filterdict = model.FilterWheelParameters['available_filters']
        self.number_of_filter_wheels = model.FilterWheelParameters['number_of_filter_wheels']
        self.verbose = verbose

    def check_if_filter_in_filterdict(self, filterposition):
        """
        # Checks if the filter designation (string) given as argument
        # exists in the filterdict
        """
        print("FilterWheelBase: Not Implemented")

    def set_filter(self, filterposition=0, speed=2, wait_until_done=False):
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
