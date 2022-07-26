"""
This stores functions that are update the dictionary common to aslm.model and aslm.controller.
"""


def update_settings_common(target, args):
    """
    Update dictionary entries common to the model and controller. This helps us percolate changes through the
    copies of the dictionaries in each major object.
    """
    if args[0] == 'channel':
        target.experiment.MicroscopeState['channels'] = args[1]

    if args[0] == 'resolution':
        """
        args[1] is a dictionary that includes 'resolution_mode': 'low', 'zoom': '1x', 'laser_info': ...
        ETL popup window updating the self.etl_constants.
        Passes new self.etl_constants to the self.model.daq
        TODO: Make sure the daq knows which etl data to use based upon wavelength, zoom, resolution mode, etc.
        """
        updated_settings = args[1]
        resolution_mode = updated_settings['resolution_mode']
        zoom = updated_settings['zoom']
        laser_info = updated_settings['laser_info']

        if resolution_mode == 'low':
            target.etl_constants.ETLConstants['low'][zoom] = laser_info
        else:
            target.etl_constants.ETLConstants['high'][zoom] = laser_info
        if target.verbose:
            print(target.etl_constants.ETLConstants['low'][zoom])


        # Modify DAQ to pull the initial values from the etl_constants.yml file, or be passed it from the model.
        # Pass to the self.model.daq to
        #             value = self.resolution_info.ETLConstants[self.resolution][self.mag][laser][etl_name]
        # print(args[1])

    if args[0] == 'galvo':
        (param, value), = args[1].items()
        target.experiment.GalvoParameters[param] = value

    if args[0] == 'number_of_pixels':
        target.experiment.CameraParameters['number_of_pixels'] = args[1]


def update_stage_dict(target, pos_dict):
    # Update our local experiment parameters
    for axis, val in pos_dict.items():
        ax = axis.split('_')[0]
        target.experiment.StageParameters[ax] = val
