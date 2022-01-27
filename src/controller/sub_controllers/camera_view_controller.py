from controller.sub_controllers.gui_controller import GUI_Controller
from PIL import Image, ImageTk
import time

class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, camera, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        #Starting Mode
        self.mode = 'live'
        self.camera = camera
        self.canvas = self.view.canvas
        #Widget Command Binds for displaying live feed of camera




    #Set mode for the execute statement in main controller
    def set_mode(self, mode=''):
        self.mode = mode
    
    #TODO Currently works for synthetic image, however if you try to reacquire another live feed it will not display
    def live_feed(self):
        #This will display the image to the view doesnt necessarily process logic
        reads = 0
        images = 0
        time.sleep(3.0) # Trying to give main window time to fully load, i guess tkinter doesnt play well with threads
        while self.mode == 'live':
            #Reading frames from camera, this is an array of numpy arrays, each element is a frame
            feed = self.camera.read_camera()
            reads += 1 #Tracking reads
            print("Reads: " + str(reads))
            #For each frame in feed convert np.array to tk photoimage then display to canvas
            for frame in feed:
                #Converting array to image and then displaying to canvas widget
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=img, anchor='nw')
                images += 1
                print("Frames displayed: " + str(images))
                time.sleep(0.15) #This is to give some semblance of a framerate and too give time to see if the "feed" is working
        

        