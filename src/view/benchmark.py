
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

import vispy
from vispy import scene
from vispy.app import use_app


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


def vispy_gui_test(arr):
    # https://github.com/vispy/vispy/issues/2168
    # https://vispy.org/gallery/scene/image.html

    root = tk.Tk()
    app = use_app("tkinter")
    canvas = vispy.scene.SceneCanvas(
        keys='interactive', show=True, parent=root, app=app)

    # Set up a viewbox to display the image with interactive pan/zoom
    view = canvas.central_widget.add_view()

    # Set 2D camera (the camera will scale to the contents in the scene)
    view.camera = scene.PanZoomCamera(aspect=1)
    view.camera.flip = (0, 1, 0)
    view.camera.zoom(1.0)

    # TODO: This isn't setting the window size correctly.
    # Need to manually expand the window to see the image
    canvas.native.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Create the image
    start = time.time()
    image = scene.visuals.Image(arr, interpolation='nearest',
                                parent=view.scene, method='subdivide')
    view.camera.set_range()
    stop = time.time()
    print(f"Vispy run took {stop-start} s")

    app.run()


if __name__ == "__main__":
    # generate image array to plot
    arr = np.random.randint(low=255, size=(100, 100, 3), dtype=np.uint8)

    pil_gui_test(arr)

    matplotlib_gui_test(arr)

    vispy_gui_test(arr)
