from navigate.controller.sub_controllers.gui import GUIController

class VolumeViewController(GUIController):
    """Controller to drive OpenGL 3D volumerendering.
       Communicates with GLVolumeViewerPopup to get user input for volume rendering settings.
       Has a GLVolumeViewBackend instance handle GPU rendering.
       """
    
    def __init__(self, view, parent_controller=None):
        super().__init__(view=view, parent_controller=parent_controller)

        