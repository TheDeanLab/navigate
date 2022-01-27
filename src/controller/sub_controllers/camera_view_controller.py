from controller.sub_controllers.gui_controller import GUI_Controller

class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        #Starting Mode
        self.mode = 'continuous'

        #Widget Command Binds for displaying live feed of camera




    #Set mode for the execute statement in main controller
    def set_mode(self, mode=''):
        self.mode = mode
    
    def live_feed(self):
        pass