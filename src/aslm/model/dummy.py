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
    def __init__(self, view):
        from aslm.controller.configuration_controller import ConfigurationController
        import random

        self.configuration = DummyModel().configuration
        self.commands = []
        self.view = view
        self.configuration_controller = ConfigurationController(self.configuration)
        self.stage_pos = {}
    
    def execute(self, str, sec=None):
        '''
        Appends commands sent via execute, first element is oldest command/first to pop off
        '''
        if sec == None:
            self.commands.append(str)
        else:
            self.commands.append(str)
            self.commands.append(sec)

        if str == 'get_stage_position':
            
            self.stage_pos['x'] = int(random.random())
            self.stage_pos['y'] = int(random.random())

            return self.stage_pos
        
    def pop(self):
        '''
        Use this method in testing code to grab the next command
        '''
        if len(self.commands) > 0:
            return self.commands.pop(0)
        else:
            return "Empty command list"

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