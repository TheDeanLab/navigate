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

# Standard Library Imports
from queue import Queue
import threading
import numpy as np
from scipy.optimize import curve_fit

# Local imports
from aslm.model.features.feature_container import load_features
import aslm.model.analysis.image_contrast as img_contrast
from copy import deepcopy

def poly2(x, a, b, c):
    return a*x**2 + b*x + c

def r_squared(y, y_fit):
    y_bar = np.mean(y)
    SS_res = np.sum((y - y_fit)**2)
    SS_tot = np.sum((y - y_bar)**2)

    return 1 - SS_res/SS_tot

def fourier_annulus(im, radius_1=0, radius_2=64):
    
    x_, y_ = np.meshgrid(range(im.shape[1]), range(im.shape[0]))
    
    x_ = x_.astype(float) - x_.mean()
    y_ = y_.astype(float) - y_.mean()

    mask = x_**2 + y_**2 > radius_1**2
    mask *= x_**2 + y_**2 <= radius_2**2
    
    IM = np.fft.fftshift(np.fft.fft2(im))
    IM_abs = np.abs(IM)
    
    IM_mask = IM_abs * mask
    
    return np.mean(IM_mask), IM_mask

class TonyWilson:
    def __init__(self, model):
        self.n_modes = None
        self.n_iter = None
        self.n_steps = None
        self.coef_amp = None
        self.done_all = False
        self.done_itr = False
        
        self.model = model
        self.mirror_controller = self.model.active_microscope.mirror.mirror_controller

        self.n_modes = self.mirror_controller.n_modes
        # self.change_coef = list(range(2, self.n_modes))
        self.change_coef = []
        modes_armed_dict = self.model.configuration['experiment']['AdaptiveOpticsParameters']['TonyWilson']['modes_armed']
        self.mode_names = modes_armed_dict.keys()
        for i, k in enumerate(self.mode_names):
            if modes_armed_dict[k]:
                self.change_coef += [i]
        self.n_coefs = len(self.change_coef)

        self.best_coefs = np.zeros(self.n_modes, dtype=np.float32)
        self.best_coefs_overall = np.zeros(self.n_modes, dtype=np.float32)
        self.best_metric = 0.0
        self.coef_sweep = None
        self.best_peaks = []

        # Queue
        self.tw_frame_queue = Queue()
        self.tw_data_queue = Queue()
        
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
        r"""Run the Tony Wilson iterative AO routine

        Parameters
        ----------
        args[0] : dict
            Current microscope state.
        args[1] : dict
            Autofocus parameters

        """
        frame_num = self.get_tw_frame_num()
        if frame_num < 1:
            return
        self.model.prepare_acquisition()  # Opens correct shutter and puts all signals to false
        self.model.active_microscope.prepare_next_channel()

        # load signal and data containers
        self.model.signal_container, self.model.data_container = load_features(
            self.model, [[{'name': TonyWilson}]]
        )

        self.model.signal_thread = threading.Thread(
            target=self.model.run_acquisition,
            name='TonyWilson Signal'
        )

        self.model.data_thread = threading.Thread(
            target=self.model.run_data_process,
            args=(frame_num+1,),
            name='TonyWilson Data'
        )

        # Start Threads
        self.model.signal_thread.start()
        self.model.data_thread.start()
        
    def get_tw_frame_num(self):
        r"""Calculate how many frames are needed: iterations x steps x num_coefs"""
        settings = self.model.configuration['experiment']['AdaptiveOpticsParameters']['TonyWilson']
        frames = settings['iterations'] * settings['steps'] * self.n_coefs
        return frames + 1

    # don't need this?
    def get_steps(self, ranges, step_size):
        steps = ranges // step_size + 1
        pos_offset = (steps // 2) * step_size + step_size
        return steps, pos_offset

    def pre_func_signal(self):
        # initialize the mirror and coef lists, etc

        # mirror_settings = self.model.configuration['experiment']['MirrorParameters']
        tw_settings = self.model.configuration['experiment']['AdaptiveOpticsParameters']['TonyWilson']

        self.done_all = False

        self.n_iter = tw_settings['iterations']
        self.n_steps = tw_settings['steps']
        self.coef_amp = tw_settings['amplitude']

        # initalize coefs to current
        """ numpy arrays screw up the threading...? need to use SharedNDArray? """
        # self.best_coefs = SharedNDArray(shape=(self.n_modes,), dtype=np.float32)

        self.coef_sweep = np.linspace(-self.coef_amp, self.coef_amp, self.n_steps).astype(np.float32)

        self.signal_id = 0
        self.target_signal_id = 0
        self.total_frame_num = self.get_tw_frame_num()

        # print(f'pre_func_signal\t>>>\t{tw_settings}\ttotal_frame_num={self.total_frame_num}')

    def in_func_signal(self):
        # update everything
        
        """
        Only PUT into frame_queue
        Only GET from data_queue
        """

        while True:
            # only increment the mirror if you've recieved new_data from the data_queue
            try:
                plot_data = self.tw_data_queue.get_nowait()[0]
            except:
                break   

            step = self.signal_id % self.n_steps
            coef = int(self.signal_id/self.n_steps) % self.n_coefs
            itr = int(self.signal_id/self.n_steps/self.n_coefs) % self.n_iter

            coef_arr = np.zeros(self.n_modes, dtype=np.float32)
            c = self.change_coef[coef]
            coef_arr[c] = self.coef_sweep[step]

            self.mirror_controller.display_modes(coef_arr + self.best_coefs)

            # if step == int(self.n_steps/2):
            #     self.best_peaks.append(plot_data[-1])
                
            self.signal_id += 1

            # if coef == 0 and step == 0 and itr > 0:
            #     self.coef_sweep *= 0.9


            if coef == self.n_coefs-1:
                if step == self.n_steps-1:
                    
                    self.coef_sweep *= 0.9
                    self.done_itr = True

                    if itr == self.n_iter-1:
                        self.done_all = True

            self.tw_frame_queue.put((self.model.frame_id, self.total_frame_num - self.signal_id, itr, coef, step, coef_arr)) # put frame_id in the Queue

        return self.signal_id > self.total_frame_num

    def end_func_signal(self):
        # self.model.event_queue.put(('tonywilson', {'best_coefs': self.best_coefs, 'best_peaks': self.best_peaks}))
        return self.signal_id > self.total_frame_num

    def pre_func_data(self):
        self.f_frame_id = -1  #  to indicate if there is one frame need to calculate shannon value, but the image frame isn't ready
        self.frame_num = 10  # any value but not 1
        self.target_frame_id = 0 # frame id in the buffer with best focus
        self.get_frames_num = 0
        self.plot_data = []
        self.trace_list = {}
        self.total_frame_num = self.get_tw_frame_num()
        self.x = self.coef_sweep
        self.y = []
        self.x_fit = np.linspace(-self.coef_amp, self.coef_amp, 1024)
        self.y_fit = []
        self.mirror_img = None

    """
    c = y_min
    2*a*x_max + b = 0
    """

    def process_data(self, coef):
        self.y = self.plot_data
        c = np.min(self.y) # offset guess
        b = (np.max(self.y) - c) / self.coef_amp # slope guess
        a = -b/2
        p, _ = curve_fit(poly2, self.x, self.y, p0=[a,b,c], bounds=([-np.inf, -np.inf, -np.inf], [0., np.inf, np.inf]))
        # x_fit = np.linspace(-self.coef_amp, self.coef_amp, 4096)
        self.y_fit = poly2(self.x_fit, p[0], p[1], p[2])
        r_2 = r_squared(self.y, poly2(self.x, p[0], p[1], p[2]))
        self.best_coefs[self.change_coef[coef-1]] += self.x_fit[self.y_fit.argmax()] * r_2 # weight by R^2 goodness of fit
        self.mirror_img = self.mirror_controller.get_wavefront_pix()

        new_metric = self.plot_data[int(self.n_steps/2)]        
        self.best_peaks.append(new_metric)
        if new_metric > self.best_metric:
            self.best_metric = new_metric
            self.best_coefs_overall = deepcopy(self.best_coefs)
    
        self.plot_data = []

    def in_func_data(self, frame_ids=[]):
        self.get_frames_num += len(frame_ids)
        
        """
        Only GET from frame_queue
        Only PUT into data_queue
        """
        
        out_str = ''

        while True:
            try:
                if self.f_frame_id < 0:
                    self.f_frame_id, self.frame_num, itr, coef, step, coef_arr = self.tw_frame_queue.get_nowait()
                if self.f_frame_id not in frame_ids:
                    break
            except:
                break

            coef_str = ' '.join([f'{c:.2f}' for c in (coef_arr + self.best_coefs)[3:]])
            out_str += f'in_func_data\t>>>\titer: {itr}\tcoef: {coef}\tstep: {step}\t[{coef_str}]'

            # get the image metric
            img = self.model.data_buffer[self.f_frame_id]
            # nx, ny = img.shape
            # nx = int(nx/2)
            # ny = int(ny/2)
            # roi = 128
            # img = img[ny-roi:ny+roi, nx-roi:nx+roi]
            new_data = img.max()
            # new_data = img.mean()
            # new_data = img_contrast.fast_normalized_dct_shannon_entropy(self.model.data_buffer[self.f_frame_id], 3)[0]
            # new_data = img_contrast.image_intensity(self.model.data_buffer[self.f_frame_id], 3)[0]
            # new_data = self.model.data_buffer[self.f_frame_id].mean()
            # new_data = fourier_annulus(self.model.data_buffer[self.f_frame_id], radius_1=50, radius_2=100)[0]

            if len(self.plot_data) == self.n_steps:
                self.process_data(coef)
                self.trace_list[self.mode_names[self.change_coef[coef]]] = {
                    'x': self.x, 'y': self.y,
                    'x_fit': self.x_fit[::32], 'y_fit': self.y_fit[::32]
                    }

            self.plot_data.append(new_data)
            out_str += f'\t{np.flip(self.plot_data)}'

            self.f_frame_id = -1

            print(out_str)

            if self.frame_num == 1:
                self.frame_num = 10  # any value but not 1
                return [self.target_frame_id]

        self.tw_data_queue.put((self.plot_data,))

        if self.get_frames_num > self.total_frame_num:
            return frame_ids

    def end_func_data(self):
        # if self.get_frames_num <= self.total_frame_num:
        #     return False
        # send out plot data
        # self.model.event_queue.put(('autofocus', self.plot_data))
        # print('end_func_data() called!!!')
        if self.done_all:
            self.best_coefs = self.best_coefs_overall        
        try:
            if self.done_itr:
                self.model.event_queue.put(('mirror_update', {
                    'mirror_img': self.mirror_img,
                    'coefs': self.best_coefs
                    }))
                self.model.event_queue.put(('tonywilson', {
                    'peaks': self.best_peaks,
                    'trace': self.trace_list,
                    'done': self.done_all
                    }))
        except Exception as e:
            print(e)
        
        self.done_itr = False

        # self.mirror_controller.flat()
        self.mirror_controller.display_modes(self.best_coefs_overall)
        return self.get_frames_num > self.total_frame_num

