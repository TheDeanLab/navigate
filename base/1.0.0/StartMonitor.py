"""
    Main starting point of the program. It imports the base classes and defines the function (:meth:`~UUTrack.startCamera.start`)
    To start the program you can run either from the command prompt or embed into your own code.

        >>> from UUTrack import startMonitor
        >>> config_dir = 'Path/To/Config_Dir'
        >>> config_file = 'config.yml'
        >>> startMonitor.start(config_dir,config_file)

    The config file is passed to a :class:`~UUTrack.Model.Session` variable.
    That will be shared with the rest of the program.
    The session variable idea comes from programming websites, but is useful in other kind of programs as well.

    :copyright: 2017

    .. sectionauthor:: Aquiles Carattino <aquiles@aquicarattino.com>
"""
import os
import sys
from datetime import datetime

from model.session import Session

# Import View
from view.main_application_window import Main_App as main_window

import tkinter as tk
# from UUTrack.View.Monitor.monitorMain import monitorMain


def start(constants, verbose=False):
    """
    Starts the main window of the program and loads the appropriate configuration file.
    :param str configDir: Folder where the config file is stored
    :param str configFile: Name of the config file
    :return: Window for the camera
    """
    initialize_camera = False

    camera_config = constants.CameraParameters
    saving_config = constants.SavingParameters
    if verbose:
        print("The Camera Configuration is:", camera_config)
        print("The Saving Parameters are:", saving_config)

    #session = Session(camera_config.camera_parameters, saving_config, verbose)

    # Load the GUI
    # monitorMain(session)
    
    '''
    # Make the Path for Saving the Data
    if session.Saving['directory'] == '':
        savedir = os.path.join(base_dir, str(datetime.now().date()))
    else:
        savedir = os.path.join(session.Saving['directory'], str(datetime.now().date()))

    if not os.path.exists(savedir):
        os.makedirs(savedir)

    session.Saving = {'directory': savedir}
    '''

    if initialize_camera == True:
        # Camera Imports
        from model.camera.dcam import Dcam
        from model.camera.dcam import Dcamapi

        # Initialize Dcamapi
        if Dcamapi.init() is not False:
            n = Dcamapi.get_devicecount()
            if verbose:
                print("Found %d cameras" % n)

            # Initialize the cameras
            low_resolution_camera = Dcam(0)
            high_resolution_camera = Dcam(1)

            # Confirm cameras are open, and set default parameters
            if low_resolution_camera.dev_open() is not False:
                low_resolution_camera.dcam_set_default_light_sheet_mode_parameters()
            else:
                print('-NG: low_resolution_camera.dev_open() fails with error {}'.format(low_resolution_camera.lasterr()))
                sys.exit()

            if high_resolution_camera.dev_open() is not False:
                high_resolution_camera.dcam_set_default_light_sheet_mode_parameters()
            else:
                print('-NG: high_resolution_camera.dev_open() fails with error {}'.format(high_resolution_camera.lasterr()))
                sys.exit()

            if verbose:
                print("Cameras Initialized")

        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))
            sys.exit()
    else:
        pass

    # Starts the GUI event loop and presents gui to user
    # Instance of the main window any additional windows will be toplevel classes
    root = tk.Tk()

    # Runs the view code which will call controller code to adjust and present the model
    main_window(root)

    # GUI event handler
    root.mainloop()

if __name__ == "__main__":
        #start('Config', 'Config_Pritam.yml')
    pass
        
    