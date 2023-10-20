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

import os
from typing import Optional, Union

from .metadata import XMLMetadata
from aslm import __version__


class OMETIFFMetadata(XMLMetadata):
    """Metadata for OME-TIFF files. OME-XML spec at
    https://docs.openmicroscopy.org/ome-model/6.3.1/ome-xml/index.html."""

    def ome_tiff_xml_dict(
        self,
        c: int = 0,
        t: int = 0,
        file_name: Union[str, list, None] = None,
        uid: Union[str, list, None] = None,
        views: Optional[list] = None,
        **kw,
    ):
        """
        Generates dictionary with same heirarchical structure as OME-XML. Useful for
        OME-TIFF and OME-XML.

        Returns
        -------
        ome_dict
            OME TIFF metadata dictionary
        """
        ome_dict = {
            "Creator": f"ASLM,v{__version__},Dean Lab at UTSW",
            "xmlns": "http://www.openmicroscopy.org/Schemas/OME/2016-06",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.openmicroscopy.org/Schemas/OME/2016-06 "
            "http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd",
        }
        if uid is not None:
            # Assume uid is a list passed in the order of the channels
            if not isinstance(uid, list):
                uid = [uid]
            ome_dict["UUID"] = "urn:uuid:" + uid[c]
        idx = c + t * self.shape_c
        ome_dict["Image"] = {"ID": f"Image:{idx}"}
        if file_name is not None:
            # Assume file name is a list passed in the order of the channels
            if not isinstance(file_name, list):
                file_name = [file_name]
            ome_dict["Image"]["Name"] = os.path.basename(file_name[c])
        ome_dict["Image"]["Pixels"] = {"ID": f"Pixels:{idx}"}
        ome_dict["Image"]["Pixels"]["BigEndian"] = "false"
        ome_dict["Image"]["Pixels"]["Interleaved"] = "false"
        ome_dict["Image"]["Pixels"][
            "Type"
        ] = "uint16"  # Hardcoded from SharedNDArray call

        ome_dict["Image"]["Pixels"]["SizeX"] = self.shape_x
        ome_dict["Image"]["Pixels"]["SizeY"] = self.shape_y

        # The following two are commented since we split our TIFFs into one TIFF stack
        # per channel per time point
        ome_dict["Image"]["Pixels"]["SizeT"] = self.shape_t
        ome_dict["Image"]["Pixels"]["SizeC"] = self.shape_c

        ome_dict["Image"]["Pixels"]["DimensionOrder"] = "XYZCT"
        # z_steps = 1
        # if (
        #     self.configuration["experiment"]["MicroscopeState"]["image_mode"]
        #     == "z-stack"
        # ):
        #     z_steps = int(
        #         self.configuration["experiment"]["MicroscopeState"]["number_z_steps"]
        #     )
        #     ome_dict["Image"]["Pixels"]["PhysicalSizeZ"] = float(
        #         self.configuration["experiment"]["MicroscopeState"]["step_size"]
        #     )
        # elif (
        #     self.configuration["experiment"]["MicroscopeState"]["image_mode"]
        #     == "confocal-projection"
        # ):
        #     z_steps = int(
        #         self.configuration["experiment"]["MicroscopeState"]["n_plane"]
        #     )
        #     ome_dict["Image"]["Pixels"]["PhysicalSizeZ"] = (
        #         float(self.configuration["experiment"]["MicroscopeState"]["offset_end"])
        #         - float(
        #             self.configuration["experiment"]["MicroscopeState"]["offset_start"]
        #         )
        #     ) / (z_steps - 1)

        ome_dict["Image"]["Pixels"]["SizeZ"] = self.shape_z

        zoom = self.configuration["experiment"]["MicroscopeState"]["zoom"]
        pixel_size = float(
            self.configuration["configuration"]["microscopes"][self.active_microscope][
                "zoom"
            ]["pixel_size"][zoom]
        )
        (
            ome_dict["Image"]["Pixels"]["PhysicalSizeX"],
            ome_dict["Image"]["Pixels"]["PhysicalSizeY"],
        ) = (pixel_size, pixel_size)

        ome_dict["Image"]["Pixels"]["Channel"] = []
        for i in range(self.shape_c):
            d = {"ID": f"Channel:{idx}:{i}", "SamplesPerPixel": "1", "LightPath": {}}
            ome_dict["Image"]["Pixels"]["Channel"].append(d)

        if file_name is not None and uid is not None:
            ome_dict["Image"]["Pixels"]["TiffData"] = []
            if not isinstance(file_name, list):
                file_name = [file_name]
            if not isinstance(uid, list):
                uid = [uid]
            if len(file_name) == len(uid):
                # Assume file name is a list passed in the order of the channels
                for i, fn in enumerate(file_name):
                    d = {
                        "FirstC": str(i),
                        "FirstT": str(t),
                        "FirstZ": "0",
                        "IFD": "0",
                        "PlaneCount": str(self.shape_z),
                    }
                    d["UUID"] = {
                        "FileName": os.path.basename(fn),
                        "text": "urn:uuid:" + uid[i],
                    }
                    ome_dict["Image"]["Pixels"]["TiffData"].append(d)
            else:
                ome_dict["Image"]["Pixels"]["MetadataOnly"] = {}  # Required filler
        else:
            ome_dict["Image"]["Pixels"]["MetadataOnly"] = {}  # Required filler

        dt = float(
            self.configuration["experiment"]["MicroscopeState"]["timepoint_interval"]
        )
        ome_dict["Image"]["Pixels"]["TimeIncrement"] = dt

        # TODO: Populate plane positions in OME-XML
        if views is not None:
            ome_dict["Image"]["Pixels"]["Plane"] = []
            for i in range(self.shape_c):
                view_idx = i * self.shape_z
                d = {
                    "DeltaT": dt,
                    "TheT": "0",
                    "TheC": str(i),
                    "TheZ": "0",
                    "PositionX": views[view_idx]["x"],
                    "PositionY": views[view_idx]["y"],
                    "PositionZ": views[view_idx]["z"],
                }
                ome_dict["Image"]["Pixels"]["Plane"].append(d)

        return ome_dict

    def write_xml(
        self,
        file_name: str,
        file_type: str = "OME-TIFF",
        root: Optional[str] = "OME",
        **kw,
    ) -> None:
        return super().write_xml(file_name, file_type=file_type, root=root, **kw)

    def to_xml(
        self, file_type: str = "OME-TIFF", root: Optional[str] = "OME", **kw
    ) -> str:
        return super().to_xml(file_type, root=root, **kw)
