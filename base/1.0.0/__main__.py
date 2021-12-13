"""
Starting point for running the program.
"""

if __name__ == '__main__':
    import os
    import pretty_errors
    import tkinter as tk
    from controller.aslm_controller import ASLM_controller as controller
    verbose = True

    # Specify the Configuration Directory
    base_directory = os.path.dirname(os.path.abspath(__file__))
    configuration_directory = os.path.join(base_directory, 'config')
    configuration_path = os.path.join(configuration_directory, 'configuration.yml')

    # Start the GUI
    root = tk.Tk()
    app = controller(root, configuration_path, verbose)
    root.mainloop()
