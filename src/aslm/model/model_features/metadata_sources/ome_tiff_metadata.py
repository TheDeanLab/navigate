import os
from typing import Optional, Union

from .metadata import XMLMetadata


class OMETIFFMetadata(XMLMetadata):

    def ome_tiff_xml_dict(self, c: int = 0, t: int = 0, file_name: Union[str, list, None] = None,
                          uid: Union[str, list, None] = None, views: Optional[list] = None, **kw):
        """
        Generates dictionary with same heirarchical structure as OME-XML. Useful for
        OME-TIFF and OME-XML.

        Returns
        -------
        ome_dict
            OME TIFF metadata dictionary
        """
        ome_dict = {'Creator': 'ASLM,DeanLab,v0.0.1',
                    'xmlns': "http://www.openmicroscopy.org/Schemas/OME/2016-06",
                    'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                    'xsi:schemaLocation': "http://www.openmicroscopy.org/Schemas/OME/2016-06 "
                                          "http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd"}
        if uid is not None:
            # Assume uid is a list passed in the order of the channels
            if type(uid) != list:
                uid = [uid]
            ome_dict['UUID'] = 'urn:uuid:'+uid[c]
        idx = c+t*self.shape_c
        ome_dict['Image'] = {'ID': f'Image:{idx}'}
        if file_name is not None:
            # Assume file name is a list passed in the order of the channels
            if type(file_name) != list:
                file_name = [file_name]
            ome_dict['Image']['Name'] = os.path.basename(file_name[c])
        ome_dict['Image']['Pixels'] = {'ID': f'Pixels:{idx}'}
        ome_dict['Image']['Pixels']['BigEndian'] = 'false'
        ome_dict['Image']['Pixels']['Interleaved'] = 'false'
        ome_dict['Image']['Pixels']['Type'] = 'uint16'  # Hardcoded from SharedNDArray call

        ome_dict['Image']['Pixels']['SizeX'] = int(self.experiment.CameraParameters['x_pixels'])
        ome_dict['Image']['Pixels']['SizeY'] = int(self.experiment.CameraParameters['y_pixels'])
        
        # The following two are commented since we split our TIFFs into one TIFF stack per
        # channel per time point
        ome_dict['Image']['Pixels']['SizeT'] = int(self.experiment.MicroscopeState['timepoints'])
        ome_dict['Image']['Pixels']['SizeC'] = len(self.experiment.MicroscopeState['channels'])

        ome_dict['Image']['Pixels']['DimensionOrder'] = 'XYZCT'
        z_steps = 1
        if self.experiment.MicroscopeState['image_mode'] == 'z-stack':
            z_steps = int(self.experiment.MicroscopeState['number_z_steps'])
            ome_dict['Image']['Pixels']['PhysicalSizeZ'] = float(self.experiment.MicroscopeState['step_size'])

        ome_dict['Image']['Pixels']['SizeZ'] = z_steps

        # This section contains duplicated code b/c in the instance resolution mode != high or low, we
        # do not want to include this information
        if self.experiment.MicroscopeState['resolution_mode'] == 'low':
            pixel_size = float(self.configuration.ZoomParameters['low_res_zoom_pixel_size'][self.experiment.MicroscopeState['zoom']])
            ome_dict['Image']['Pixels']['PhysicalSizeX'], ome_dict['Image']['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size
        elif self.experiment.MicroscopeState['resolution_mode'] == 'high':
            pixel_size = float(self.configuration.ZoomParameters['high_res_zoom_pixel_size'])
            ome_dict['Image']['Pixels']['PhysicalSizeX'], ome_dict['Image']['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size

        ome_dict['Image']['Pixels']['Channel'] = []
        for i in range(self.shape_c):
            d = {'ID': f'Channel:{idx}:{i}', 'SamplesPerPixel': '1', 'LightPath': {}}
            ome_dict['Image']['Pixels']['Channel'].append(d)

        if file_name is not None and uid is not None:
            ome_dict['Image']['Pixels']['TiffData'] = []
            if type(file_name) != list:
                file_name = [file_name]
            if type(uid) != list:
                uid = [uid]
            if len(file_name) == len(uid):
                # Assume file name is a list passed in the order of the channels
                for i, fn in enumerate(file_name):
                    d = {"FirstC": str(i), "FirstT": str(t), "FirstZ": "0", "IFD": "0", "PlaneCount": str(z_steps)}
                    d['UUID'] = {'FileName': os.path.basename(fn), 'text': 'urn:uuid:'+uid[i]}
                    ome_dict['Image']['Pixels']['TiffData'].append(d)
            else:
                ome_dict['Image']['Pixels']['MetadataOnly'] = {}  # Required filler
        else:
            ome_dict['Image']['Pixels']['MetadataOnly'] = {}  # Required filler

        dt = float(self.experiment.MicroscopeState['timepoint_interval'])
        ome_dict['Image']['Pixels']['TimeIncrement'] = dt

        # TODO: Populate plane positions in OME-XML
        if views is not None:
            ome_dict['Image']['Pixels']['Plane'] = []
            for i in range(self.shape_c):
                view_idx = i*self.shape_z
                d = {'DeltaT': dt, 'TheT': '0',
                     'TheC': str(i), 'TheZ': '0', 'PositionX': views[view_idx]['x'],
                     'PositionY': views[view_idx]['y'], 'PositionZ': views[view_idx]['z']}
                ome_dict['Image']['Pixels']['Plane'].append(d)

        return ome_dict

    def write_xml(self, file_name: str, file_type: str = 'OME-TIFF', root: Optional[str] = 'OME', **kw) -> None:
        return super().write_xml(file_name, file_type=file_type, root=root, **kw)

    def to_xml(self, file_type: str = 'OME-TIFF', root: Optional[str] = 'OME', **kw) -> str:
        return super().to_xml(file_type, root=root, **kw)
