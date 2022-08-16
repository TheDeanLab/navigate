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

    def bdv_xml_dict(self, file_name: str, views: list) -> dict:
        # Header
        bdv_dict = {'version': 2.0}
        
        # File path
        bdv_dict['BasePath'] = {'type': 'relative', 'text': '.'}
        bdv_dict['SequenceDescription'] = {}
        bdv_dict['SequenceDescription']['ImageLoader'] = {'format': 'bdv.hdf5'}
        bdv_dict['SequenceDescription']['ImageLoader']['hdf5'] = {'type': 'relative', 'text': file_name}

        # Populate the views
        bdv_dict['SequenceDescription']['ViewSetups'] = {}
        bdv_dict['SequenceDescription']['ViewSetups']['ViewSetup'] = []
        view_id = 0
        for _ in range(self.shape_c):
            for _ in range(self.positions):
                d = {'id': {'text': view_id}, 'name': {'text': view_id}}
                d['size'] = {'text': f"{self.shape_x} {self.shape_y} {self.shape_z}"}
                d['voxelSize'] = {'unit': {'text': 'um'}}
                d['voxelSize']['size'] = {'text': f"{self.dx} {self.dy} {self.dz}"}
                bdv_dict['SequenceDescription']['ViewSetups']['ViewSetup'].append(d)
                view_id += 1

        # Time
        bdv_dict['SequenceDescription']['Timepoints'] = {'type': 'range'}
        bdv_dict['SequenceDescription']['Timepoints']['first'] = {'text': 0}
        bdv_dict['SequenceDescription']['Timepoints']['last'] = {'text': self.shape_t-1}

        # View registrations
        bdv_dict['ViewRegistrations'] = {'ViewRegistration': []}
        for t in range(self.shape_t):
            for p in range(self.positions):
                for c in range(self.shape_c):
                    view_id = c * self.positions + p
                    mat = np.zeros((3,4), dtype=float)
                    for z in range(self.shape_z):
                        matrix_id = z + self.shape_z*c + t*self.shape_c*self.shape_z*self.positions
                        # Construct centroid of volume matrix
                        mat += self.stage_positions_to_affine_matrix(**views[matrix_id])/self.shape_z
                    d = {'timepoint': t, 'setup': view_id}
                    d['ViewTransform'] = {'type': 'affine'}
                    d['ViewTransform']['affine'] = {'text':
                        ' '.join([f"{x:.6f}" for x in mat.ravel()])}
                    bdv_dict['ViewRegistrations']['ViewRegistration'].append(d)
        
        return bdv_dict

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

    def write_xml(self, file_name: str, views: list) -> None:
        return super().write_xml(file_name, file_type='bdv', root='SpimData', views=views)
