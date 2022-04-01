from controller.sub_controllers.gui_controller import GUI_Controller
import tkinter as tk
import numpy as np
import cv2
from PIL import Image, ImageTk
import time


class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting Widgets/Buttons
        self.image_metrics = view.image_metrics.get_widgets()
        # keys = ['Frames to Avg', 'Image Max Counts', 'Channel']

        self.pallete = view.scale_pallete.get_widgets()
        # keys = ['Gray','Gradient','Rainbow', 'Autoscale', 'Min','Max']

        # Binding for Pallete
        self.pallete['Autoscale'].widget.config(command=self.update_minmax)

        self.display = 'PIL'
        # PIL or Matplotlib

        #  Starting Mode
        self.mode = 'stop'
        self.colormap = 'gray'
        self.image_count = 0
        self.temp_array = None
        self.rolling_frames = 1
        self.live_subsampling = self.parent_controller.configuration.CameraParameters['display_live_subsampling']

        if self.display == 'PIL':
            # PIL
            self.canvas = self.view.canvas

        elif self.display == 'Matplotlib':
            # Matplot
            self.canvas = self.view.matplotlib_canvas
            self.figure = self.view.matplotlib_figure
        else:
            print("Image Display Configured Improperly in camera_view_controller")


        # self.view.scale_pallete.autoscale.trace_add(self.update_counts_display())

    def initialize(self, name, data):
        '''
        #### Function that sets widgets based on data given from main controller/config
        '''
        # Pallete section (colors, autoscale, min/max counts)
        if name == 'minmax':
            min = data[0]
            max = data[1]

            # Invoking defaults
            self.pallete['Gray'].widget.invoke()
            self.pallete['Autoscale'].widget.invoke()

            # Populating defaults
            self.pallete['Min'].set(min)
            self.pallete['Max'].set(max)
            self.pallete['Min'].widget['state'] = 'disabled'
            self.pallete['Max'].widget['state'] = 'disabled'
        
        # Image Metrics section
        if name == 'image':
            frames = data[0]
            # Populating defaults
            self.image_metrics['Frames'].set(frames)


    #  Set mode for the execute statement in main controller
    def set_mode(self, mode=''):
        self.mode = mode

    def populate_view(self):
        # self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1.5)
        pass

    # def update_counts_display(self):
    # """
    # Would ideally like to have the ability to change whether or not the state is normal, disabled, or read only,
    # depending upon the autoscale checkbox state...
    # """
    #     if self.view.scale_pallete.autoscale.get() is True:
    #         self.view.scale_pallete.min_counts_spinbox(state="readonly")
    #         self.view.scale_pallete.max_counts_spinbox(state="readonly")
    #     else:
    #         self.view.scale_pallete.min_counts_spinbox(state=NORMAL)
    #         self.view.scale_pallete.max_counts_spinbox(state=NORMAL)


    def update_max_counts(self, image):
        """
        #  Function gets the number of frames to average from the VIEW.
        #  If frames to average == 0 or 1, provides the maximum value from the last acquired data.
        #  If frames to average >1, initializes a temporary array, and appends each subsequent image to it.
        #  Once the number of frames to average has been reached, deletes the first image in.
        #  Reports the rolling average.
        """
        self.rolling_frames = int(self.view.cam_counts.avg_frame.get())
        if self.rolling_frames == 0:
            self.view.cam_counts.avg_frame.set(1)
            self.view.cam_counts.count.set(np.max(image))
        elif self.rolling_frames == 1:
            self.view.cam_counts.count.set(np.max(image))
        else:
            self.image_count = self.image_count + 1
            if self.image_count == 1:
                self.temp_array = image
            else:
                self.temp_array = np.dstack((self.temp_array, image))
                if np.shape(self.temp_array)[2] > self.rolling_frames:
                    self.temp_array = np.delete(self.temp_array, 0, 2)
            self.view.cam_counts.count.set(np.max(self.temp_array))

    def display_image(self, image):
        """
        #  Displays a camera image using the Lookup Table specified in the View.
        #  If Autoscale is selected, automatically calculates the min and max values for the data.
        #  If Autoscale is not selected, takes the user values as specified in the min and max counts.
        """
        self.image_count = 0

        # #  Update the colorbar.
        # self.colormap = self.view.scale_pallete.color.get()

        # #  Update the GUI according to the instantaneous or rolling average max counts.
        # self.update_max_counts(image)

        #  Down-sample the data according to the configuration file.
        if self.live_subsampling != 1:
            image = cv2.resize(image, (int(np.shape(image)[0]/self.live_subsampling),
                                       int(np.shape(image)[1]/self.live_subsampling)))

        # #  Specify the lookup table min and maximum.
        # autoscale = self.view.scale_pallete.autoscale.get()
        # if autoscale is True:
        #     min = np.min(image)
        #     max = np.max(image)
        # else:
        #     min = self.view.scale_pallete.min_counts.get()
        #     max = self.view.scale_pallete.max_counts.get()

        if self.display == 'Matplotlib':
            begin_time = time.perf_counter()
            self.figure.add_subplot(111).imshow(image, self.colormap, vmin=min, vmax=max)
            self.figure.gca().set_axis_off()
            self.canvas.draw()
            end_time = time.perf_counter()

        elif self.display == 'PIL':
            begin_time = time.perf_counter()
            self.img = ImageTk.PhotoImage(Image.fromarray(image))
            self.canvas.create_image(0, 0, image=self.img, anchor='nw')
            end_time = time.perf_counter()
            print("PIL display")

        # if self.verbose:
        print('Time necessary to display an image:', (end_time - begin_time) * 1000)


    def update_channel_idx(self, channel_idx):
        self.view.cam_counts.channel_idx.set(channel_idx)

    def update_minmax(self):
        on_off = self.pallete['Autoscale'].get()
        if on_off == True: # Checkbox selected
            self.pallete['Min'].widget['state'] = 'disabled'
            self.pallete['Max'].widget['state'] = 'disabled'
        elif on_off == False: # Checkbox unselected
            self.pallete['Min'].widget['state'] = 'normal'
            self.pallete['Max'].widget['state'] = 'normal'