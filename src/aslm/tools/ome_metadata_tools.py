def ome_pixels_dict(configuration, experiment):
    """Map our configuration and experiment dictionary to a new dictionary containing
    OME-specific values for the pixel entry (https://docs.openmicroscopy.org/ome-model/6.3.1).

    Parameters 
    ----------
    configuration : aslm.model.aslm_model_config.Session
        Dictionary of microscope configuration data
    model: aslm.model.aslm_model_config.Session
        Dictionary of microscope experiment data
    
    Returns
    -------
    ome_dict
        OME TIFF metadata dictionary
    """

    ome_dict = {}
    ome_dict['Pixels'] = {}
    ome_dict['Pixels']['Type'] = 'uint16'  # Hardcoded from SharedNDArray call

    ome_dict['Pixels']['SizeX'] = int(experiment.CameraParameters['x_pixels'])
    ome_dict['Pixels']['SizeY'] = int(experiment.CameraParameters['y_pixels'])
    ome_dict['Pixels']['SizeT'] = int(experiment.MicroscopeState['timepoints'])
    ome_dict['Pixels']['SizeC'] = len(experiment.MicroscopeState['channels'])

    if experiment.MicroscopeState['image_mode'] == 'z-stack':
        ome_dict['Pixels']['SizeZ'] = int(experiment.MicroscopeState['number_z_steps'])
        ome_dict['Pixels']['PhysicalSizeZ'] = int(experiment.MicroscopeState['step_size'])
        if experiment.MicroscopeState['stack_cycling_mode'] == 'per_stack':
            ome_dict['Pixels']['DimensionOrder'] = 'XYZCT'
        elif experiment.MicroscopeState['stack_cycling_mode'] == 'per_z':
            ome_dict['Pixels']['DimensionOrder'] = 'XYCZT'
    else:
        ome_dict['Pixels']['SizeZ'] = 1


    # This section contains duplicated code b/c in the instance resolution mode != high or low, we
    # do not want to include this information
    if experiment.MicroscopeState['resolution_mode'] == 'low':
        pixel_size = float(configuration.ZoomParameters['low_res_zoom_pixel_size'][experiment.MicroscopeState['zoom']])
        ome_dict['Pixels']['PhysicalSizeX'], ome_dict['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size
    elif experiment.MicroscopeState['resolution_mode'] == 'high':
        pixel_size = float(configuration.ZoomParameters['high_res_zoom_pixel_size'])
        ome_dict['Pixels']['PhysicalSizeX'], ome_dict['Pixels']['PhysicalSizeY'] = pixel_size, pixel_size
        
    ome_dict['Pixels']['TimeIncrement'] = float(experiment.MicroscopeState['timepoint_interval'])

    return ome_dict
