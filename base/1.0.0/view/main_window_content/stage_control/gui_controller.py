class GUI_Controller:
    def __init__(self, view, parent_controller = None):
        self.view = view
        self.parent_controller = parent_controller
        
    def execute(self, command, *args):
        print('command passed from child', command)
        pass