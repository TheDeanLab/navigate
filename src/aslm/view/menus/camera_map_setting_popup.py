from aslm.view.custom_widgets.popup import PopUp

class CameraMapSettingPopup(PopUp):
    """ Popup to create and visualize camera offset and variance map generation. """

    def __init__(self, root, name="Camera Map Settings", size='+320+180', top=True, transient=True, *args, **kwargs):
        super().__init__(root, name, size, top, transient, *args, **kwargs)
    
        