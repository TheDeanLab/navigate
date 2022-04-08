class GUI_Controller:
    def __init__(self, view, parent_controller=None, verbose=False, configuration_controller=None):
        self.view = view
        self.parent_controller = parent_controller
        self.verbose = verbose

    def initialize(self, configuration_controller):
        """
        # this function initializes GUI based on configuration setting
        # parameter: configuration_controller
        # set range value for entry or spinbox widgets; 
        # add values to combobox
        # get other necessary information for configuration.yml
        """
        pass

    def set_experiment_values(self, setting_dict):
        """
        # this function sets values of widgets based on experiment setting
        # setting_dict is a dictionary
        """
        pass

    def update_experiment_values(self, setting_dict):
        """
        # this function collects all the values of widgets
        # setting_dict is a reference of experiment dictionary
        # update the dictionary directly
        """
        pass
        
    def execute(self, command, *args):
        self.show_verbose_info('command passed from child:', command)
        pass

    def show_verbose_info(self, *info):
        if self.verbose:
            print('From', self.__class__.__name__, ':', *info)
