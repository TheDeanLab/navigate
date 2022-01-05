"""
Module for synthetic Filter Wheels
Author: Kevin Dean,
"""
#Standard Library Imports
import time

# Local Imports
from model.devices.filter_wheel.FilterWheelBase import FilterWheelBase

class SyntheticFilterWheel(FilterWheelBase):
    def __init__(self, model, verbose):
        self.filterdict = model.FilterWheelParameters['available_filters']
        self.verbose = verbose

    def check_if_filter_in_filterdict(self, filter):
        '''
        Checks if the filter designation (string) given as argument
        exists in the filterdict
        '''
        if filter in self.filterdict:
            return True
        else:
            raise ValueError('Filter designation not in the configuration')

    def set_filter(self, filter, wait_until_done=False):
        if self._check_if_filter_in_filterdict(filter) is True:
            if self.verbose:
                print('Filter set to: ', str(filter))
            if wait_until_done:
                time.sleep(1)

    def read(selfself, num_bytes):
        pass

    def close(self):
        pass
