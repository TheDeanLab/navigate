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

    def __init__(self):
        """Initialize metadata object."""

        super().__init__()

        # Affine Transform Parameters
        #: bool: Shear the data.
        self.shear_data = False
        #: str: Dimension to shear the data.
        self.shear_dimension = "YZ"
        #: float: Angle in degrees to shear the data.
        self.shear_angle = 0
        #: npt.NDArray: Shear transform matrix.
        self.shear_transform = np.eye(3, 4)

        # Rotation Transform Parameters
        #: bool: Rotate the data.
        self.rotate_data = False
        #: float: Angle in degrees to rotate the data in X.
        self.rotate_angle_x = 0
        #: float: Angle in degrees to rotate the data in Y.
        self.rotate_angle_y = 0
        #: float: Angle in degrees to rotate the data in Z.
        self.rotate_angle_z = 0
        #: npt.NDArray: Rotation transform matrix.
        self.rotate_transform = np.eye(3, 4)

    def get_affine_parameters(self, configuration):
        """Get the affine transform parameters from the configuration file.

        Parameters
        ----------
        configuration : dict
            Configuration dictionary.
        """
        bdv_configuration = configuration["configuration"]["BDVParameters"]

        # Shear Parameters
        self.shear_data = bdv_configuration["shear"].get("shear_data", False)
        self.shear_dimension = (
            bdv_configuration["shear"].get("shear_dimension", "YZ").upper()
        )
        self.shear_angle = bdv_configuration["shear"].get("shear_angle", 0)

        # Rotate Parameters
        self.rotate_data = bdv_configuration["rotate"].get("rotate_data", False)
        self.rotate_angle_x = bdv_configuration["rotate"].get("X", 0)
        self.rotate_angle_y = bdv_configuration["rotate"].get("Y", 0)
        self.rotate_angle_z = bdv_configuration["rotate"].get("Z", 0)

    def bdv_xml_dict(
        self, file_name: Union[str, list, None], views: list, **kw
    ) -> dict:
        # Header
        bdv_dict = {"version": 0.2}

        # File path
        bdv_dict["BasePath"] = {"type": "relative", "text": "."}
        bdv_dict["SequenceDescription"] = {}

        ext = os.path.basename(file_name).split(".")[-1]
        if ext == "h5":
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

        # Calculate shear and rotation transforms
        self.calculate_shear_transform()
        self.calculate_rotate_transform()

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
        # Finish up the Tile Attributes outside of the channels loop so we have
        # one per tile
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

                        # Construct centroid of volume matrix
                        # print(matrix_id, views[matrix_id])
                        try:
                            mat += (
                                self.stage_positions_to_affine_matrix(
                                    **views[matrix_id]
                                )
                                / self.shape_z
                            )
                        except IndexError:
                            # We have most likely canceled in the middle of
                            # an acquisition.
                            pass

                    view_transforms = [
                        {
                            "type": "affine",
                            "Name": "Translation to Regular Grid",
                            "affine": {
                                "text": " ".join([f"{x:.6f}" for x in mat.ravel()])
                            },
                        }
                    ]

                    if self.shear_data:
                        view_transforms.append(
                            {
                                "type": "affine",
                                "Name": "Shearing Transform",
                                "affine": {
                                    "text": " ".join(
                                        [
                                            f"{x:.6f}"
                                            for x in self.shear_transform.ravel()
                                        ]
                                    )
                                },
                            }
                        )

                    if self.rotate_data:
                        view_transforms.append(
                            {
                                "type": "affine",
                                "Name": "Rotation Transform",
                                "affine": {
                                    "text": " ".join(
                                        [
                                            f"{x:.6f}"
                                            for x in self.rotate_transform.ravel()
                                        ]
                                    )
                                },
                            }
                        )

                    d = dict(timepoint=t, setup=view_id, ViewTransform=view_transforms)

                    bdv_dict["ViewRegistrations"]["ViewRegistration"].append(d)

        return bdv_dict

    def stage_positions_to_affine_matrix(
        self, x: float, y: float, z: float, theta: float, f: Optional[float] = None
    ) -> npt.ArrayLike:
        """Convert stage positions to an affine matrix. Ignore theta, focus for now."""
        arr = np.eye(3, 4)

        # Translation into pixels
        arr[:, 3] = [y / self.dy, x / self.dx, z / self.dz]

        # Rotation (theta pivots in the xz plane, about the y axis)
        # sin_theta, cos_theta = np.sin(theta), np.cos(theta)
        # arr[0,0], arr[2,2] = cos_theta, cos_theta
        # arr[0,2], arr[2,0] = sin_theta, -sin_theta

        return arr

    def affine_matrix_to_stage_positions(self, mat: npt.ArrayLike) -> tuple:
        """
        Convert affine matrix back into stage positions. Ignore theta, focus for now.
        """
        y, x, z = mat[:, 3] * np.array([self.dy, self.dx, self.dz])
        theta, f = None, None

        return x, y, z, theta, f

    def calculate_shear_transform(self):
        """Calculate the shear transform matrix.

        Affine Transform for shear has the following form:

        [1 hxy hxz, 0,
        hyx 1 hyz, 0,
        hzx hzy 1, 0]
        """
        if self.shear_data:
            scaled_angle = np.multiply(
                np.cos(np.deg2rad(self.shear_angle)),
                [self.dy / self.dx, self.dz / self.dx, self.dz / self.dy],
            )

            if self.shear_dimension == "XY" or self.shear_dimension == "YX":
                self.shear_transform[0, 1] = scaled_angle[0]
            elif self.shear_dimension == "XZ" or self.shear_dimension == "ZX":
                self.shear_transform[0, 2] = scaled_angle[1]
            elif self.shear_dimension == "YZ" or self.shear_dimension == "ZY":
                self.shear_transform[1, 2] = scaled_angle[2]
            else:
                pass

    def calculate_rotate_transform(self):
        """Calculate the rotation transform matrix.

        Affine transform for rotation has the following forms.

        Rotation about x:
        [1, 0, 0, 0,
        0, cos(theta), -sin(theta), 0,
        0, sin(theta), cos(theta), 0]

        Rotation about Y:
        [cos(theta), 0, sin(theta), 0,
        0, 1, 0, 0,
        -sin(theta), 0, cos(theta), 0,

        Rotation about Z:
        [cos(theta), -sin(theta), 0, 0,
        sin(theta), cos(theta), 0, 0,
        0, 0, 1, 0]
        """
        if self.rotate_data:
            if self.rotate_angle_x != 0:
                cosine_theta = np.cos(np.deg2rad(self.rotate_angle_x))
                sin_theta = np.sin(np.deg2rad(self.rotate_angle_x))
                x_transform = np.eye(3, 4)
                x_transform[1, 1] = cosine_theta
                x_transform[1, 2] = -sin_theta
                x_transform[2, 1] = sin_theta
                x_transform[2, 2] = cosine_theta
            else:
                x_transform = None

            if self.rotate_angle_y != 0:
                cosine_theta = np.cos(np.deg2rad(self.rotate_angle_y))
                sin_theta = np.sin(np.deg2rad(self.rotate_angle_y))
                y_transform = np.eye(3, 4)
                y_transform[0, 0] = cosine_theta
                y_transform[0, 2] = sin_theta
                y_transform[2, 0] = -sin_theta
                y_transform[2, 2] = cosine_theta
            else:
                y_transform = None

            if self.rotate_angle_z != 0:
                cosine_theta = np.cos(np.deg2rad(self.rotate_angle_z))
                sin_theta = np.sin(np.deg2rad(self.rotate_angle_z))
                z_transform = np.eye(3, 4)
                z_transform[0, 0] = cosine_theta
                z_transform[0, 1] = -sin_theta
                z_transform[1, 0] = sin_theta
                z_transform[1, 1] = cosine_theta
            else:
                z_transform = None

            matrices = [x_transform, y_transform, z_transform]
            matrices = [x for x in matrices if x is not None]
            if len(matrices) == 0:
                # self.rotate_data = True, but all angles are 0
                self.rotate_transform = np.eye(3, 4)
            if len(matrices) == 1:
                # self.rotate_data = True, but one angle is non-zero
                self.rotate_transform = matrices[0]
            elif len(matrices) == 2:
                # self.rotate_data = True, but two angles are non-zero
                self.rotate_transform = np.matmul(matrices[0].T, matrices[1])[:3]
            else:
                # self.rotate_data = True, and all angles are non-zero
                self.rotate_transform = np.matmul(matrices[0].T, matrices[1])[:3]
                self.rotate_transform = np.matmul(self.rotate_transform.T, matrices[2])[
                    :3
                ]
        else:
            # self.rotate_data is False
            self.rotate_transform = np.eye(3, 4)

    def parse_xml(self, root: Union[str, ET.Element]) -> tuple:
        """Parse a BigDataViewer XML file into our metadata format."""

        # Open the file, if present
        if isinstance(root, str) and os.path.isfile(root):
            with open(root, "r") as fp:
                example = fp.read()
                root = ET.fromstring(example)

        if root.tag != "SpimData":
            raise NotImplementedError(f"Unknown format {root.tag} failed to load.")

        # Check if we are loading a BigDataViewer hdf5
        image_loader = root.find("SequenceDescription/ImageLoader")
        if image_loader.attrib["format"] not in ["bdv.hdf5", "bdv.n5"]:
            raise NotImplementedError(
                f"Unknown format {image_loader.attrib['format']} failed to load."
            )

        # Parse the file path
        base_path = root.find("BasePath")
        file = root.find("SequenceDescription/ImageLoader/hdf5")
        file_path = os.path.join(base_path.text, file.text)

        # Get setups. Each setup represents a visualisation data source in the viewer
        # that provides one image volume per timepoint
        setups = [
            x.text for x in root.findall("SequenceDescription/ViewSetups/ViewSetup/id")
        ]

        # Get channels, one per setup
        channels = list(
            set(
                [
                    x.text
                    for x in root.findall(
                        "SequenceDescription/ViewSetups/ViewSetup/attributes/channel"
                    )
                ]
            )
        )

        # Get number of positions, one per setup
        self.positions = len(
            root.findall("SequenceDescription/ViewSetups/ViewSetup/attributes/tile")
        )

        # Get image sizes in (x, y, z), one per setup
        sizes = [
            [int(y) for y in x.text.split()]
            for x in root.findall("SequenceDescription/ViewSetups/ViewSetup/size")
        ]

        # Get image voxel sizes (dx, dy, dz), one per setup
        voxel_sizes = [
            [float(y) for y in x.text.split()]
            for x in root.findall(
                "SequenceDescription/ViewSetups/ViewSetup/voxelSize/size"
            )
        ]

        # Get timepoints
        timepoint_type = root.find("SequenceDescription/Timepoints").attrib["type"]
        if timepoint_type != "range":
            raise NotImplementedError(
                f"Unknown format {timepoint_type} failed to load."
            )
        t_start = int(root.find("SequenceDescription/Timepoints/first").text)
        t_stop = int(root.find("SequenceDescription/Timepoints/last").text)
        timepoints = (t_start, t_stop + 1)

        # Get affine transformations, one per setup
        tt, ts = np.array(
            [
                [int(x.attrib["timepoint"]), int(x.attrib["setup"])]
                for x in root.findall("ViewRegistrations/ViewRegistration")
            ]
        ).T
        transforms = [
            np.array(x.text.split(), dtype=float).reshape(-1, 4)
            for x in root.findall(
                "ViewRegistrations/ViewRegistration/ViewTransform/affine"
            )
        ]

        # Set up metadata parameters
        self.dx, self.dy, self.dz = np.array(voxel_sizes).min(
            0
        )  # default to finest sampling
        self._multiposition = self.positions > 1
        self.shape_x, self.shape_y, self.shape_z = np.array(sizes).max(
            0
        )  # default to largest size captured
        self.shape_c = len(channels)
        self.shape_t = timepoints[1] - timepoints[0]

        return file_path, setups, transforms

    def write_xml(self, file_name: str, views: list) -> None:
        return super().write_xml(
            file_name, file_type="bdv", root="SpimData", views=views
        )
