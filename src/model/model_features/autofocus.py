"""
ASLM camera communication classes.

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

# Standard Library Imports
from queue import Queue
import numpy as np
import threading

class Autofocus():
    def __init__(self, model):
        self.model = model

        # Queue
        self.autofocus_frame_queue = Queue()
        self.autofocus_pos_queue = Queue()

    def run(self, *args):
        self.model.experiment.MicroscopeState = args[0]
        self.model.experiment.AutoFocusParameters = args[1]
        frame_num = self.get_autofocus_frame_num() + 1
        if frame_num < 1:
            return
        self.model.prepare_acquisition()  # Opens correct shutter and puts all signals to false
        self.focus_pos = args[2]  # Current position

        self.model.signal_thread = threading.Thread(target=self.model.run_single_acquisition,
                                                kwargs={'target_channel': 1, 'snap_func': self.snap_image_with_autofocus},
                                                name='Autofocus Signal')

        self.model.data_thread = threading.Thread(target=self.model.run_data_process,
                                            args=(frame_num, self.pre_func_data, self.in_func_data, self.end_func_data,),
                                            name='Autofocus Data')

        # Start Threads
        self.model.signal_thread.start()
        self.model.data_thread.start()

    def get_autofocus_frame_num(self):
        """
        # this function calculate how many frames are needed to get the best focus position.
        """
        settings = self.model.experiment.AutoFocusParameters
        frames = 0
        if settings['coarse_selected']:
            frames = int(settings['coarse_range']) // int(settings['coarse_step_size']) + 1
        if settings['fine_selected']:
            frames += int(settings['fine_range']) // int(settings['fine_step_size']) + 1
        return frames

    def snap_image_with_autofocus(self):
        # get autofocus setting according to channel
        settings = self.model.experiment.AutoFocusParameters
        pos = self.focus_pos

        if settings['coarse_selected']:
            pos = self.send_autofocus_signals(pos, int(settings['coarse_range']), int(settings['coarse_step_size']))

        if settings['fine_selected']:
            pos = self.send_autofocus_signals(pos, int(settings['fine_range']), int(settings['fine_step_size']))

        # move stage to the focus position
        self.model.move_stage({'f': pos}, wait_until_done=True)
        
        self.model.snap_image()
        

    def send_autofocus_signals(self, f_position, ranges, step_size):
        """
        Executes the Autofocusing Routine
        Moves the stages, captures frames, etc.
        """
        steps = ranges // step_size + 1
        pos = f_position - (steps // 2) * step_size
        self.max_entropy = 0
        self.focus_pos = f_position

        for i in range(steps):
            # move focus device
            # low resolution move device
            self.model.move_stage({'f': pos}, wait_until_done=True)
            self.autofocus_frame_queue.put((self.model.frame_id, steps - i, pos))

            self.model.snap_image()
            pos += step_size

        # wait to get the focus position
        pos = self.autofocus_pos_queue.get(timeout=steps*10)
        return pos

    def pre_func_data(self):
        self.f_frame_id = -1  #  to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
        self.frame_num = 10  # any value but not 1
        self.f_pos = self.focus_pos
        self.plot_data = []

    def in_func_data(self, frame_ids=[]):
        while True:
            try:
                if self.f_frame_id < 0:
                    self.f_frame_id, self.frame_num, self.f_pos = self.autofocus_frame_queue.get_nowait()
                if self.f_frame_id not in frame_ids:
                    break
            except:
                break
            entropy = self.model.analysis.normalized_dct_shannon_entropy(self.model.data_buffer[self.f_frame_id], 3)

            self.model.logger.debug(f'Appending plot data focus, entropy: {self.f_pos}, {entropy}')
            self.plot_data.append([self.f_pos, entropy[0]])
            # Need to initialize entropy above for the first iteration of the autofocus routine.
            # Need to initialize entropy_vector above for the first iteration of the autofocus routine.
            # Then need to append each measurement to the entropy_vector.  First column will be the focus position, 
            # second column would be the DCT entropy value.
            # 
            self.f_frame_id = -1
            if entropy > self.max_entropy:
                self.max_entropy = entropy
                self.focus_pos = self.f_pos
            if self.frame_num == 1:
                self.frame_num = 10  # any value but not 1
                print('***********max shannon entropy:', self.max_entropy, self.focus_pos)
                # find out the focus
                self.autofocus_pos_queue.put(self.focus_pos)
                break

    def end_func_data(self):
        plot_data = np.asarray(self.plot_data)
        self.model.plot_pipe.send(plot_data) # Sending controller plot data
