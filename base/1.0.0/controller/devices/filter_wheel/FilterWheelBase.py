'''
Filterwheel Base Class
'''

class FilterWheelBase():
    def __init__(self, model, verbose):
        self.comport = model.FilterWheelParameters['filter_wheel_port']
        self.baudrate = model.FilterWheelParameters['baudrate']
        self.filterdict = model.FilterWheelParameters['available_filters']
        self.number_of_filter_wheels = model.FilterWheelParameters['number_of_filter_wheels']
        self.verbose = verbose

    def check_if_filter_in_filterdict(self, filterposition):
        print("FilterWheelBase: Not Implemented")

    def set_filter(self, filterposition=0, speed=2, wait_until_done=False):
        print("FilterWheelBase: Not Implemented")

    def read(self, num_bytes):
        print("FilterWheelBase: Not Implemented")

    def close(self):
        print("FilterWheelBase: Not Implemented")
