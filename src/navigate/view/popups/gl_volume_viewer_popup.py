import tkinter as tk

class GLVolumeViewerPopup:
    """Popup containing widgets for viewing a 3D volume using OpenGL.
       Serves as the view for VolumeViewController.
       """

    def __init__(self, root, *args, **kwargs):
        """Initialize the GLVolumeViewerPopup.
            
        Parameters
        ----------
        root : tkinter.Tk
            Root window of the application.
        args : list
            List of arguments.
        kwargs : dict
            Dictionary of keyword arguments.    
        """
        from navigate.view.custom_widgets.popup import PopUp

        self.popup = PopUp(
            root, 
            name="Volume Settings", 
            size="+320+600",
            top=False,
            transient=False
            )
        self.popup.resizable(tk.FALSE, tk.FALSE)

