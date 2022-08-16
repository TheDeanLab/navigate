from typing import Optional

from .metadata import XMLMetadata


class OMETIFFMetadata(XMLMetadata):

    def ome_tiff_xml_dict(self, c: int = 0, t: int = 0, views: Optional[list] = None, **kw):
        """
        Generates dictionary with same heirarchical structure as OME-XML. Useful for
        OME-TIFF and OME-XML.

        Returns
        -------
        ome_dict
            OME TIFF metadata dictionary
        """
        ome_dict = {'xmlns': "http://www.openmicroscopy.org/Schemas/OME/2016-06",
                    'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                    'xsi:schemaLocation': "http://www.openmicroscopy.org/Schemas/OME/2016-06 "
                                          "http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd"}
        uid = c+t*self.shape_c
        ome_dict['Image'] = {'ID': f'Image:{uid}'}
        ome_dict['Image']['Pixels'] = {'ID': f'Pixels:{uid}'}
        ome_dict['Image']['Pixels']['Type'] = 'uint16'  # Hardcoded from SharedNDArray call

        ome_dict['Image']['Pixels']['SizeX'] = int(self.experiment.CameraParameters['x_pixels'])
        ome_dict['Image']['Pixels']['SizeY'] = int(self.experiment.CameraParameters['y_pixels'])
        
        # The following two are commented since we split our TIFFs into one TIFF stack per
        # channel per time point
        ome_dict['Image']['Pixels']['SizeT'] = int(self.experiment.MicroscopeState['timepoints'])
        ome_dict['Image']['Pixels']['SizeC'] = len(self.experiment.MicroscopeState['channels'])

        ome_dict['Image']['Pixels']['DimensionOrder'] = 'XYCZT'
        if self.experiment.MicroscopeState['image_mode'] == 'z-stack':
            ome_dict['Image']['Pixels']['SizeZ'] = int(self.experiment.MicroscopeState['number_z_steps'])
            ome_dict['Image']['Pixels']['PhysicalSizeZ'] = float(self.experiment.MicroscopeState['step_size'])
        else:
            ome_dict['Image']['Pixels']['SizeZ'] = 1

        # This section contains duplicated code b/c in the instance resolution mode != high or low, we
        # do not want to include this information
        if self.experiment.MicroscopeState['resolution_mode'] == 'low':
            pixel_size = float(self.configuration.ZoomParameters['low_res_zoom_pixel_size'][self.experiment.MicroscopeState['zoom']])
            ome_dict['Image']['Pixels']['PhysicalSizeX'], ome_dict['Image']['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size
        elif self.experiment.MicroscopeState['resolution_mode'] == 'high':
            pixel_size = float(self.configuration.ZoomParameters['high_res_zoom_pixel_size'])
            ome_dict['Image']['Pixels']['PhysicalSizeX'], ome_dict['Image']['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size

        # Units
        ome_dict['Image']['Pixels']['PhysicalSizeXUnit'] = "µm"
        ome_dict['Image']['Pixels']['PhysicalSizeYUnit'] = "µm"
        ome_dict['Image']['Pixels']['PhysicalSizeZUnit'] = "µm"

        ome_dict['Image']['Pixels']['MetadataOnly'] = {}  # Required filler

        ome_dict['Image']['Pixels']['TimeIncrement'] = float(self.experiment.MicroscopeState['timepoint_interval'])

        # TODO: Populate plane positions in OME-XML
        if views is not None:
            ome_dict['Image']['Pixels']['Plane'] = []
            for i in range(self.shape_z):
                view_idx = i+c*self.shape_z
                d = {'TheT': str(t), 'TheC': str(c), 'TheZ': str(i),
                     'PositionX': views[view_idx]['x'], 'PositionY': views[view_idx]['y'], 'PositionZ': views[view_idx]['z'],
                     'PositionXUnit': "µm", 'PositionYUnit': "µm", 'PositionZUnit': "µm"}
                ome_dict['Image']['Pixels']['Plane'].append(d)

        return ome_dict

    def write_xml(self, file_name: str, file_type: str = 'OME-TIFF', root: Optional[str] = 'OME', **kw) -> None:
        return super().write_xml(file_name, file_type=file_type, root=root, **kw)

    def to_xml(self, file_type: str = 'OME-TIFF', root: Optional[str] = 'OME', **kw) -> str:
        return super().to_xml(file_type, root=root, **kw)
