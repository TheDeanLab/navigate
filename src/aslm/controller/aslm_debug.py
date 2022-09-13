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
import tkinter.simpledialog as simple_dialog
from tkinter import StringVar
import logging
from pathlib import Path
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class Debug_Module:
    def __init__(self, central_controller, menubar):
        self.central_controller = central_controller

        # self.analysis_type = StringVar()
        # self.analysis_type.set('normal')
        # menubar.add_radiobutton(label='Normal', variable=self.analysis_type, value='normal')
        # menubar.add_radiobutton(label='ObjectInSubprocess', variable=self.analysis_type, value='subprocess')
        # menubar.add_command(label='ProcessPool', command=self.start_autofocus)
        # menubar.add_separator()
        menubar.add_command(label='test feature container', command=self.test_feature_container)
        # menubar.add_command(label='ignored signal?', command=self.debug_ignored_signal)
        # menubar.add_command(label='get timings', command=self.debug_get_timings)
        # menubar.add_command(label='ignored autofocus signal?', command=self.debug_autofocus)
        # menubar.add_command(label='blocked queue?', command=self.debug_blocked_queue)
        # menubar.add_command(label='update image size', command=lambda: self.central_controller.model.run_command('debug', 'update_image_size'))
        # menubar.add_command(label='get shannon value?', command=None)
        # menubar.add_command(label='stop acquire', command=lambda: self.central_controller.execute('stop_acquire'))

        # self.analysis_type.trace_add('write', self.update_analysis)

    def debug_get_timings(self):
        self.central_controller.model.run_command('debug', 'get_timings')

    def test_feature_container(self):
        signal_num = 10
        feature_id = simple_dialog.askinteger('Input', 'Which feature routine do you want?\n \
                            1. detective->yes->save->autofocus->yes->save\n \
                            2. detective->yes->autofocus->yes->save\n \
                            3. detective->yes->save\n \
                            4. detective->save\n \
                            5. autofocus->yes->save\n \
                            6. autofocus')
        if not feature_id:
            print('no input!')
            return
        if feature_id < 1 or feature_id > 6:
            print('no such feature!')
            return
        if feature_id == 3 or feature_id == 4:
            signal_num = 30
        elif feature_id == 1 or feature_id == 2:
            signal_num = 3
        else:
            signal_num = 1
        self.start_debug(signal_num, 'debug', 'test_feature_container', self.central_controller.experiment.MicroscopeState,
                        signal_num, feature_id-1, saving_info=self.central_controller.experiment.Saving)

    def debug_ignored_signal(self):
        signal_num = simple_dialog.askinteger('Input', 'How many signals you want to send out?', parent=self.central_controller.view)
        if not signal_num:
            print('no input!')
            return

        channel_num = len(self.central_controller.experiment['MicroscopeState']['channels'].keys())
        signal_num = (signal_num // channel_num) * channel_num + channel_num

        self.start_debug(signal_num, 'debug', 'ignored_signals', 'live', self.central_controller.experiment.MicroscopeState,
                            signal_num, saving_info=self.central_controller.experiment.Saving)
             

    def debug_autofocus(self):
        signal_num = simple_dialog.askinteger('Input', 'How many signals you want to send out?', parent=self.central_controller.view)
        if not signal_num:
            print('no input!')
            return
        
        self.start_debug(signal_num, 'debug', 'ignored_signals', 'autofocus',
                            self.central_controller.experiment.MicroscopeState,
                            self.central_controller.experiment.AutoFocusParameters,
                            self.central_controller.experiment['StageParameters']['f'],
                            signal_num)
        

    def get_frames(self):
        while True:
            image_id = self.central_controller.show_img_pipe.recv()
            logger.debug(f"Received: {image_id}")
            if image_id == 'stop':
                break
            if not isinstance(image_id, int):
                print('some thing wrong happened, stop the model!', image_id)
                self.central_controller.execute('stop_acquire')
            self.central_controller.camera_view_controller.display_image(
                self.central_controller.data_buffer[image_id])
        print('get frame ends!!!')
        self.central_controller.model.run_command('debug', 'clear_feature_container')
        self.central_controller.execute('stop_acquire')


    def debug_blocked_queue(self):
        signal_num = simple_dialog.askinteger('Input', 'How many signals you want to send out?', parent=self.central_controller.view)
        if not signal_num:
            print('no input!')
            return

        signal_num = (signal_num // 10) * 10 + 10

        self.start_debug(signal_num, 'debug', 'blocked_queue', 
                            self.central_controller.experiment.MicroscopeState,
                            self.central_controller.experiment['StageParameters']['f'],
                            signal_num)

    def start_debug(self, signal_num, *args, **kwargs):

        def func():

            self.central_controller.model.run_command(*args, **kwargs)
            autofocus_plot_pipe = self.central_controller.model.create_pipe('autofocus_plot_pipe')
            
            self.get_frames()

            # image_num = self.central_controller.show_img_pipe.recv()

            # print('signal num:', signal_num, 'image num:', image_num)
            
            self.central_controller.set_mode_of_sub('stop')

        if not self.central_controller.prepare_acquire_data():
            return
        self.central_controller.threads_pool.createThread('camera', func)
        
    def update_analysis(self, *args):
        self.central_controller.model.run_command('debug', 'update_analysis_type', self.analysis_type.get())

    def start_autofocus(self, *args):
        cpu_num = simple_dialog.askinteger('Input', 'How many cpu cores do you want to use for analysis?', parent=self.central_controller.view)
        if not cpu_num:
            print('no input!')
            return

        def func():
            if hasattr(self.central_controller, 'af_popup_controller'):
                self.central_controller.af_popup_controller.update_experiment_values()
            self.central_controller.model.run_command('debug', 'update_analysis_type', 'pool',
                            self.central_controller.experiment.MicroscopeState,
                            self.central_controller.experiment.AutoFocusParameters,
                            self.central_controller.experiment['StageParameters']['f'],
                            cpu_num)
            self.get_frames()
            image_num = self.central_controller.show_img_pipe.recv()

            print('image num:', image_num)
            
            # Rec plot data from model and send to sub controller to display plot
            plot_data = self.central_controller.plot_pipe_controller.recv()
            logger.debug(f"Controller received plot data: {plot_data}")
            if hasattr(self.central_controller, 'af_popup_controller'):
                self.central_controller.af_popup_controller.display_plot(plot_data)
            
            self.central_controller.set_mode_of_sub('stop')

        if not self.central_controller.prepare_acquire_data():
            return
            
        self.central_controller.threads_pool.createThread('camera', func)