''' Filterwheel classes '''
import time

class DemoFilterWheel():
    def __init__(self, filterdict):
        super().__init__()
        self.filterdict = filterdict
        self.verbose = True

    def _check_if_filter_in_filterdict(self, filter):
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


class FilterWheel():
    def __init__(self, config, parent = None):
        super().__init__()
        self.cfg = config
        self.parent = parent
        self.verbose = True
        # self.parent.sig_set_filter.connect(self.set_filter)
        # self.parent.sig_set_filter_and_wait_until_done.connect(self.sig_set_filter_and_wait_until_done, type=3)

    def set_state_parameter(self, key, value):
        '''
        Sets the state of the parent (in most cases, multiscale_MainWindow)
        In order to do this, a QMutexLocker from the parent has to be acquired
        Args:
            key (str): State dict key
            value (str, float, int): Value to set
        '''
        # with QtCore.QMutexLocker(self.parent.state_mutex):
        if key in self.parent.state:
            self.parent.state[key]=value
            #self.sig_state_updated.emit()
        else:
            print('Set state parameters failed: Key ', key, 'not in state dictionary!')

    def set_filter(self, filter):
        pass

    def sig_set_filter_and_wait_until_done(self, filter):
        pass
