# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

# Standard Library Imports

# Third Party Imports
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Local Imports


def text_array(text: str, offset: tuple = (0, 0)):
    """Create a binary array from a piece of text

    Use Default font to avoid OS related errors.

    Parameters
    ----------
    text : str
        Text to convert
    offset : tuple
        (x,y) offset from upper left of image
    font_size: int
        Size of font in pixels

    Returns
    -------
    np.array
        Binary array of text
    """
    font = ImageFont.load_default()
    bbox = font.getbbox(text)
    im = Image.new(mode="1", size=(bbox[2] + offset[0], bbox[3] + offset[1]))
    ImageDraw.Draw(im).text(xy=offset, text=text, fill=1, font=font)
    return np.array(im, dtype=bool)


def create_arrow_image(xys, image_width=300, image_height=200, direction="right", image=None):
    """Create/Update a Image Object 

    Draw lines and arrows in a Image ojbect

    Parameters
    ----------
    xys : list
        list of points [(x, y),] to draw lines
    image_width : int
        width of image
    image_height: int
        height of image
    direction: str
        arrow directions: "left", "right", "up", "down"
    image: Image/None
        update an exist Image object/create a new Image object

    Returns
    -------
    image:
        Image object
    """
    w, h = image_width, image_height
    if not image:
        image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # draw line
    for i in range(len(xys)-1):
        draw.line([xys[i], xys[i+1]], fill="black", width=2)
    
    # draw arrow
    circle_x, circle_y = xys[-1]
    if direction == "right":
        bounding_circle = ((circle_x-10, circle_y), 10)
        rotation = 270
    elif direction == "left":
        bounding_circle = ((circle_x+10, circle_y), 10)
        rotation = 90
    elif direction == "up":
        bounding_circle = ((circle_x, circle_y+10), 10)
        rotation = 0
    elif direction == "down":
        bounding_circle = ((circle_x, circle_y-10), 10)
        rotation = 180
    draw.regular_polygon(bounding_circle, n_sides=3, rotation=rotation, fill="black")
    
    return image