from controller.sub_controllers.gui_controller import GUI_Controller
from model.aslm_model import Model as model #I imported this because I can not think of the elegant way to pass this to this class, just to get funcitonality for now

class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        #Starting Mode
        self.mode = 'stop'
        self.camera = model.cam
        
        #Widget Command Binds for displaying live feed of camera




    #Set mode for the execute statement in main controller
    def set_mode(self, mode=''):
        self.mode = mode
    
    def live_feed(self):
        #This will display the image to the view doesnt necessarily process logic
        while self.mode == 'live':
            pass
        