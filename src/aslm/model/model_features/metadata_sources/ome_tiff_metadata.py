from .metadata import XMLMetadata

class OMETIFFMetadata(XMLMetadata):
    def __init__(self) -> None:
        super().__init__()

    @property
    def ome_tiff_xml_dict(self) -> dict:
        """
        Generates dictionary with same heirarchical structure as OME-XML. Useful for
        OME-TIFF and OME-XML.

        Returns
        -------
        ome_dict
            OME TIFF metadata dictionary
        """
        ome_dict = {}
        ome_dict['Pixels'] = {}
        ome_dict['Pixels']['Type'] = 'uint16'  # Hardcoded from SharedNDArray call

        ome_dict['Pixels']['SizeX'] = int(self.experiment.CameraParameters['x_pixels'])
        ome_dict['Pixels']['SizeY'] = int(self.experiment.CameraParameters['y_pixels'])
        ome_dict['Pixels']['SizeT'] = int(self.experiment.MicroscopeState['timepoints'])
        ome_dict['Pixels']['SizeC'] = len(self.experiment.MicroscopeState['channels'])

        if self.experiment.MicroscopeState['image_mode'] == 'z-stack':
            ome_dict['Pixels']['SizeZ'] = int(self.experiment.MicroscopeState['number_z_steps'])
            ome_dict['Pixels']['PhysicalSizeZ'] = int(self.experiment.MicroscopeState['step_size'])
            if self.experiment.MicroscopeState['stack_cycling_mode'] == 'per_stack':
                ome_dict['Pixels']['DimensionOrder'] = 'XYZCT'
            elif self.experiment.MicroscopeState['stack_cycling_mode'] == 'per_z':
                ome_dict['Pixels']['DimensionOrder'] = 'XYCZT'
        else:
            ome_dict['Pixels']['SizeZ'] = 1

        # This section contains duplicated code b/c in the instance resolution mode != high or low, we
        # do not want to include this information
        if self.experiment.MicroscopeState['resolution_mode'] == 'low':
            pixel_size = float(self.configuration.ZoomParameters['low_res_zoom_pixel_size'][self.experiment.MicroscopeState['zoom']])
            ome_dict['Pixels']['PhysicalSizeX'], ome_dict['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size
        elif self.experiment.MicroscopeState['resolution_mode'] == 'high':
            pixel_size = float(self.configuration.ZoomParameters['high_res_zoom_pixel_size'])
            ome_dict['Pixels']['PhysicalSizeX'], ome_dict['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size
            
        ome_dict['Pixels']['TimeIncrement'] = float(self.experiment.MicroscopeState['timepoint_interval'])

        return ome_dict