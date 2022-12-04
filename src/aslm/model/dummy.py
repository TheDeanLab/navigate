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
from pathlib import Path

# Annies imports for dummy feature containter
import multiprocessing as mp
from multiprocessing import Manager
import threading
import time
import random

import numpy as np
import tkinter as tk

from aslm.model.features.feature_container import SignalNode, DataNode, DataContainer, load_features
from aslm.model.features.common_features import WaitToContinue
from aslm.model.features.feature_container import dummy_True
from aslm.config.config import load_configs
from aslm.model.devices.camera.camera_synthetic import SyntheticCamera, SyntheticCameraController
from aslm.controller.thread_pool import SynchronizedThreadPool
from aslm.view.main_application_window import MainApp
from aslm.config import get_configuration_paths
from aslm.controller.controller import Controller



# def get_dummy_model():
#     """
#     Creates a dummy model to be used for testing. All hardware is synthetic and the current config settings are loaded.
#     """
#     # Set up the model, experiment, ETL dictionaries
#     base_directory = Path(__file__).resolve().parent.parent
#     configuration_directory = Path.joinpath(base_directory, 'config')


#     config = Path.joinpath(configuration_directory, 'configuration.yml')
#     experiment = Path.joinpath(configuration_directory, 'experiment.yml')
#     etl_constants = Path.joinpath(configuration_directory, 'etl_constants.yml')

#     class args():
#         """
#         Leaving this class here in case we need to instantiate a full synthetic model
#         """
#         def __init__(self):
#             self.synthetic_hardware = True

#     # This return is used when you want a full syntethic model instead of just variable data from config files
#     # return Model(False, args(), config, experiment, etl_constants)
    
#     class dummy_model():
#         def __init__(self):
#             self.configuration = Configurator(config)
#             self.experiment = Configurator(experiment)
#             self.etl_constants = Configurator(etl_constants)
#             self.data_buffer = None

#     # Instantiate fake model to return
#     dumb_model = dummy_model()

    
#     return dumb_model

class DummyController:
    def __init__(self):
        self.configuration = None
    
    def execute(str):
        return str

class DummyModel:
    def __init__(self):
        # Set up the model, experiment, ETL dictionaries
        base_directory = Path(__file__).resolve().parent.parent
        configuration_directory = Path.joinpath(base_directory, 'config')


        self.config = Path.joinpath(configuration_directory, 'configuration.yaml')
        self.experiment = Path.joinpath(configuration_directory, 'experiment.yml')
        self.etl_constants = Path.joinpath(configuration_directory, 'etl_constants.yml')

        self.manager = Manager()
        self.configuration = load_configs(self.manager,
                                        configuration=self.config,
                                        experiment=self.experiment,
                                        etl_constants=self.etl_constants)

        # self.configuration = Configurator(config)
        # self.experiment = Configurator(experiment)
        # self.etl_constants = Configurator(etl_constants)
        
        self.device = DummyDevice()
        self.signal_pipe, self.data_pipe = None, None

        self.signal_container = None
        self.data_container = None
        self.signal_thread = None
        self.data_thread = None

        self.stop_flag = False
        self.frame_id = 0 #signal_num

        self.current_channel = 0

        self.data = []
        self.signal_records = []
        self.data_records = []

        self.img_width = int(self.configuration['experiment']['CameraParameters']['x_pixels'])
        self.img_height = int(self.configuration['experiment']['CameraParameters']['y_pixels'])
        self.number_of_frames = 10
        self.data_buffer = np.zeros((self.number_of_frames, self.img_width, self.img_height))
        self.data_buffer_positions = np.zeros(shape=(self.number_of_frames, 5), dtype=float)  # z-index, x, y, z, theta, f

        self.camera = {}
        microscope_name = self.configuration['experiment']['MicroscopeState']['microscope_name']
        for k in self.configuration['configuration']['microscopes'].keys():
            self.camera[k] = SyntheticCamera(microscope_name, SyntheticCameraController(), self.configuration)
            self.camera[k].initialize_image_series(self.data_buffer, self.number_of_frames)

    def signal_func(self):
        self.signal_container.reset()
        while not self.signal_container.end_flag:
            if self.signal_container:
                self.signal_container.run()

            self.signal_pipe.send('signal')
            self.signal_pipe.recv()

            if self.signal_container:
                self.signal_container.run(wait_response=True)

            self.frame_id += 1 # signal_num

        self.signal_pipe.send('shutdown')

        self.stop_flag = True

    def data_func(self):
        while not self.stop_flag:
            self.data_pipe.send('getData')
            frame_ids = self.data_pipe.recv()
            print('receive: ', frame_ids)
            if not frame_ids:
                continue

            self.data.append(frame_ids)

            if self.data_container:
                self.data_container.run(frame_ids)
        self.data_pipe.send('shutdown')

    def start(self, feature_list):
        if feature_list is None:
            return False
        self.data = []
        self.signal_records = []
        self.data_records = []
        self.stop_flag = False
        self.frame_id = 0 # signal_num

        self.signal_pipe, self.data_pipe = self.device.setup()

        self.signal_container, self.data_container = load_features(self, feature_list)
        self.signal_thread = threading.Thread(target=self.signal_func, name='signal')
        self.data_thread = threading.Thread(target=self.data_func, name='data')
        self.signal_thread.start()
        self.data_thread.start()

        self.signal_thread.join()
        self.stop_flag = True
        self.data_thread.join()

        return True


