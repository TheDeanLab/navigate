'''
Sub-controller for the acquire popup window
When the mode is changed, we need to communicate this to the central controller.
Central controller then communicates these changes to the channel_setting_controller.
'''

from view.gui_controller import GUI_Controller

class Acquire_Bar_Controller(GUI_Controller):
    def __init__(self, view, parent_controller):
        super().__init__(view, parent_controller)
        self.verbose = True

        #gui event bind
        #self.view.acquire_btn.config(command=lambda: self.launch_popup_window(self, root, self.verbose))
        self.view.acquire_btn.config(command=lambda: self.launch_popup_window(self, view))

        self.view.pull_down.bind('<<ComboboxSelected>>', lambda *args: self.update_microscope_mode(self, self.verbose))

        self.view.exit_btn.config(command=lambda: self.exit_program(self, self.verbose))

    def launch_popup_window(self, root, verbose=False):
        """
        # The popup window should only be launched if the microscope is set to save the data,
        # with the exception of the continuous acquisition mode.
        # The popup window provides the user with the opportunity to fill in fields that describe the experiment and also
        # dictate the save path of the data in a standardized format.
        """
        # Is the save data checkbox checked?
        #TODO: Fix this.  I broke it. Kevin
        #save_data = self.view.notebook_1.channels_tab.stack_timepoint_frame.save_data.get()
        save_data=True
        if save_data:
            if self.model.experiment.MicroscopeState['image_mode'] != 'continuous':
                popup_window = acquire_popup(root, verbose)

                # Configure the button callbacks on the popup window
                popup_window.content.cancel_btn.config(command=lambda: popup_window.dismiss(verbose))
                popup_window.content.done_btn.config(command=lambda: self.launch_acquisition(popup_window))
                #TODO: The launch_acquisition function should be called here and operate in the mode specified by the user.

                # Populate the base path
                popup_window.content.root_entry_string.set(self.model.experiment.Saving['root_directory'])

                # Populate the user name
                if self.model.experiment.Saving['user'] is not None:
                    popup_window.content.user_string.set(self.model.experiment.Saving['user'])

                # Populate the Tissue Type
                if self.model.experiment.Saving['tissue'] is not None:
                    popup_window.content.tissue_string.set(self.model.experiment.Saving['tissue'])

                # Populate the Cell Type
                if self.model.experiment.Saving['celltype'] is not None:
                    popup_window.content.celltype_string.set(self.model.experiment.Saving['celltype'])

                # Populate the Label Type
                if self.model.experiment.Saving['label'] is not None:
                    popup_window.content.label_string.set(self.model.experiment.Saving['label'])
        else:
            # Launch the acquisition without the popup window. Data will not be saved.  Only displayed to the user in
            # the camera window of the view.
            pass
            #TODO: Here we would begin to acquire data and present it to the user in the View.
            #self.launch_acquisition(verbose)

    def update_microscope_mode(self, verbose):
        '''
        # Gets the state of the pull-down menu and updates the model accordingly.

        '''
        microscope_state = self.pull_down.get()

        if microscope_state == 'Continuous Scan':
            self.model.experiment.MicroscopeState['image_mode'] = 'continuous'
        elif microscope_state == 'Z-Stack':
            self.model.experiment.MicroscopeState['image_mode'] = 'z-stack'
        elif microscope_state == 'Single Acquisition':
            self.model.experiment.MicroscopeState['image_mode'] = 'single'
        elif microscope_state == 'Projection':
            self.model.experiment.MicroscopeState['image_mode'] = 'projection'
        if verbose:
            print("The Microscope State is now:", self.model.experiment.MicroscopeState['image_mode'])

    def exit_program(self, verbose=False):
        if verbose:
            print("Exiting Program")
        sys.exit()


# create_save_path - This can also be broken up into more reasonable smaller functions