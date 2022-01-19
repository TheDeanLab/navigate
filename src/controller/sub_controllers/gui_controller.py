class GUI_Controller:
    def __init__(self, view, parent_controller = None, verbose=False):
        self.view = view
        self.parent_controller = parent_controller
        self.verbose = verbose
        
    def execute(self, command, *args):
        self.show_verbose_info('command passed from child:', command)
        pass

    def show_verbose_info(self, *info):
        if self.verbose:
            print('From', self.__class__.__name__, ':', *info)