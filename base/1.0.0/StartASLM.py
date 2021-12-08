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
import tkinter as tk

# Local imports
from model.session import Session
from view.main_application_window import Main_App as main_window
from view.Monitor.ASLMMain import ASLMMain
from initialization_functions import *

def start(configuration_directory, configuration_file, verbose=False):
    """
    Starts the main window of the program and loads the appropriate configuration file.
    :param str configuration_directory: Folder where the config file is stored
    :param str configuration_file: Name of the config file
    :return: Window for the camera
    """

    # Initialize the Session
    config_path = os.path.join(configuration_directory, configuration_file)
    if verbose:
        print("The Configuration Path is:", config_path)

    # Initialize the Session
    global session
    session = Session(config_path, verbose)

    # Specify Root Saving Directory.  The Default saving directory is pulled from the
    # configuration file if it is not specified. Updates session afterwads.
    if session.Saving['save_directory'] == '':
        save_directory = base_dir
    else:
        save_directory = session.Saving['save_directory']
    session.Saving = {'save_directory': save_directory}

    # Start the devices
    cam = start_camera(session, 0, verbose)
    stages = start_stages(session, verbose)


    # Initialize GUI
    if verbose:
        print("Initializing GUI")

    # Starts the GUI event loop and presents gui to user
    # Instance of the main window any additional windows will be toplevel classes
    root = tk.Tk()

    # Runs the view code which will call controller code to adjust and present the model
    main_window(root, session, cam, verbose)

    # GUI event handler
    root.mainloop()


if __name__ == "__main__":
    pass
