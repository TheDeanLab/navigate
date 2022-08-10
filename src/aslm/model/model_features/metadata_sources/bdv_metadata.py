#  Standard Imports
import os
from typing import Optional
import xml.etree.ElementTree as ET

# Third Party Imports
import numpy as np
import numpy.typing as npt

# Local imports
from .metadata import XMLMetadata

class BigDataViewerMetadata(XMLMetadata):
    
    def stage_positions_to_affine_matrix(self, x: float, y: float, z: float, 
                                         theta: float, f: Optional[float] = None) -> npt.ArrayLike:
        """Convert stage positions to an affine matrix. Ignore focus for now."""
        arr = np.eye(3,4)

        # Translation 
        arr[:,3] = [x,y,z]

        # Rotation (theta pivots in the xz plane, about the y axis)
        sin_theta, cos_theta = np.sin(theta), np.cos(theta)
        arr[0,0], arr[2,2] = cos_theta, cos_theta
        arr[0,2], arr[2,0] = sin_theta, -sin_theta

        return arr
    
    def parse_bdv_xml(root: ET.Element) -> tuple:
        """Parse a BigDataViewer XML file."""
        if root.tag != 'SpimData':
            raise NotImplementedError(f"Unknown format {root.tag} failed to load.")

        # Check if we are loading a BigDataViewer hdf5
        image_loader = root.find('SequenceDescription/ImageLoader')
        if image_loader.attrib['format'] != 'bdv.hdf5':
            raise NotImplementedError(f"Unknown format {image_loader.attrib['format']} failed to load.")

        # Parse the file path
        base_path = root.find('BasePath')
        file = root.find('SequenceDescription/ImageLoader/hdf5')
        file_path = file.text
        if file.attrib['type'] == 'relative':
            file_path = os.path.join(base_path.text, file_path)
            if base_path.attrib['type'] == 'relative':
                file_path = os.path.join(os.getcwd(), file_path)

        # Get setups. Each setup represents a visualisation data source in the viewer that 
        # provides one image volume per timepoint
        setups = [x.text for x in root.findall('SequenceDescription/ViewSetups/ViewSetup/id')]

        # Get timepoints
        timepoint_type = root.find('SequenceDescription/Timepoints').attrib['type']
        if timepoint_type != 'range':
            raise NotImplementedError(f"Unknown format {timepoint_type} failed to load.")
        t_start = int(root.find('SequenceDescription/Timepoints/first').text)
        t_stop = int(root.find('SequenceDescription/Timepoints/last').text)
        timepoints = range(t_start, t_stop+1)
        
        return file_path, setups, timepoints