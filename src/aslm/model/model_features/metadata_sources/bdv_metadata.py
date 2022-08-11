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
    def __init__(self) -> None:
        super().__init__()
        # self._views = []
        self.setups = range(self.shape_c*self.shape_z)

    def bdv_xml_dict(self, file_name: str, views: list) -> dict:
        # Header
        bdv_dict = {}
        bdv_dict['SpimData'] = {'version': 2.0}
        
        # File path
        bdv_dict['SpimData']['BasePath'] = {'type': 'relative', 'text': '.'}
        bdv_dict['SpimData']['SequenceDescription'] = {}
        bdv_dict['SpimData']['SequenceDescription']['ImageLoader'] = {'format': 'bdv.hdf5'}
        bdv_dict['SpimData']['SequenceDescription']['ImageLoader']['hdf5'] = {'type': 'relative', 'text': file_name}

        # Populate the views
        bdv_dict['SpimData']['SequenceDescription']['ViewSetups'] = []
        view_id = 0
        for _ in self.shape_c:
            for _ in self.shape_z:
                d = {'ViewSetup': {'id': {'text': view_id}, 'name': {'text': view_id}}}
                d['ViewSetup']['size'] = {'text': f"{self.shape_x} {self.shape_y} {self.shape_z}"}
                d['ViewSetup']['voxelSize'] = {'unit': {'text': 'um'}}
                d['ViewSetup']['voxelSize']['size'] = {'text': f"{self.dx} {self.dy} {self.dz}"}
                bdv_dict['SpimData']['SequenceDescription']['ViewSetups'].append(d)
                view_id += 1

        # Time
        bdv_dict['SpimData']['SequenceDescription']['Timepoints'] = {'type': 'range'}
        bdv_dict['SpimData']['SequenceDescription']['Timepoints']['first'] = {'text': 0}
        bdv_dict['SpimData']['SequenceDescription']['Timepoints']['last'] = {'text': self.shape_t}

        # View registrations
        bdv_dict['SpimData']['ViewRegistrations'] = []
        for t in self.shape_t:
            for c in self.shape_c:
                for z in self.shape_z:
                    view_id = c*self.shape_z+z
                    matrix_id = view_id + t*self.shape_c*self.shape_z
                    d = {'ViewRegistration' : {'timepoint': t, 'setup': view_id}}
                    d['ViewRegistration']['ViewTransform'] = {'type': 'affine'}
                    d['ViewRegistration']['ViewTransform']['affine'] = {'text': 
                        self.stage_positions_to_affine_matrix(**views[matrix_id])}
                    bdv_dict['SpimData']['ViewRegistrations'].append(d)

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
        """Parse a BigDataViewer XML file.
        
        TODO: Incomplete."""
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
