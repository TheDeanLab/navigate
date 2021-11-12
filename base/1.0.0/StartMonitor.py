"""
    Main starting point of the program. It imports the base classes and defines the function (:meth:`~UUTrack.startCamera.start`)
    To start the program you can run either from the command prompt or embed into your own code.

        >>> from UUTrack import startMonitor
        >>> config_dir = 'Path/To/Config_Dir'
        >>> config_file = 'config.yml'
        >>> startMonitor.start(config_dir,config_file)

    The config file is passed to a :class:`~UUTrack.Model._session` variable. That will be shared with the rest of the program. The session variable idea comes from programming websites, but is useful in other kind of programs as well.

    :copyright: 2017

    .. sectionauthor:: Aquiles Carattino <aquiles@aquicarattino.com>
"""
import os
import sys
from datetime import datetime

from model.session import _session
from model.camera.dcam import Dcam as dcam
from view.main_application_window import Main_App as mainwin
import tkinter as tk
# from UUTrack.View.Monitor.monitorMain import monitorMain


def start(constants, verbose=False):
    """
    Starts the main window of the program and loads the appropriate configuration file.
    :param str configDir: Folder where the config file is stored
    :param str configFile: Name of the config file
    :return: Window for the camera
    """

    camera_config = constants.CameraParameters
    saving_config = constants.SavingParameters
    if verbose:
        print("The Camera Configuration is:", camera_config)
        print("The Saving Parameters are:", saving_config)

    session = _session(camera_config.camera_parameters, saving_config, verbose)

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
    
    # Initialize Cameras
    low_resolution_camera = dcam(0)
    high_resolution_camera = dcam(1)

    # Set default camera properties
    low_resolution_camera.dcam_set_default_light_sheet_mode_parameters()
    high_resolution_camera.dcam_set_default_light_sheet_mode_parameters()

    if verbose:
        print("Cameras Initialized")

    #Starts the GUI event loop and presents gui to user
    root = tk.Tk() #Instance of the main window any additional windows will be toplevel classes
    mainwin(root) #Runs the view code which will call controller code to adjust and present the model
    root.mainloop() #GUI event handler

    if __name__ == "__main__":
        start('Config', 'Config_Pritam.yml')
        
    