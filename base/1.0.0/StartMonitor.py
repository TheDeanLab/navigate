"""
    Main starting point of the program.
    It imports the base classes and defines the function (:meth:`~UUTrack.startCamera.start`)
    The config file is passed to a :class:`~UUTrack.Model.Session` variable.
    That will be shared with the rest of the program.
    The session variable idea comes from programming websites, but is useful in other kind of programs as well.
    :copyright: 2017
    .. sectionauthor:: Aquiles Carattino <aquiles@aquicarattino.com>
"""

# Standard library imports
import os
import sys
from datetime import datetime

# Local imports
from model.session import Session

# Import view
from view.main_application_window import Main_App as main_window
import tkinter as tk


# from UUTrack.View.Monitor.monitorMain import monitorMain

def start(configuration_directory, configuration_file, verbose=False):
    """
    Starts the main window of the program and loads the appropriate configuration file.
    :param str configuration_directory: Folder where the config file is stored
    :param str configuration_file: Name of the config file
    :return: Window for the camera
    """

    initialize_camera = True
    initialize_GUI = True

    # Initialize the Session
    config_path = os.path.join(configuration_directory, configuration_file)
    if verbose:
        print("The Configuration Path is:", config_path)

    global session
    session = Session(config_path, verbose)

    # Initialize GUI
    if initialize_GUI:
        if verbose:
            print("Initializing GUI")

        # Starts the GUI event loop and presents gui to user
        # Instance of the main window any additional windows will be toplevel classes
        root = tk.Tk()

        # Runs the view code which will call controller code to adjust and present the model
        main_window(root, session)

        # GUI event handler
        root.mainloop()

    # Specify Root Saving Directory
    if session.Saving['save_directory'] == '':
        # Default Saving Directory if not specified
        save_directory = base_dir
    else:
        save_directory = session.Saving['save_directory']

    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Update the Session with the new save path
    session.Saving = {'save_directory': save_directory}

    # Initialize Camera
    if initialize_camera == True:
        if verbose:
            print("Attempting to Initialize Cameras")

        if session.CameraParameters['type'] == 'SyntheticCamera':
            if verbose:
                print("Initializing Synthetic Camera")

            # Import the SyntheticCamera Class
            from model.camera.synthetic_camera import Camera

            # Create an instance of the camera class with the CameraParameters
            cam = Camera(session.CameraParameters)

        elif session.CameraParameters['type'] == 'HamamatsuCamera':
            #TODO: Implement Hamamatsu Camera as a subclass of CameraBase
            # Initialize Hamamatsu Camera
            if verbose:
                print("Initializing Hamamatsu Camera")

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
            print("Camera Type Not Recognized - Initialization Failed")
            sys.exit()
    else:
        if verbose:
            print("Did not attempt to initialize the cameras")
        pass



if __name__ == "__main__":
    pass
        
    