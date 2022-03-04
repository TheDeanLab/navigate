from controller.sub_controllers.widget_functions import validate_wrapper
from controller.sub_controllers.gui_controller import GUI_Controller

class Etl_Popup_Controller(GUI_Controller):

    def __init__(self, view, parent_controller, verbose=False):
        super().__init__(view, parent_controller, verbose)

        self.resolution_info = None
        self.widgets = self.view.get_widgets()
        self.lasers = ['488nm', '562nm', '642nm']
        self.mode = None
        self.mag = None

        # event combination
        self.widgets['Mode'].widget.bind('<<ComboboxSelected>>', self.update_magnification)
        self.widgets['Mag'].widget.bind('<<ComboboxSelected>>', self.update_laser)

    def initialize(self, name, data):
        """
        # initialize widgets with data
        """
        if name == 'resolution':
            self.resolution_info = data
            self.widgets['Mode'].widget['values'] = list(data.keys())
            # for laser in self.lasers:
            #     self.widgets[laser + ' Amp'].widget['state'] = 'readonly'
            #     self.widgets[laser + ' Off'].widget['state'] = 'readonly'

    def update_magnification(self, *args):
        """
        # update magnification options when the user changes the focus mode
        """
        # get mode setting
        self.mode = self.widgets['Mode'].widget.get()
        temp = list(self.resolution_info[self.mode].keys())
        self.widgets['Mag'].widget['values'] = temp
        self.widgets['Mag'].widget.set(temp[0])
        # update laser info
        self.update_laser()

    def update_laser(self, *args):
        """
        # update laser info when the user changes magnification setting
        """
        # get magnification setting
        self.mag = self.widgets['Mag'].widget.get()
        for laser in self.lasers:
            self.widgets[laser + ' Amp'].set(self.resolution_info[self.mode][self.mag][laser]['amplitude'])
            self.widgets[laser + ' Off'].set(self.resolution_info[self.mode][self.mag][laser]['offset'])
        