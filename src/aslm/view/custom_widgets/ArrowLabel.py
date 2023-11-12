# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Standard Library Imports
import tkinter as tk

# Third Party Imports
from PIL import Image, ImageTk

# Local Imports
from aslm.tools.image import create_arrow_image


class ArrowLabel(tk.Label):
    """A label that displays an arrow image."""

    def __init__(
        self,
        master,
        *args,
        xys=[],
        direction="right",
        image_width=300,
        image_height=200,
        **kwargs
    ):
        """Initialize the ArrowLabel.

        Parameters
        ----------
        master : tk.Widget
            The parent widget.
        *args : list
            Additional positional arguments to pass to the tk.Label constructor.
        xys : list of tuples
            The coordinates of the arrow.
        direction : str
            The direction of the arrow. One of "right", "left", "up", or "down".
        image_width : int
            The width of the image.
        image_height : int
            The height of the image.
        **kwargs : dict
            Additional keyword arguments to pass to the tk.Label constructor.
        """
        super().__init__(master, *args, **kwargs)
        img = create_arrow_image(xys, image_width, image_height, direction)
        image_gif = img.convert("P", palette=Image.ADAPTIVE)
        #: ImageTk.PhotoImage: The image to display.
        self.image = ImageTk.PhotoImage(image_gif)
        self["image"] = self.image
