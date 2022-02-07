from controller.sub_controllers.gui_controller import GUI_Controller
import tkinter as tk
import numpy as np

class Camera_View_Controller(GUI_Controller):
    def __init__(self, view, camera, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        #  Starting Mode
        self.mode = 'stop'
        self.camera = camera
        self.canvas = self.view.matplotlib_canvas
        self.figure = self.view.matplotlib_figure
        self.colormap = 'gray'
        self.image_count = 0
        self.temp_array = None
        self.rolling_frames = 1

    #  Set mode for the execute statement in main controller
    def set_mode(self, mode=''):
        self.mode = mode

    def populate_view(self):
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1.5)

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
        else self.rolling_frames > 1:
            self.image_count = self.image_count + 1
            if self.image_count == 1:
                self.temp_array = image
            else:
                self.temp_array = np.dstack((self.temp_array, image))
                if np.shape(self.temp_array)[2] > self.rolling_frames:
                    self.temp_array = np.delete(self.temp_array, 0, 2)
            self.view.cam_counts.count.set(np.max(self.temp_array))

    def lookup_table_range(self):
        """
        #  Specify the minimum and maximum intensity values to display in the image
        #  Will need to see if the self.view.scale_pallete.count_scale is checked.
        #  If so, the user will need to provide inputs for the lookup table.
        """
        pass

    def display_image(self, image):
        self.image_count = 0
        self.colormap = self.view.scale_pallete.color.get()
        self.update_max_counts(image)
        self.figure.add_subplot(111).imshow(image, self.colormap)
        self.figure.gca().set_axis_off()
        self.canvas.draw()
