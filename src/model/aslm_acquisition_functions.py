"""
ASLM Acquisition Functions

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

def acquire_with_waveform_update(self):
    """
    # Sets the camera in a state where it can be triggered.
    # Changes the Filter Wheel to the correct position
    # Specifies the laser
    # Open the shutter as specified by the experiment parameters.
    # The NIDAQ tasks are initialized during the daq __init__ function.
    # Not sure if we have to self.daq.close_tasks() them in order to load a fresh waveform.
    # if so, self.daq.initialize_tasks() need to be called after.

    # Grab the image from the camera and save it.
    # Closes the shutter
    # Disables the camera
    """
    self.camera.set_property_value(
        'exposure_time',
        self.experiment.MicroscopeState['channels']['channel_1']['camera_exposure_time'])
    # self.camera.set_exposure_time(self.experiment.MicroscopeState['channels']
    #                               ['channel_1']['camera_exposure_time']/1000)
    # self.camera.initialize_image_series(self.data_ptr)
    self.daq.initialize_tasks()

    self.filter_wheel.set_filter(
        self.experiment.MicroscopeState['channels']['channel_1']['filter'])
    self.daq.identify_laser_idx(
        self.experiment.MicroscopeState['channels']['channel_1']['laser'])
    self.open_shutter()
    self.daq.start_tasks()
    self.daq.create_waveforms()
    self.daq.run_tasks()
    self.daq.stop_tasks()
    # image = self.camera.get_image()
    #  self.save_test_image(image)
    self.close_shutter()
    # self.camera.close_image_series()


def per_z_acquisition(self, microscope_state, microscope_position):
    for z_idx in range(int(microscope_state['number_z_steps'])):
        for channel_idx in range(len(microscope_state['channels'])):
            # Check if it is selected.
            if microscope_state['channels']['is_selected']:
                print("Channel :", channel_idx)
                # self.camera.set_exposure_time(microscope_state['channels']
                #                               ['channel_' + str(channel_idx + 1)]
                #                               ['camera_exposure_time']/1000)
                self.filter_wheel.set_filter(microscope_state['channels']
                                             ['channel_' + str(channel_idx + 1)]
                                             ['filter'])
                self.daq.identify_laser_idx(self.experiment.MicroscopeState['channels']
                                            ['channel_' + str(channel_idx + 1)]
                                            ['laser'])
                self.open_shutter()
                self.daq.create_waveforms()
                self.daq.start_tasks()
                self.daq.run_tasks()
                # image = self.camera.get_image()
                if microscope_state['is_save']:
                    # Save the data.
                    pass
                microscope_position['Z'] = microscope_position['Z'] + \
                    microscope_state['step_size']
                self.stages.move_absolute(microscope_position)


def per_stack_acquisition(self, microscope_state, microscope_position):
    prefix_len = len('channel_')
    for channel_key in microscope_state['channels']:
        channel_idx = int(channel_key[prefix_len:])
        channel = microscope_state['channels'][channel_key]
        if channel['is_selected'] is True:
            if self.verbose:
                print("Channel :", channel_idx)

            self.current_channel = channel_idx
            self.current_exposure_time = channel['camera_exposure_time']
            self.current_filter = channel['filter']
            self.current_laser = channel['laser']

            #  Set the parameters
            # self.camera.set_exposure_time(self.current_exposure_time)
            self.filter_wheel.set_filter(self.current_filter)
            self.daq.identify_laser_idx(self.current_laser)

            self.open_shutter()
            self.daq.create_waveforms()
            self.daq.start_tasks()

            for z_idx in range(int(microscope_state['number_z_steps'])):
                print("Z slice :", z_idx)
                self.daq.run_tasks()
                image = self.camera.get_image()
                if microscope_state['is_save']:
                    # Save the data.
                    pass
                microscope_position['Z'] = microscope_position['Z'] + \
                    microscope_state['step_size']
                self.stages.move_absolute(microscope_position)
        self.close_shutter()


def run_z_stack_acquisition(self, is_multi_position, update_view):
    # self.camera.initialize_image_series(self.data_ptr)

    microscope_state = self.experiment.MicroscopeState
    for time_idx in range(microscope_state['timepoints']):
        if is_multi_position is True:
            for position_idx in range(
                    len(microscope_state['stage_positions'])):
                if self.verbose:
                    print("Position :", position_idx)
                microscope_position = microscope_state['stage_positions'][position_idx]
                self.stages.move_absolute(microscope_position)
                if microscope_state['stack_cycling_mode'] == 'per_stack':
                    #  self.per_stack_acquisition(microscope_state, microscope_position)
                    pass
                elif microscope_state['stack_cycling_mode'] == 'per_z':
                    #  self.per_z_acquisition(microscope_state, microscope_position)
                    pass
        elif is_multi_position is False:
            self.stages.create_position_dict()
            microscope_position = self.stages.position_dict
            print(microscope_position)
            if microscope_state['stack_cycling_mode'] == 'per_stack':
                #  self.per_stack_acquisition(microscope_state, microscope_position)
                pass
            elif microscope_state['stack_cycling_mode'] == 'per_z':
                #  self.per_z_acquisition(microscope_state, microscope_position)
                pass
    # self.camera.close_image_series()
