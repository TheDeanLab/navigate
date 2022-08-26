"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Local imports
from aslm.model.model_features.aslm_feature_container import load_features

class Autofocus():
    def __init__(self, model):
        self.model = model
        self.max_entropy = None
        self.f_frame_id = None
        self.frame_num = None
        self.f_pos = None
        self.target_frame_id = None
        self.get_frames_num = None
        self.plot_data = None
        self.total_frame_num = None

        # Queue
        self.autofocus_frame_queue = Queue()
        self.autofocus_pos_queue = Queue()
        
        # target channel
        self.target_channel = 1

        self.config_table = {'signal': {'init': self.pre_func_signal,
                                        'main': self.in_func_signal,
                                        'end': self.end_func_signal},
                             'data': {'init': self.pre_func_data,
                                      'main': self.in_func_data,
                                      'end': self.end_func_data},
                             'node': {'node_type': 'multi-step',
                                      'device_related': True },
                            }

    def run(self, *args):
        r"""Run the Autofocusing Routine

        Parameters
        ----------
        args[0] : dict
            Current microscope state.
        args[1] : dict
            Autofocus parameters

        """
        self.model.experiment.MicroscopeState = args[0]
        self.model.experiment.AutoFocusParameters = args[1]
        frame_num = self.get_autofocus_frame_num()
        if frame_num < 1:
            return
        self.model.prepare_acquisition()  # Opens correct shutter and puts all signals to false
        
        # load Autofocus
        self.model.signal_container, self.model.data_container = load_features(self.model, [[{'name': Autofocus}]])

        self.model.signal_thread = threading.Thread(target=self.model.run_single_channel_acquisition_with_features,
                                                kwargs={'target_channel': self.target_channel},
                                                name='Autofocus Signal')

        self.model.data_thread = threading.Thread(target=self.model.run_data_process,
                                                  args=(frame_num+1,),
                                                  name='Autofocus Data')

        # Start Threads
        self.model.signal_thread.start()
        self.model.data_thread.start()

    def get_autofocus_frame_num(self):
        r"""Calculate how many frames are needed to get the best focus position."""
        settings = self.model.experiment.AutoFocusParameters
        frames = 0
        if settings['coarse_selected']:
            frames = int(settings['coarse_range']) // int(settings['coarse_step_size']) + 1
        if settings['fine_selected']:
            frames += int(settings['fine_range']) // int(settings['fine_step_size']) + 1
        return frames

    def get_steps(self, ranges, step_size):
        steps = ranges // step_size + 1
        pos_offset = (steps // 2) * step_size + step_size
        return steps, pos_offset

    def pre_func_signal(self):
        settings = self.model.experiment.AutoFocusParameters
        # self.focus_pos = args[2]  # Current position
        # self.focus_pos = self.model.focus_pos # TODO: get focus position from model right now.
        self.focus_pos = self.model.get_stage_position()['f_pos']
        self.total_frame_num = self.get_autofocus_frame_num() #total frame num
        self.coarse_steps, self.init_pos = 0, 0
        if settings['fine_selected']:
            self.fine_step_size = int(settings['fine_step_size'])
            fine_steps, self.fine_pos_offset = self.get_steps(int(settings['fine_range']), self.fine_step_size)
            self.init_pos = self.focus_pos - self.fine_pos_offset
        if settings['coarse_selected']:
            self.coarse_step_size = int(settings['coarse_step_size'])
            self.coarse_steps, coarse_pos_offset = self.get_steps(int(settings['coarse_range']), self.coarse_step_size)
            self.init_pos = self.focus_pos - coarse_pos_offset
        self.signal_id = 0

    def in_func_signal(self):
        if self.signal_id < self.coarse_steps:
            self.init_pos += self.coarse_step_size
            self.model.move_stage({'f': self.init_pos}, wait_until_done=True)
            # print('put to queue:', (self.model.frame_id, self.coarse_steps - self.signal_id, self.init_pos))
            self.autofocus_frame_queue.put((self.model.frame_id, self.coarse_steps - self.signal_id, self.init_pos))

        elif self.signal_id < self.total_frame_num:

            if self.signal_id and self.signal_id == self.coarse_steps:
                self.init_pos = self.autofocus_pos_queue.get(timeout=self.coarse_steps*10)
                self.init_pos -= self.fine_pos_offset
            self.init_pos += self.fine_step_size
            self.model.move_stage({'f': self.init_pos}, wait_until_done=True)
            self.autofocus_frame_queue.put((self.model.frame_id, self.total_frame_num - self.signal_id, self.init_pos))

        else:
            self.init_pos = self.autofocus_pos_queue.get(timeout=self.coarse_steps*10)
            self.model.move_stage({'f': self.init_pos}, wait_until_done=True)

        self.signal_id += 1
        return self.init_pos if self.signal_id > self.total_frame_num else None

    def end_func_signal(self):
        return self.signal_id > self.total_frame_num

    def pre_func_data(self):
        self.max_entropy = 0
        self.f_frame_id = -1  #  to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
        self.frame_num = 10  # any value but not 1
        self.f_pos = 0
        self.target_frame_id = 0 # frame id in the buffer with best focus
        self.get_frames_num = 0
        self.plot_data = []
        self.total_frame_num = self.get_autofocus_frame_num()

    def in_func_data(self, frame_ids=[]):
        self.get_frames_num += len(frame_ids)
        while True:
            try:
                if self.f_frame_id < 0:
                    self.f_frame_id, self.frame_num, self.f_pos = self.autofocus_frame_queue.get_nowait()
                if self.f_frame_id not in frame_ids:
                    break
            except:
                break
            # entropy = self.model.analysis.normalized_dct_shannon_entropy(self.model.data_buffer[self.f_frame_id], 3)
            entropy = self.model.analysis.fast_normalized_dct_shannon_entropy(self.model.data_buffer[self.f_frame_id], 3)
            # entropy = self.model.analysis.image_intensity(self.model.data_buffer[self.f_frame_id], 3)

            # print('entropy:', self.f_frame_id, self.frame_num, self.f_pos, entropy)

            self.model.logger.debug(f'Appending plot data focus, entropy: {self.f_pos}, {entropy}')
            self.plot_data.append([self.f_pos, entropy[0]])
            # Need to initialize entropy above for the first iteration of the autofocus routine.
            # Need to initialize entropy_vector above for the first iteration of the autofocus routine.
            # Then need to append each measurement to the entropy_vector.  First column will be the focus position, 
            # second column would be the DCT entropy value.
            # 
            if entropy > self.max_entropy:
                self.max_entropy = entropy
                self.focus_pos = self.f_pos
                self.target_frame_id = self.f_frame_id

            self.f_frame_id = -1

            if self.frame_num == 1:
                self.frame_num = 10  # any value but not 1
                print('***********max shannon entropy:', self.max_entropy, self.focus_pos)
                # find out the focus
                self.autofocus_pos_queue.put(self.focus_pos)
                # return [self.target_frame_id]

        if self.get_frames_num > self.total_frame_num:
            return frame_ids

    def end_func_data(self):
        print('data:', len(self.plot_data), self.total_frame_num)
        if self.get_frames_num <= self.total_frame_num:
            return False
        # send out plot data
        plot_data = np.asarray(self.plot_data)
        self.model.autofocus_plot_pipe.send(plot_data) # Sending controller plot data
        print('data end: true')
        return self.get_frames_num > self.total_frame_num

    def generate_meta_data(self):
        print('autofocus signal:', self.model.frame_id)