class DummyFeature:
    def __init__(self, *args):
        '''
        args: 
            0: model
            1: name
            2: with response (True/False) (1/0)
            3: device related (True/False) (1/0)
            4: multi step (integer >= 1)
            5: has data function? There could be no data functions when node_type is 'multi-step'
        '''
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.running_times_cleanup_func = 0
        self.is_end = False
        self.is_closed = False

        self.model = None if len(args) == 0 else args[0]
        self.feature_name = args[1] if len(args) > 1 else 'none'
        self.config_table = {'signal':{'name-for-test': self.feature_name,
                                       'init': self.signal_init_func,
                                       'main': self.signal_main_func},
                            'data':  {'name-for-test': self.feature_name,
                                      'init': self.data_init_func,
                                      'main': self.data_main_func},
                            'node': {}}

        if len(args) > 2 and args[2]:
            self.config_table['signal']['main-response'] = self.signal_wait_func
            self.has_response_func = True
        else:
            self.has_response_func = False

        if len(args) > 3:
            self.config_table['node']['device_related'] = (args[3] == 1)

        if len(args) > 4 and args[4]>1:
            self.config_table['node']['node_type'] = 'multi-step'
            self.multi_steps = args[4]
            self.config_table['signal']['end'] = self.signal_end_func
            self.config_table['data']['end'] = self.data_end_func
        else:
            self.multi_steps = 1

        if len(args)>5 and args[4]>1 and args[2]==False and args[5]==False:
            self.config_table['data'] = {}

        self.target_frame_id = 0
        self.response_value = 0
        self.current_signal_step = 0
        self.current_data_step = 0
        self.wait_lock = threading.Lock()

    def init_func(self):
        self.init_times += 1

    def main_func(self, value=None):
        self.running_times_main_func += 1
        return value

    def response_func(self, value=None):
        self.running_times_response_func += 1
        return value

    def end_func(self):
        return self.is_end

    def close(self):
        self.is_closed = True
        self.running_times_cleanup_func += 1

    def clear(self):
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.running_times_cleanup_func = 0
        self.is_end = False
        self.is_closed = False

    def signal_init_func(self, *args):
        self.target_frame_id = -1
        self.current_signal_step = 0
        if self.wait_lock.locked():
            self.wait_lock.release()

    def signal_main_func(self, *args):
        self.target_frame_id = self.model.frame_id # signal_num
        if self.feature_name.startswith('node'):
            self.model.signal_records.append((self.target_frame_id, self.feature_name))
        if self.has_response_func:
            self.wait_lock.acquire()
            print(self.feature_name, ': wait lock is acquired!!!!')

        return True

    def signal_wait_func(self, *args):
        self.wait_lock.acquire()
        self.wait_lock.release()
        print(self.feature_name, ': wait response!(signal)', self.response_value)
        return self.response_value

    def signal_end_func(self):
        self.current_signal_step += 1
        return self.current_signal_step >= self.multi_steps

    def data_init_func(self):
        self.current_data_step = 0
        pass

    def data_pre_main_func(self, frame_ids):
        return self.target_frame_id in frame_ids

    def data_main_func(self, frame_ids):
        # assert self.target_frame_id in frame_ids, 'frame is not ready'
        if self.feature_name.startswith('node'):
            self.model.data_records.append((frame_ids[0], self.feature_name))

        if self.has_response_func and self.wait_lock.locked():
            # random Yes/No
            self.response_value = random.randint(0, 1)
            print(self.feature_name, ': wait lock is released!(data)', self.response_value)
            self.wait_lock.release()
            return self.response_value
        return True

    def data_end_func(self):
        self.current_data_step += 1
        return self.current_data_step >= self.multi_steps

class DummyDevice:
    def __init__(self, timecost=0.2):
        self.msg_count = mp.Value('i', 0)
        self.sendout_msg_count = 0
        self.out_port = None
        self.in_port = None
        self.timecost = timecost
        self.stop_flag = False

    def setup(self):
        signalPort, self.in_port = mp.Pipe()
        dataPort, self.out_port = mp.Pipe()
        in_process = mp.Process(target=self.listen)
        out_process = mp.Process(target=self.sendout)
        in_process.start()
        out_process.start()

        self.sendout_msg_count = 0
        self.msg_count.value = 0
        self.stop_flag = False

        return signalPort, dataPort

    def generate_message(self):
        time.sleep(self.timecost)
        self.msg_count.value += 1

    def clear(self):
        self.msg_count.value = 0

    def listen(self):
        while not self.stop_flag:
            signal = self.in_port.recv()
            if signal == 'shutdown':
                self.stop_flag = True
                self.in_port.close()
                break
            self.generate_message()
            self.in_port.send('done')

    def sendout(self, timeout=100):
        while not self.stop_flag:
            msg = self.out_port.recv()
            if msg == 'shutdown':
                self.out_port.close()
                break
            c = 0
            while self.msg_count.value == self.sendout_msg_count and c < timeout:
                time.sleep(0.01)
                c += 1
            self.out_port.send(list(range(self.sendout_msg_count, self.msg_count.value)))
            self.sendout_msg_count = self.msg_count.value