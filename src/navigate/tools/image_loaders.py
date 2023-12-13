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

import numpy as np
import PIL
import glob


class LazyTiff:
    def __init__(self, fp):
        """Lazy-loads a folder containing a sequence of TIFF files using PIL.

        Assumes all TIFF files are single slices, with the same x and y dims.

        Parameters
        ----------
        fp : str
            Path to folder containting sequence of TIFF (.tif) files.

        Returns
        -------
        LazyTiff
            A LazyTiff object that can be indexed like a numpy array.

        Raises
        ------
        FileNotFoundError
            If there are no TIFF files in the folder.

        Examples
        --------
        >>> low_res_fp = '~/2022-07-02/Cell_001'
        >>> low_res = LazyTiff(fp)
        >>> imshow(low_res[:,:,500])
        """

        # How many images in this sequence?
        self._files = sorted(glob.glob(fp + "/*.tif"))
        self._n_files = len(self._files)
        self._image_index = 0
        try:
            # Open the first image to get the sizing
            with PIL.Image.open(self._files[0]) as im:
                self._image = im
                self._width, self._height = im.width, im.height
        except FileNotFoundError:
            raise FileNotFoundError("Is there a TIFF (.tif) in this folder?")

    @property
    def shape(self):
        """Shape of the image sequence.



        Returns
        -------
        tuple
            Shape of the image sequence.
        """
        return (self._width, self._height, self._n_files)

    def __getitem__(self, keys):
        """Custom __getitem__ for numpy slicing access.

        Parameters
        ----------
        keys : tuple
            Tuple of indices to access. Can be 1, 2, or 3 indices.

        Returns
        -------
        np.ndarray
            The image slice.
        """

        if not isinstance(keys, tuple):
            keys = (keys,)
        if len(keys) > 3:
            raise IndexError(f"Cannot access this index. Shape is {self.shape}.")

        print(keys, self._image_index)

        image_index = self._image_index
        if len(keys) == 0:
            return self._image.squeeze()
        elif len(keys) < 2:
            # Need to grab all of the files
            new_files = self._files
            self._image_index = ()
        elif keys[2] != self._image_index:
            # load a new image
            new_files = self._files[keys[2]]
            if not isinstance(new_files, list):
                new_files = [new_files]
            self._image_index = keys[2]

        if image_index != self._image_index:
            self._image = np.zeros(
                (self._width, self._height, len(new_files)), dtype=np.uint16
            )
            for i, file in enumerate(new_files):
                with PIL.Image.open(file) as im:
                    self._image[..., i] = im

        if len(keys) == 1:
            return self._image[keys[0], ...].squeeze()

        return self._image[keys[0], keys[1], :].squeeze()
