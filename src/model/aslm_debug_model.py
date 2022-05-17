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

import threading

class Debug_Module:
    def __init__(self, model, verbose=False):
        self.model = model
        self.verbose = verbose

    def debug(self, command, *args, **kwargs):
        getattr(self, command)(*args, **kwargs)

    def ignored_signals(self, command, *args, **kwargs):
        if command == 'live':
            print('live!!!!!!')
            self.model.experiment.MicroscopeState = args[0]
            self.model.is_save = False
            self.model.before_acquisition()
            self.model.signal_thread = threading.Thread(
                target=self.send_signals(args[1]))
            self.model.data_thread = threading.Thread(target=self.get_frames, args=(args[1],))
            self.model.signal_thread.start()
            self.model.data_thread.start()
        elif command == 'autofocus':
            self.model.experiment.MicroscopeState = args[0]
            self.model.experiment.AutoFocusParameters = args[1]
            signal_num = args[3]
            self.model.before_acquisition()
            self.model.autofocus_on = True
            self.model.is_save = False
            f_position = args[2]

            self.model.signal_thread = threading.Thread(target=self.send_autofocus_signals, args=(f_position, signal_num))
            self.model.data_thread = threading.Thread(target=self.get_frames, args=(signal_num,))
            self.model.signal_thread.start()
            self.model.data_thread.start()


    def send_signals(self, signal_num):
        channel_num = len(self.model.experiment.MicroscopeState['channels'].keys())
        i = 0
        while i < signal_num and not self.model.stop_acquisition:
            self.model.run_single_acquisition()
            i += channel_num
            print('sent out', i, 'signals!!!!!')

    def send_autofocus_signals(self, f_position, signal_num):
        ranges = 5 * (signal_num-1)
        step_size = 5
        pos = self.model.send_autofocus_signals(f_position, ranges, step_size)

        print('focus position', pos)

        
    def get_frames(self, num_of_frames=0):
        """
        # This function will listen to camera, when there is a frame ready, it will call next steps to handle the frame data
        """
        count_frame = num_of_frames > 0
        if self.model.autofocus_on:
            f_frame_id = -1 # to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
            frame_num = 10 # any value but not 1

        wait_num = 10
        acquired_frame_num = 0

        while not self.model.stop_acquisition:
            frame_ids = self.model.camera.get_new_frame()
            # frame_ids = self.camera.buf_getlastframedata()
            if self.verbose:
                print('running data process, get frames', frame_ids)
            # if there is at least one frame available
            if not frame_ids:
                wait_num -= 1
                if wait_num <= 0:
                    break
                continue

            wait_num = 10
            acquired_frame_num += len(frame_ids)

            # show image
            if self.verbose:
                print('sent through pipe', frame_ids[0])
            self.model.show_img_pipe.send(frame_ids[0])

            # autofocuse analyse
            # debug: change something here!!!!!
            while self.model.autofocus_on:
                try:
                    if f_frame_id < 0:
                        f_frame_id, frame_num, f_pos = self.model.autofocus_frame_queue.get_nowait()
                    if f_frame_id not in frame_ids:
                        break
                except:
                    break
                entropy = f_frame_id #self.model.analysis.normalized_dct_shannon_entropy(self.model.data_buffer[f_frame_id], 3)
                f_frame_id = -1
                if entropy > self.model.max_entropy:
                    self.model.max_entropy = entropy
                    self.model.focus_pos = f_pos
                if frame_num == 1:
                    frame_num = 10 # any value but not 1
                    print('max shannon entropy:', self.model.max_entropy, self.model.focus_pos)
                    # find out the focus
                    self.model.autofocus_pos_queue.put(self.model.focus_pos)
                    break

            if count_frame:
                num_of_frames -= len(frame_ids)
                self.model.stop_acquisition = (num_of_frames <= 0) or self.model.stop_acquisition
        
        self.model.show_img_pipe.send('stop')
        self.model.show_img_pipe.send(acquired_frame_num)
        print('received frames in total:', acquired_frame_num)
        if self.verbose:
            print('data thread is stopped, send stop to parent pipe')
            