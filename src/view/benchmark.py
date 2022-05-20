
"""
Benchmark different GUI image draw times in tkinter
Environment setup instructions:
    conda create -n gui-test tk matplotlib pillow vispy
    pip install pyopengltk
"""

import time
import tkinter as tk
import numpy as np

from PIL import Image, ImageTk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib as mpl

# import vispy
# from vispy import scene
# from vispy.app import use_app


def pil_gui_test(arr):
    # https://stackoverflow.com/questions/52459277/convert-a-c-or-numpy-array-to-a-tkinter-photoimage-with-a-minimum-number-of-copi

    root = tk.Tk()

    start = time.time()
    img = ImageTk.PhotoImage(Image.fromarray(arr))
    stop = time.time()
    print(f"Pillow run took {stop-start} s")

    lbl = tk.Label(root, image=img)
    lbl.pack()
    root.mainloop()


def matplotlib_gui_test(arr):
    # https://matplotlib.org/3.1.0/gallery/user_interfaces/embedding_in_tk_sgskip.html

    root = tk.Tk()

    f = Figure()
    canvas = FigureCanvasTkAgg(f, root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    start = time.time()

    f.add_subplot(111).imshow(arr)
    canvas.draw()

    stop = time.time()
    print(f"Matplotlib run took {stop-start} s")

    lbl = tk.Label(root)
    lbl.pack()

    root.mainloop()


# def vispy_gui_test(arr):
#     # https://github.com/vispy/vispy/issues/2168
#     # https://vispy.org/gallery/scene/image.html
#
#     root = tk.Tk()
#     app = use_app("tkinter")
#     canvas = vispy.scene.SceneCanvas(
#         keys='interactive', show=True, parent=root, app=app)
#
#     # Set up a viewbox to display the image with interactive pan/zoom
#     view = canvas.central_widget.add_view()
#
#     # Set 2D camera (the camera will scale to the contents in the scene)
#     view.camera = scene.PanZoomCamera(aspect=1)
#     view.camera.flip = (0, 1, 0)
#     view.camera.zoom(1.0)
#
#     # TODO: This isn't setting the window size correctly.
#     # Need to manually expand the window to see the image
#     canvas.native.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
#
#     # Create the image
#     start = time.time()
#     image = scene.visuals.Image(arr, interpolation='nearest',
#                                 parent=view.scene, method='subdivide')
#     view.camera.set_range()
#     stop = time.time()
#     print(f"Vispy run took {stop-start} s")
#
#     app.run()


if __name__ == "__main__":
    # generate image array to plot
    # PIL seems to like a random uint8 matrix y, x, c.
    # arr = np.random.randint(low=255, size=(100, 100, 3), dtype=np.uint8)
    # arr = np.random.randint(low=1000, size=(512, 512, 3), dtype=np.uint16)
    arr = np.random.randint(low=1000, size=(512, 512), dtype=np.uint16)

    # Normalize the data.
    arr_max = np.max(arr)
    arr_min = np.min(arr)
    scaling_factor = 2**8
    arr = scaling_factor * ((arr - arr_min) / (arr_max - arr_min))
    y, x = np.shape(arr)
    arr_lut = np.zeros((y, x, 3))

    # Green LUT
    lookup_table = 'yellow'

    if lookup_table == 'green':
        arr_lut[:, :, 1] = arr
    elif lookup_table == 'red':
        arr_lut[:, :, 0] = arr
    elif lookup_table == 'blue':
        arr_lut[:, :, 2] = arr
    elif lookup_table == 'cyan':
        arr_lut[:, :, 1] = arr
        arr_lut[:, :, 2] = arr
    elif lookup_table == 'magenta':
        arr_lut[:, :, 0] = arr
        arr_lut[:, :, 2] = arr
    elif lookup_table == 'yellow':
        arr_lut[:, :, 0] = arr
        arr_lut[:, :, 1] = arr




    # How about displaying saturated values?
    i = arr_lut == 256

    pil_gui_test(np.uint8(arr_lut))

    # matplotlib_gui_test(arr)

    # vispy_gui_test(arr)
