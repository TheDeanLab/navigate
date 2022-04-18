"""
Camera View Tab
"""
import numpy as np
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from controller.devices.camera.SyntheticCamera import Camera as camera

# the figure that will contain the plot
# fig = Figure(figsize=(4, 4), dpi=100)

# Generate Waveform
# synthetic_image = camera.read_camera()

# adding the subplot
# plot1 = fig.add_subplot(111)
# plot1.axis('off')

# add the image
# TODO: Handle the synthetic and real images.
# plot1.imshow(synthetic_image, cmap='gray')

# creating the Tkinter canvas containing the Matplotlib figure
# canvas = FigureCanvasTkAgg(fig, master=camera_tab)
# canvas.draw()

# placing the canvas on the Tkinter window
# canvas.get_tk_widget().pack()

# Need to add image code here, using a label to hold the image.
# image_viewer = ttk.Label(camera_tab)
# image_viewer.grid(row=0, column=0, sticky=NSEW)

"""
Maximum intensity projection tab
"""
# Third Party Imports


# TODO: Be able to change the channel number, load the data, and perform maximum intensity projection in parallel.
# TODO: May need a button that specifies when to perform the maximum
# intensity projection.

# the figure that will contain the plot
# fig = Figure(figsize=(8, 3), dpi=100)

# Generate Waveform
# synthetic_image = camera.read_camera(camera)

# XY
# plot1 = fig.add_subplot(131, title='XY')
# plot1.axis('off')
# plot1.imshow(synthetic_image, cmap='gray')

# YZ
# plot2 = fig.add_subplot(132, title='YZ')
# plot2.axis('off')
# plot2.imshow(synthetic_image, cmap='gray')

# XZ
# plot3 = fig.add_subplot(133, title='XZ')
# plot3.axis('off')
# plot3.imshow(synthetic_image, cmap='gray')

# creating the Tkinter canvas containing the Matplotlib figure
# canvas = FigureCanvasTkAgg(fig, master=maximum_intensity_projection_tab)
# canvas.draw()

# placing the canvas on the Tkinter window
# canvas.get_tk_widget().pack()
