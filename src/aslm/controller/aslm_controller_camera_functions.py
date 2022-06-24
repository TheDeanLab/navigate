"""
ASLM camera functions.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
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
