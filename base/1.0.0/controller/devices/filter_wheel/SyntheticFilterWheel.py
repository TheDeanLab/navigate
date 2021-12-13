

class SyntheticFilterWheel():
    def __init__(self, filterdict):
        super().__init__()
        self.filterdict = filterdict
        self.verbose = True

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
