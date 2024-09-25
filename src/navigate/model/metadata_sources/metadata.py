# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

#  Standard Imports
import os
import logging
from typing import Optional

# Local Imports
from navigate.tools import xml_tools
from navigate import __version__, __commit__

from multiprocessing.managers import DictProxy

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Metadata:
    def __init__(self) -> None:
        """Metadata class

        Store and convert internal representation of metadata (configuration,
        experiment, etc.) to alternative file types.

        Note
        ----
            Concept and some of the code borrowed from python-microscopy
            (https://github.com/python-microscopy/python-microscopy/).
        """
        #: dict: Configuration dictionary
        self._configuration = None

        #: float: Pixel size in x (um)
        #: float: Pixel size in y (um)
        #: float: Pixel size in z (um)
        self.dx, self.dy, self.dz = 1, 1, 1  # pixel sizes (um)

        #: float: Time displacement (s)
        self.dt = 1

        #: int: Step size between channels, should always be 1
        self.dc = 1

        self._order = "XYCZT"
        self._per_stack = True
        self._multiposition = False
        self._coupled_axes = None

        #: int: Shape of the data in x
        #: int: Shape of the data in y
        #: int: Shape of the data in z
        #: int: Shape of the data in t
        #: int: Shape of the data in c
        self.shape_x, self.shape_y, self.shape_z, self.shape_t, self.shape_c = (
            1,
            1,
            1,
            1,
            1,
        )

        #: int: Number of positions
        self.positions = 1

        #: str: Active microscope
        self.active_microscope = None

    @property
    def configuration(self) -> Optional[DictProxy]:
        """Return configuration dictionary

        Returns
        -------
        Optional[DictProxy]
            Configuration dictionary
        """
        return self._configuration

    @configuration.setter
    def configuration(self, configuration: DictProxy) -> None:
        """Set configuration dictionary

        Parameters
        ----------
        configuration : DictProxy
            Configuration dictionary
        """
        self._configuration = configuration
        self.set_from_configuration_experiment()

    @property
    def per_stack(self) -> bool:
        """Return per stack

        Returns
        -------
        bool
            True if per stack, False otherwise
        """
        return self._per_stack

    def set_from_dict(self, metadata_config: dict) -> None:
        """Set from a dictionary

        Parameters
        ----------
        metadata_config : dict
            dictionary of metadata: "c", "z", "t", "p", "is_dynamic", "per_stack"
        """
        self.shape_c = metadata_config.get("c", self.shape_c)
        self.shape_z = metadata_config.get("z", self.shape_z)
        self.shape_t = metadata_config.get("t", self.shape_t)
        self.positions = metadata_config.get("p", self.positions)
        if metadata_config.get("is_dynamic", False):
            self._multiposition = True
        self._per_stack = metadata_config.get("per_stack", self._per_stack)

    def set_from_configuration_experiment(self) -> None:
        """Set from configuration experiment"""
        if (
            self.configuration.get("experiment") is not None
            and self.configuration.get("configuration") is not None
        ):
            if self.active_microscope is None:
                self.active_microscope = self.configuration["experiment"][
                    "MicroscopeState"
                ]["microscope_name"]
            self.set_shape_from_configuration_experiment()
            self.set_stack_order_from_configuration_experiment()

    def set_shape_from_configuration_experiment(self) -> None:
        """Set shape from configuration experiment"""
        state = self.configuration["experiment"]["MicroscopeState"]
        scope = self.configuration["configuration"]["microscopes"][
            self.active_microscope
        ]
        zoom = state["zoom"]
        pixel_size = float(scope["zoom"]["pixel_size"].get(zoom, 1))
        self.dx, self.dy = pixel_size, pixel_size
        self.dz = float(abs(state["step_size"]))
        self.dt = float(state["timepoint_interval"])

        # TODO: do we need to update the XML meta data accordingly?
        self.shape_x = int(
            self.configuration["experiment"]["CameraParameters"][
                self.active_microscope
            ]["img_x_pixels"]
        )
        self.shape_y = int(
            self.configuration["experiment"]["CameraParameters"][
                self.active_microscope
            ]["img_y_pixels"]
        )
        if (state["image_mode"] == "z-stack") or (state["image_mode"] == "customized"):
            self.shape_z = int(state["number_z_steps"])
        else:
            self.shape_z = 1
        self.shape_t = int(state["timepoints"])
        self.shape_c = sum(
            [v["is_selected"] is True for k, v in state["channels"].items()]
        )

        self._multiposition = state["is_multiposition"]

        if bool(self._multiposition):
            self.positions = len(self.configuration["experiment"]["MultiPositions"])
        else:
            self.positions = 1

        # tiff
        if state["image_mode"] == "customized":
            self._multiposition = True
        # let the data sources have the ability to save more frames
        # self._multiposition = True
        # self.positions = len(
        #     self.configuration["experiment"]["MultiPositions"]
        # )

        # Allow additional axes (e.g. f) to couple onto existing axes (e.g. z)
        # if they are both moving along the same physical dimension
        self._coupled_axes = scope["stage"].get("coupled_axes", None)

        # print(f"Coupled axes: {self._coupled_axes} {type(self._coupled_axes)}")

        # safety
        assert (self._coupled_axes is None) or isinstance(self._coupled_axes, DictProxy)

        # If we have additional axes, create self.d{axis} for each
        # additional axis, to ensure we keep track of the step size
        if self._coupled_axes is not None:
            for leader, follower in self._coupled_axes.items():
                # print(leader, follower)
                assert leader.lower() in "xyzct"  # safety
                if getattr(self, f"d{follower.lower()}", None) is None:
                    # print(state.get(f"{follower.lower()}_step_size", 1))
                    setattr(
                        self,
                        f"d{follower.lower()}",
                        state.get(f"{follower.lower()}_step_size", 1),
                    )

    def set_stack_order_from_configuration_experiment(self) -> None:
        """Set stack order from configuration experiment"""
        state = self.configuration["experiment"]["MicroscopeState"]
        self._per_stack = (
            state["stack_cycling_mode"] == "per_stack"
            and state["image_mode"] != "single"
        )

    @property
    def voxel_size(self) -> tuple:
        """Return voxel size

        Returns
        -------
        tuple
            Voxel size
        """
        return (self.dx, self.dy, self.dz)

    @property
    def shape(self) -> tuple:
        """Return shape as XYCZT.

        Returns
        -------
        tuple
            Shape as XYCZT
        """
        return (self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t)


