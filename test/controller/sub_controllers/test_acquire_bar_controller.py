# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from aslm.controller.sub_controllers import AcquireBarController
import pytest




class TestAcquireBarController():

    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        v = dummy_controller.view
        
        self.acqbarController = AcquireBarController(v.acqbar, v.settings.channels_tab, c)
        self.acqbarController.populate_experiment_values()
        
    def test_init(self):
        
        assert isinstance(self.acqbarController, AcquireBarController)


    def test_attr(self):

        # Listing off attributes to check existence
        attrs = ['parent_view', 'mode', 'is_save', 'mode_dict']

        for attr in attrs:
            assert hasattr(self.acqbarController, attr)

    @pytest.mark.parametrize("mode,mode_expected,value_expected", [ ('live', 'indeterminate', None), ('single', 'determinate', 0), ('projection', 'determinate', 0), ('z-stack', 'determinate', 0) ])
    def test_progress_bar(self, mode, mode_expected, value_expected):
        
        # Simulating an image series

        # Startup progress bars
        images_received = 0
        mode = mode
        stop = False
        self.acqbarController.progress_bar(images_received=images_received,
                                           microscope_state=self.acqbarController.parent_controller.configuration['experiment']['MicroscopeState'],
                                           mode=mode,
                                           stop=stop)
        progress_mode = str(self.acqbarController.view.CurAcq['mode'])
        ovr_mode = str(self.acqbarController.view.OvrAcq['mode'])

        assert progress_mode == mode_expected, f"Wrong progress bar mode ({progress_mode}) relative to microscope mode ({mode})"
        assert ovr_mode == mode_expected, f"Wrong progress bar mode ({progress_mode}) relative to microscope mode ({mode})"

        if value_expected != None:
            progress_start = int(self.acqbarController.view.CurAcq['value'])
            ovr_start = int(self.acqbarController.view.OvrAcq['value'])
            assert progress_start == value_expected, "Wrong starting value for progress bar"
            assert ovr_start == value_expected, "Wrong starting value for progress bar"

        # Updating progress bar
        images_received += 1
        while images_received > 0 and images_received < 6:
            self.acqbarController.progress_bar(images_received=images_received,
                                           microscope_state=self.acqbarController.parent_controller.configuration['experiment']['MicroscopeState'],
                                           mode=mode,
                                           stop=stop)
            making_progress = float(self.acqbarController.view.CurAcq['value'])
            ovr_progress = float(self.acqbarController.view.OvrAcq['value'])
            if mode != 'projection': # Ignoring projection until setup
                assert making_progress > 0, "Progress bar should be moving"
                assert ovr_progress > 0, "Progress bar should be moving"
            

            images_received += 1
        

        # Stopping progress bar
        stop = True
        self.acqbarController.progress_bar(images_received=images_received,
                                           microscope_state=self.acqbarController.parent_controller.configuration['experiment']['MicroscopeState'],
                                           mode=mode,
                                           stop=stop)

        after_stop = float(self.acqbarController.view.CurAcq['value'])
        after_ovr = float(self.acqbarController.view.OvrAcq['value'])

        assert after_stop == 0, "Progress Bar did not stop"
        assert after_ovr == 0, "Progress Bar did not stop"
            
    @pytest.mark.parametrize("mode,expected_state", [ ('live', 'disabled'), ('z-stack', 'normal'), ('single', 'disabled'), ('alignment', 'disabled'), ('projection', 'normal') ])
    def test_update_stack_acq(self, mode, expected_state):

        stack = self.acqbarController.parent_view.stack_acq_frame.get_widgets()

        # Checking mode and expected state
        self.acqbarController.update_stack_acq(mode)
        for key, widget in stack.items():
            state = str(widget.widget['state'])
            assert state == expected_state, f"Widget state not correct for {mode} mode"

        # Switching back to orginal live
        self.acqbarController.update_stack_acq('live')
        for key, widget in stack.items():
            state = str(widget.widget['state'])
            assert state == 'disabled', "Widget state not correct for switching back to live mode"
            
    @pytest.mark.parametrize("mode,expected_state", [ ('live', 'disabled'), ('z-stack', 'normal'), ('single', 'normal'), ('alignment', 'disabled'), ('projection', 'normal') ])
    def test_update_stack_time(self, mode, expected_state):
        
        stack_time = self.acqbarController.parent_view.stack_timepoint_frame.get_widgets()
        
        # Checking mode and expected state
        self.acqbarController.update_stack_time(mode)
        for key, widget in stack_time.items():
            state = str(widget['state'])
            assert state == expected_state, f"Widget state not correct for {mode} mode"
            
        
        # Switching back to orginal live
        self.acqbarController.update_stack_time('live')
        for key, widget in stack_time.items():
            state = str(widget['state'])
            assert state == 'disabled', "Widget state not correct for switching back to live mode"

    @pytest.mark.parametrize("mode", ['live', 'single', 'z-stack', 'projection'])
    def test_get_set_mode(self, mode):
        
        self.acqbarController.set_mode(mode)
        test = self.acqbarController.get_mode()
        
        assert test == mode, "Mode not set correctly"
        
    
    def test_set_save(self):
        
        # Assuming save state starts as False
        self.acqbarController.set_save_option(True)
        assert self.acqbarController.is_save == True, "Save option not correct"

        # Return value to False
        self.acqbarController.set_save_option(False)
        assert self.acqbarController.is_save == False, "Save option did not return to original value"

    def test_stop_acquire(self):

        # Stopping acquitition
        self.acqbarController.stop_acquire()
        assert self.acqbarController.view.acquire_btn['text'] == 'Acquire'
    
    @pytest.mark.parametrize("user_mode,expected_mode", [ ('Continuous Scan', 'live'), ('Z-Stack', 'z-stack'), ('Single Acquisition', 'single'), ('Alignment', 'alignment'), ('Projection', 'projection') ])
    def test_update_microscope_mode(self, user_mode, expected_mode):
        
        # Assuming mode starts on live
        assert self.acqbarController.mode == 'live'
        
        # Setting to mode specified by user
        self.acqbarController.view.pull_down.set(user_mode)
        
        # Generate event that calls update microscope mode
        self.acqbarController.view.pull_down.event_generate('<<ComboboxSelected>>')

        # Checking that new mode gets set by function
        assert self.acqbarController.mode == expected_mode
        
        # Resetting to live
        self.acqbarController.view.pull_down.set('Continuous Scan')
        self.acqbarController.view.pull_down.event_generate('<<ComboboxSelected>>')
        assert self.acqbarController.mode == 'live'
        
    def test_populate_experiment_values(self):
        
        # Calling function to populate values
        self.acqbarController.populate_experiment_values()
        
        # Checking values are what we expect
        for key, value in self.acqbarController.saving_settings.items():
            assert self.acqbarController.saving_settings[key] == self.acqbarController.parent_controller.configuration['experiment']['Saving'][key]
        assert self.acqbarController.saving_settings['date'] == '2022-06-07' # Assuming default value in exp file, can be altered TODO maybe set default to current date
        assert self.acqbarController.mode == self.acqbarController.parent_controller.configuration['experiment']['MicroscopeState']['image_mode']

    @pytest.mark.parametrize("text,save,mode,file_types,choice", [ ('Stop', None, 'live', [], None ), ('Acquire', True, 'live', [], None), ('Acquire', False, 'z-stack', [], None), ('Acquire', True, 'z-stack', ['TIFF', 'OME-TIFF', 'BDV'], 'Done'), ('Acquire', True, 'z-stack', ['TIFF', 'OME-TIFF', 'BDV'], 'Cancel')  ])
    def test_launch_popup_window(self, text, save, mode, file_types, choice):
        '''
        This is the largest test for this controller. It will test multiple functions that are all used together
        and difficult to isolate.
        
        Funcs Tested:
        launch_popup_window
        update_file_type
        launch_acquisition
        update_experiment_values
        acquire_pop.popup.dismiss # This will be double tested in view
        '''

        # Setup Gui for test
        self.acqbarController.view.acquire_btn.configure(text=text)
        self.acqbarController.is_save = save
        self.acqbarController.set_mode(mode)
        
        # Test based on setup, launches popup
        self.acqbarController.view.acquire_btn.invoke()
        
        # Checking things are what we expect
        if text == 'Stop':
            assert self.acqbarController.view.acquire_btn['text'] == 'Acquire'
            res = self.acqbarController.parent_controller.pop()
            assert res == 'stop_acquire'
            
        if text == 'Acquire':
            # First scenario Save is on and in live mode
            if save == True and mode == 'live':
                assert self.acqbarController.view.acquire_btn['text'] == 'Stop'
                res = self.acqbarController.parent_controller.pop()
                print(res)
                print(self.acqbarController.parent_controller.pop())
                assert res == 'acquire'
            
            # Second scenario Save is off and mode is not live
            if save == False and mode != 'live':
                assert self.acqbarController.view.acquire_btn['text'] == 'Stop'
                res = self.acqbarController.parent_controller.pop()
                assert res == 'acquire'
                
            # Third and final scenario Save is on and mode is not live
            if save == True and mode != 'live':
                from aslm.view.main_window_content.acquire_bar_frame.acquire_popup import AcquirePopUp
                
                # Checking if popup created
                assert isinstance(self.acqbarController.acquire_pop, AcquirePopUp)
                assert self.acqbarController.acquire_pop.popup.winfo_exists() == 1

                
                # Testing update_file_type if list exists
                widgets = self.acqbarController.acquire_pop.get_widgets()
                if len(file_types) > 0:
                    for file in file_types:
                        widgets['file_type'].set(file)
                        assert self.acqbarController.saving_settings['file_type'] == file
                    # Resetting file type back to orginal 
                    widgets['file_type'].set('TIFF')
                    assert self.acqbarController.saving_settings['file_type'] == 'TIFF'
                    
                # Check that loop thru saving settings is correct
                for k, v in self.acqbarController.saving_settings.items():
                    if widgets.get(k, None):
                        value = widgets[k].get().strip()
                        assert value == v
                    
                # Grabbing buttons to test
                buttons = self.acqbarController.acquire_pop.get_buttons()

                if choice == 'Cancel':
                    # Testing cancel button

                    buttons['Cancel'].invoke() # Call to dismiss popup
                    # Check toplevel gone
                    assert self.acqbarController.acquire_pop.popup.winfo_exists() == 0

                elif choice == 'Done':
                    # Testing done button

                    # Update experiment values test
                    # Changing popup vals to test update experiment values inside launch acquisition
                    widgets['user'].set("John")
                    widgets['tissue'].set("Heart")
                    widgets['celltype'].set("34T")
                    widgets['label'].set("BCB")
                    widgets['solvent'].set("uDISCO")
                    widgets['file_type'].set("OME-TIFF")
                    widgets['misc'].set("This is a test!")

                    # Launch acquisition start/test
                    buttons['Done'].invoke() # Call to launch acquisition

                    # Check if update experiment values works correctly
                    pop_vals = self.acqbarController.acquire_pop.get_variables()
                    for k, v in self.acqbarController.saving_settings.items():
                        if pop_vals.get(k, None):
                            value = pop_vals[k].strip()
                            assert value == v             

                    # Check command sent to controller and if acquire button changed to Stop
                    res = self.acqbarController.parent_controller.pop()
                    assert res == 'acquire_and_save'
                    assert self.acqbarController.view.acquire_btn['text'] == 'Stop'
                    assert self.acqbarController.acquire_pop.popup.winfo_exists() == 0
