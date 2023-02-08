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

#  Standard Imports
import os
from typing import Optional, Union
import xml.etree.ElementTree as ET

# Third Party Imports
import numpy as np
import numpy.typing as npt

# Local imports
from .metadata import XMLMetadata


class BigDataViewerMetadata(XMLMetadata):
    """Metadata for BigDataViewer files. XML spec in section 2.3 of
    https://arxiv.org/abs/1412.0488."""

    def __init__(self) -> None:
        super().__init__()

    def bdv_xml_dict(
        self, file_name: Union[str, list, None], views: list, **kw
    ) -> dict:
        # Header
        bdv_dict = {"version": 0.2}

        # File path
        bdv_dict["BasePath"] = {"type": "relative", "text": "."}
        bdv_dict["SequenceDescription"] = {}

        ext = os.path.basename(file_name).split(".")[-1]
        if ext == "hdf":
            """
            <ImageLoader format="bdv.hdf5">
                <hdf5 type="relative">dataset.h5</hdf5>
            </ImageLoader>
            """
            bdv_dict["SequenceDescription"]["ImageLoader"] = {"format": "bdv.hdf5"}
            bdv_dict["SequenceDescription"]["ImageLoader"]["hdf5"] = {
                "type": "relative",
                "text": file_name,
            }

        elif ext == "tiff" or ext == "tif":
            """
            Need to iterate through the time points, etc.
            <ImageLoader format="spimreconstruction.filelist">
                <imglib2container>ArrayImgFactory</imglib2container>
                <ZGrouped>false</ZGrouped>
                <files>
                    <FileMapping view_setup="0" timepoint="0" series="0" channel="0">
                        <file type="relative">1_CH00_000000.tif</file>
                    </FileMapping>
                    <FileMapping view_setup="1" timepoint="0" series="0" channel="0">
                        <file type="relative">1_CH01_000000.tif</file>
                    </FileMapping>
                </files>
            </ImageLoader>
            """
            pass

        elif ext == "n5":
            """
            <ImageLoader format="bdv.n5" version="1.0">
                <n5 type="relative">dataset.n5</n5>
            </ImageLoader>
            """
            bdv_dict["SequenceDescription"]["ImageLoader"] = {"format": "bdv.n5"}
            bdv_dict["SequenceDescription"]["ImageLoader"]["n5"] = {
                "type": "relative",
                "text": file_name,
            }

        # Populate ViewSetups
        bdv_dict["SequenceDescription"]["ViewSetups"] = {}
        bdv_dict["SequenceDescription"]["ViewSetups"]["ViewSetup"] = []
        # Attributes are necessary for BigStitcher
        bdv_dict["SequenceDescription"]["ViewSetups"]["Attributes"] = [
            {
                "name": "illumination",
                "Illumination": {"id": {"text": 0}, "name": {"text": 0}},
            },
            {"name": "channel", "Channel": []},
            {"name": "tile", "Tile": []},
            {"name": "angle", "Angle": {"id": {"text": 0}, "name": {"text": 0}}},
        ]
        # The actual loop that populates ViewSetup
        view_id = 0
        for c in range(self.shape_c):
            # We also take care of the Channel attributes here
            ch = {"id": {"text": str(c)}, "name": {"text": str(c)}}
            bdv_dict["SequenceDescription"]["ViewSetups"]["Attributes"][1][
                "Channel"
            ].append(ch)
            for p in range(self.positions):
                d = {"id": {"text": view_id}, "name": {"text": view_id}}
                d["size"] = {"text": f"{self.shape_x} {self.shape_y} {self.shape_z}"}
                d["voxelSize"] = {"unit": {"text": "um"}}
                d["voxelSize"]["size"] = {"text": f"{self.dx} {self.dy} {self.dz}"}
                # These attributes are necessary for BigStitcher
                d["attributes"] = {
                    "illumination": {"text": "0"},
                    "channel": {"text": str(c)},
                    "tile": {"text": str(p)},
                    "angle": {"text": "0"},
                }
                bdv_dict["SequenceDescription"]["ViewSetups"]["ViewSetup"].append(d)
                view_id += 1
        # Finish up the Tile Attributes outside of the channels loop so we have one
        # per tile
        for p in range(self.positions):
            tile = {"id": {"text": str(p)}, "name": {"text": str(p)}}
            bdv_dict["SequenceDescription"]["ViewSetups"]["Attributes"][2][
                "Tile"
            ].append(tile)

        # Time
        bdv_dict["SequenceDescription"]["Timepoints"] = {"type": "range"}
        bdv_dict["SequenceDescription"]["Timepoints"]["first"] = {"text": 0}
        bdv_dict["SequenceDescription"]["Timepoints"]["last"] = {
            "text": self.shape_t - 1
        }

        # View registrations
        bdv_dict["ViewRegistrations"] = {"ViewRegistration": []}
        for t in range(self.shape_t):
            for p in range(self.positions):
                for c in range(self.shape_c):
                    view_id = c * self.positions + p
                    mat = np.zeros((3, 4), dtype=float)
                    for z in range(self.shape_z):
                        matrix_id = (
                            z
                            + self.shape_z * c
                            + p * self.shape_c * self.shape_z
                            + t * self.shape_c * self.shape_z * self.positions
                        )

                        try:
                            # Construct centroid of volume matrix
                            # print(matrix_id, views[matrix_id])
                            mat += (
                                self.stage_positions_to_affine_matrix(
                                    **views[matrix_id]
                                )
                                / self.shape_z
                            )
                        except IndexError:
                            raise IndexError(
                                f"matrix_id {matrix_id} for cztp {c} {z} "
                                f"{t} {p} is outside the range {len(views)}"
                            )

                    d = {"timepoint": t, "setup": view_id}
                    d["ViewTransform"] = {"type": "affine"}
                    d["ViewTransform"]["affine"] = {
                        "text": " ".join([f"{x:.6f}" for x in mat.ravel()])
                    }
                    bdv_dict["ViewRegistrations"]["ViewRegistration"].append(d)

        return bdv_dict

    def stage_positions_to_affine_matrix(
        self, x: float, y: float, z: float, theta: float, f: Optional[float] = None
    ) -> npt.ArrayLike:
        """Convert stage positions to an affine matrix. Ignore focus for now."""
        arr = np.eye(3, 4)

        # Translation
        arr[:, 3] = [x, y, z]

        # Rotation (theta pivots in the xz plane, about the y axis)
        # sin_theta, cos_theta = np.sin(theta), np.cos(theta)
        # arr[0,0], arr[2,2] = cos_theta, cos_theta
        # arr[0,2], arr[2,0] = sin_theta, -sin_theta

        return arr

    def parse_bdv_xml(root: ET.Element) -> tuple:
        """Parse a BigDataViewer XML file.

        TODO: Incomplete."""
        if root.tag != "SpimData":
            raise NotImplementedError(f"Unknown format {root.tag} failed to load.")

        # Check if we are loading a BigDataViewer hdf5
        image_loader = root.find("SequenceDescription/ImageLoader")
        if image_loader.attrib["format"] != "bdv.hdf5":
            raise NotImplementedError(
                f"Unknown format {image_loader.attrib['format']} failed to load."
            )

        # Parse the file path
        base_path = root.find("BasePath")
        file = root.find("SequenceDescription/ImageLoader/hdf5")
        file_path = file.text
        if file.attrib["type"] == "relative":
            file_path = os.path.join(base_path.text, file_path)
            if base_path.attrib["type"] == "relative":
                file_path = os.path.join(os.getcwd(), file_path)

        # Get setups. Each setup represents a visualisation data source in the viewer
        # that provides one image volume per timepoint
        setups = [
            x.text for x in root.findall("SequenceDescription/ViewSetups/ViewSetup/id")
        ]

        # Get timepoints
        timepoint_type = root.find("SequenceDescription/Timepoints").attrib["type"]
        if timepoint_type != "range":
            raise NotImplementedError(
                f"Unknown format {timepoint_type} failed to load."
            )
        t_start = int(root.find("SequenceDescription/Timepoints/first").text)
        t_stop = int(root.find("SequenceDescription/Timepoints/last").text)
        timepoints = range(t_start, t_stop + 1)

        return file_path, setups, timepoints

    def write_xml(self, file_name: str, views: list) -> None:
        return super().write_xml(
            file_name, file_type="bdv", root="SpimData", views=views
        )
