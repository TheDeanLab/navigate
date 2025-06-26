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
from typing import Optional, Union
import xml.etree.ElementTree as ET
import logging

# Third Party Imports
import numpy as np
import numpy.typing as npt

# Local imports
from .metadata import XMLMetadata
from navigate.tools.linear_algebra import affine_rotation, affine_shear

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class BigDataViewerMetadata(XMLMetadata):
    """Metadata for BigDataViewer files.

    Supports HDF5 (.h5), N5 (.n5), and TIFF filelists (.tif/.tiff) via
    the SPIM-reconstruction filelist loader (format="spimreconstruction.filelist").

    Note
    ----
    XML spec in section 2.3 of https://arxiv.org/abs/1412.0488.
    """

    def __init__(self) -> None:
        """Initialize the BigDataViewer metadata object."""
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
        bdv_configuration = configuration["experiment"].get("BDVParameters", None)

        if bdv_configuration is not None:

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
        """Create a BigDataViewer XML metadata dictionary from a list of views.

        Parameters
        ----------
        file_name : str or list of str
            For HDF5/N5, the path to the dataset file (.h5 or .n5).
            For TIFF, either a directory path containing .tif/.tiff files,
            or an explicit list of TIFF file paths.
        views : list of dict
            A list of dictionaries containing stage/transform metadata for each view.
        **kw
            Additional keyword arguments (not used directly).

        Returns
        -------
        dict
            Nested dictionary representing the BigDataViewer XML structure.
        """
        # Header
        bdv_dict = {
            "version": 0.2,
            "BasePath": {"type": "relative", "text": "."},
            "SequenceDescription": {},
        }
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

        else:
            # File type is assumed to be TIFF or TIF
            ext = "tif"
            """
               <ImageLoader format="spimreconstruction.filelist">
                  <ZGrouped>false</ZGrouped>
                  <files>
                    <FileMapping view_setup="0" timepoint="0" series="0" channel="0">
                      <file type="relative">Position0/CH00_000000.tiff</file>
                    </FileMapping>
                    ...
                    <FileMapping view_setup="11" timepoint="0" series="0" channel="0">
                      <file type="relative">Position11/CH00_000000.tiff</file>
                    </FileMapping>
                  </files>
                </ImageLoader>
            """
            # Iterate through FileMapping and populate the file paths
            file_mapping = []
            view_id = 0

            for c in range(self.shape_c):
                for pos in range(self.positions - 1):
                    file_mapping.append(
                        {
                            "view_setup": str(view_id),
                            "timepoint": "0",
                            "series": "0",
                            "channel": str(c),
                            "file": {
                                "type": "relative",
                                "text": f"Position{pos}/CH{c:02d}_000000.tiff",
                            },
                        }
                    )
                    view_id += 1

            loader = {
                "format": "spimreconstruction.filemap2",
                "ZGrouped": {"text": "false"},
                "files": {"FileMapping": file_mapping},
            }

            bdv_dict["SequenceDescription"]["ImageLoader"] = loader

        # Calculate shear and rotation transforms
        self.bdv_shear_transform()
        self.bdv_rotate_transform()

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

            for pos in range(self.positions - 1):
                d = {
                    "id": {"text": view_id},
                    "name": {"text": view_id},
                    "size": {"text": f"{self.shape_x} {self.shape_y} {self.shape_z}"},
                    "voxelSize": {
                        "unit": {"text": "um"},
                        "size": {"text": f"{self.dx} {self.dy} {self.dz}"},
                    },
                    "attributes": {
                        "illumination": {"text": "0"},
                        "channel": {"text": str(c)},
                        "tile": {"text": str(pos)},
                        "angle": {"text": "0"},
                    },
                }

                bdv_dict["SequenceDescription"]["ViewSetups"]["ViewSetup"].append(d)
                view_id += 1

        # Finish up the Tile Attributes outside the channels loop so we have
        # one per tile
        for pos in range(self.positions - 1):
            tile = {"id": {"text": str(pos)}, "name": {"text": str(pos)}}
            bdv_dict["SequenceDescription"]["ViewSetups"]["Attributes"][2][
                "Tile"
            ].append(tile)

        # Time
        bdv_dict["SequenceDescription"]["Timepoints"] = {"type": "range"}
        bdv_dict["SequenceDescription"]["Timepoints"]["first"] = {"text": 0}
        bdv_dict["SequenceDescription"]["Timepoints"]["last"] = {
            "text": self.shape_t - 1
        }
        bdv_dict["SequenceDescription"]["MissingViews"] = {}

        # View registrations
        bdv_dict["ViewRegistrations"] = {"ViewRegistration": []}
        for t in range(self.shape_t):
            for p in range(self.positions - 1):
                for c in range(self.shape_c):
                    view_id = c * self.positions + p
                    mat = np.zeros(shape=(3, 4), dtype=float)

                    if ext == "n5" or ext == "h5":
                        for z in range(self.shape_z):
                            matrix_id = (
                                z
                                + self.shape_z * c
                                + p * self.shape_c * self.shape_z
                                + t * self.shape_c * self.shape_z * self.positions
                            )

                            # Construct centroid of volume matrix
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

                    else:
                        # Tiff files.
                        for view in views:
                            mat += self.stage_positions_to_affine_matrix(**view)

                    view_transforms = [
                        {
                            "type": "affine",
                            "Name": {"text": "Translation to Regular Grid"},
                            "affine": {
                                "text": " ".join([f"{x:.6f}" for x in mat.ravel()])
                            },
                        }
                    ]

                    d = self.shear_and_rotate_transform(t, view_id, view_transforms)

                    bdv_dict["ViewRegistrations"]["ViewRegistration"].append(d)

        bdv_dict["Misc"] = {"Entry": {"Key": "Note", "text": self.misc}}

        return bdv_dict

    def shear_and_rotate_transform(self, t, view_id, view_transforms):
        if self.shear_data:
            view_transforms.append(
                {
                    "type": "affine",
                    "Name": "Shearing Transform",
                    "affine": {
                        "text": " ".join(
                            [f"{x:.6f}" for x in self.shear_transform.ravel()]
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
                            [f"{x:.6f}" for x in self.rotate_transform.ravel()]
                        )
                    },
                }
            )
        d = dict(timepoint=t, setup=view_id, ViewTransform=view_transforms)
        return d

    def stage_positions_to_affine_matrix(
        self, x: float, y: float, z: float, theta: float, f: Optional[float] = None
    ) -> npt.ArrayLike:
        """Convert stage positions to an affine matrix.

        Ignore theta, focus for now.

        Parameters
        ----------
        x : float
            The x position of the stage.
        y : float
            The y position of the stage.
        z : float
            The z position of the stage.
        theta : float
            The theta position of the stage.
        f : Optional[float]
            The focus position of the stage, by default None

        Returns
        -------
        npt.ArrayLike
            An affine matrix.
        """
        arr = np.eye(3, 4)

        # Set the transform positions
        xp, yp, zp = x / self.dx, y / self.dy, z / self.dz

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
                    xp += float(locals()[f"{follower.lower()}"]) / self.dx
                elif leader.lower() == "y":
                    yp += float(locals()[f"{follower.lower()}"]) / self.dy
                elif leader.lower() == "z":
                    zp += float(locals()[f"{follower.lower()}"]) / self.dz

        # Translation into pixels
        arr[:, 3] = [yp, xp, zp]

        # Rotation (theta pivots in the xz plane, about the y-axis)
        # sin_theta, cos_theta = np.sin(theta), np.cos(theta)
        # arr[0,0], arr[2,2] = cos_theta, cos_theta
        # arr[0,2], arr[2,0] = sin_theta, -sin_theta

        return arr

    def affine_matrix_to_stage_positions(self, mat: npt.ArrayLike) -> tuple:
        """
        Convert affine matrix back into stage positions.

        Ignore theta, focus for now.

        Parameters
        ----------
        mat : npt.ArrayLike
            An affine matrix.

        Returns
        -------
        tuple
            A tuple of stage positions.
        """
        y, x, z = mat[:, 3] * np.array([self.dy, self.dx, self.dz])
        theta, f = None, None

        return x, y, z, theta, f

    def bdv_shear_transform(self):
        """Calculate the shear transform matrix.

        BDV-specific. Matrix provided is not (4,4), but (3,4).
        """
        if self.shear_data:
            self.shear_transform = affine_shear(
                dz=self.dz,
                dx=self.dx,
                dy=self.dy,
                dimension=self.shear_dimension,
                angle=self.shear_angle,
            )[:3]
        else:
            self.shear_transform = np.eye(3, 4)

    def bdv_rotate_transform(self):
        """Calculate the BDV rotation transform matrix.

        BDV-specific. Matrix provided is not (4,4), but (3,4).
        """
        if self.rotate_data:
            self.rotate_transform = affine_rotation(
                x=self.rotate_angle_x, y=self.rotate_angle_y, z=self.rotate_angle_z
            )[:3]
        else:
            self.rotate_transform = np.eye(3, 4)

    def parse_xml(self, root: Union[str, ET.Element]) -> tuple:
        """Parse a BigDataViewer XML file into our metadata format.

        Parameters
        ----------
        root : str or xml.etree.ElementTree.Element
            Path to a BigDataViewer XML file or an ElementTree root element.

        Returns
        -------
        file_path : str or list of str
            HDF5/N5 dataset path, or list of TIFF file paths if using the
            SPIM-reconstruction filelist loader.
        setups : list of str
            View setup identifiers as strings.
        transforms : list of array-like
            List of affine transform matrices corresponding to each view.
        """

        # Open the file, if present
        if isinstance(root, str) and os.path.isfile(root):
            with open(root, "r") as fp:
                example = fp.read()
                root = ET.fromstring(example)

        if root.tag != "SpimData":
            logger.error(f"Unknown Format: {root.tag}.")
            raise NotImplementedError(f"Unknown format {root.tag} failed to load.")

        # Check if we are loading a BigDataViewer hdf5
        image_loader = root.find("SequenceDescription/ImageLoader")
        fmt = image_loader.attrib.get("format", "")
        if fmt in ("bdv.hdf5", "bdv.n5"):
            # HDF5 or N5 dataset loader
            tag = "hdf5" if fmt == "bdv.hdf5" else "n5"
            base_path = root.find("BasePath").text or "."
            file = root.find(f"SequenceDescription/ImageLoader/{tag}")
            file_path = os.path.join(base_path, file.text)
        elif fmt == "spimreconstruction.filelist":
            # SPIM-reconstruction TIFF filelist loader
            base = root.find("BasePath").text or "."
            files = []
            for fm in root.findall("SequenceDescription/ImageLoader/files/FileMapping"):
                fnode = fm.find("file")
                files.append(os.path.join(base, fnode.text))
            file_path = files
        else:
            logger.error(f"Unknown Format: {fmt}.")
            raise NotImplementedError(f"Unknown format {fmt} failed to load.")

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

        # Get number of positions, one per setup/channel
        self.positions = len(
            root.findall("SequenceDescription/ViewSetups/ViewSetup/attributes/tile")
        ) // len(channels)

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
        """Write BigDataViewer XML metadata.

        Parameters
        ----------
        file_name : str
            The file name of the file to be written.
        views : list
            A list of dictionaries containing metadata for each view.

        """

        return super().write_xml(
            file_name, file_type="bdv", root="SpimData", views=views
        )
