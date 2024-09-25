# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard library imports
from typing import Optional, Union, List, Dict
import logging

# Third-party imports
import numpy.typing as npt

# Local application imports
from .metadata import Metadata

NGFF_VERSION = "0.4"

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class OMEZarrMetadata(Metadata):
    """Class to generate OME-Zarr metadata."""

    @property
    def _axes(self) -> Dict:
        """Return tczyx axes in navigate units.

        https://ngff.openmicroscopy.org/0.4/#axes-md

        Returns
        -------
        List
            A list of dictionaries containing the axis name, type, and unit.
        """
        axes = [
            {"name": "t", "type": "time", "unit": "second"},
            {"name": "c", "type": "channel"},
            {"name": "z", "type": "space", "unit": "micrometer"},
            {"name": "y", "type": "space", "unit": "micrometer"},
            {"name": "x", "type": "space", "unit": "micrometer"},
        ]

        return axes

    def _stage_positions_to_translation_transform(
        self, x: float, y: float, z: float, theta: float, f: Optional[float] = None
    ) -> List[float]:
        """Grab the translation from the stage.

        Ignore theta, focus for now.

        Parameters
        ----------
        x : float
            The x position of the stage (um).
        y : float
            The y position of the stage (um).
        z : float
            The z position of the stage (um).
        theta : float
            The theta position of the stage (deg).
        f : float
            The focus position of the stage (um).

        Returns
        -------
        List
            A translation for each axis.
        """

        # Set the transform positions
        xp, yp, zp = x, y, z

        # Allow additional axes (e.g. f) to couple onto existing axes (e.g. z)
        # if they are both moving along the same physical dimension
        if self._coupled_axes is not None:
            for leader, follower in self._coupled_axes.items():
                if leader.lower() not in "xyz":
                    print(
                        f"Unrecognized coupled axis {leader}. "
                        "Not gonna do anything with this."
                    )
                    continue
                elif leader.lower() == "x":
                    xp += float(locals()[f"{follower.lower()}"])
                elif leader.lower() == "y":
                    yp += float(locals()[f"{follower.lower()}"])
                elif leader.lower() == "z":
                    zp += float(locals()[f"{follower.lower()}"])

        # t, c, z, y, x
        return [0.0, 0.0, zp, yp, xp]

    def _scale_transform(
        self, subdiv: Union[npt.ArrayLike, List] = [1, 1, 1]
    ) -> List[float]:
        """Calculate the image scale after subdivision.

        Parameters
        ----------
        subdiv : List
            The subdivision of the dataset.

        Returns
        -------
        List
            The scale of the dataset.
        """
        return [
            self.dt,
            self.dc,
            self.dz * subdiv[2],
            self.dy * subdiv[1],
            self.dx * subdiv[0],
        ]

    def _coordinate_transformations(
        self, scale: Optional[List] = None, translation: Optional[List] = None
    ) -> Dict:
        """Package scale and translation in a dict.

        Parameters
        ----------
        scale : List
            The scale of the dataset.
        translation : List
            The translation of the dataset.

        Returns
        -------
        Dict
            A dictionary containing the transformation.
        """
        transformation = []
        if (
            scale is None
            or not isinstance(scale, list)
            or len(scale) != len(self._axes)
        ):
            if translation is not None:
                logger.error("Translation cannot be provided without scale.")
                raise UserWarning("Translation cannot be provided without scale.")
            return transformation
        else:
            transformation.append({"type": "scale", "scale": scale})

        if (
            translation is not None
            and isinstance(translation, list)
            and len(translation) == len(self._axes)
        ):
            transformation.append({"type": "translation", "translation": translation})

        return transformation

    def multiscales_dict(
        self,
        name: str,
        paths: list,
        resolutions: Union[npt.ArrayLike, List],
        view: Optional[Dict] = None,
    ) -> Dict:
        """Create a multiscale dictionary for the OME-Zarr metadata.

        https://ngff.openmicroscopy.org/0.4/index.html#multiscale-md

        Parameters
        ----------
        name : str
            The name of the dataset.
        paths : list
            The paths of the dataset.
        resolutions : List
            The resolutions of the dataset.
        view : Dict
            The view of the dataset.

        Returns
        -------
        Dict
            A dictionary containing the multiscale metadata.
        """
        d = {"version": NGFF_VERSION, "name": name, "axes": self._axes}

        datasets = []
        for path, res in zip(paths, resolutions):
            scale = self._scale_transform(res)
            dd = {
                "path": path,
                "coordinateTransformations": self._coordinate_transformations(scale),
            }
            datasets.append(dd)
        d["datasets"] = datasets

        if view is not None:
            scale = [1.0] * len(self._axes)
            translation = self._stage_positions_to_translation_transform(**view)
            d["coordinateTransformations"] = self._coordinate_transformations(
                scale, translation
            )

        return d