class XMLMetadata(Metadata):
    """XML Metadata

    This is a base class for dealing with metadata that is stored as an XML, e.g. in
    OME-TIFF or BigDataViewer. There are multiple methods for storing XML. In OME-TIFF,
    the XML is stored in the header of the first OME-TIFF file in a directory. In
    BigDataViewer, it is stored in a separate XML. Both have proprietary XML formats. To
    address this, we store their metadata in a nested dictionary, defined by
    {file_type}_xml_dict() (e.g. ome_tiff_xml_dict()) (see to_xml()). We then parse this
    nested dictionary into an XML file. Similarly, we can parse from an XML file to a
    nested dictionary and map these values back to our internal representation of
    metadata values (TODO: Not implemented. Will use xml_tools.parse_xml() for the
    first bit.)
    """

    def write_xml(
        self, file_name: str, file_type: str, root: Optional[str] = None, **kw
    ) -> None:
        """Write to XML file. Assumes we do not include the XML header in our nested
        metadata dictionary.

        Parameters
        ----------
        file_name : str
            File name
        file_type : str
            File type
        root : Optional[str], optional
            Root, by default None
        """
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'  # XML file header
        xml += (
            f"<!-- Created by Navigate, "
            f"v{__version__}, "
            f"Commit {__commit__}, Dean Lab at UTSW -->\n"
        )
        # TODO: should os.path.basename be the default? Added this for BigDataViewer's
        # relative path.
        xml += self.to_xml(file_type, root, file_name=os.path.basename(file_name), **kw)
        file_name = os.path.splitext(file_name)[0] + ".xml"
        with open(file_name, "w") as fp:
            fp.write(xml)

    def to_xml(self, file_type: str, root: Optional[str] = None, **kw) -> str:
        """
        Convert stored metadata to XML

        Parameters
        ----------
        file_type : str
            File type
        root : Optional[str], optional
            Root, by default None
        **kw
            Keyword arguments

        Returns
        -------
        str
            XML string
        """
        xml = ""
        try:
            d = getattr(
                self, f"{file_type.lower().replace(' ','_').replace('-','_')}_xml_dict"
            )(**kw)
            xml = xml_tools.dict_to_xml(d, root)
        except AttributeError:
            logging.debug(
                f"Metadata Writer - I do not know how to export {file_type} "
                f"metadata to XML."
            )
        return xml
