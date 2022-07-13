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
from aslm.model.model_features.aslm_feature_container import dummy_True

class ChangeResolution:
    def __init__(self, model, resolution_mode='high'):
        self.model = model

        self.config_table={'signal': {'main': self.signal_func}, 
                            'data': {'main': dummy_True}}

        self.resolution_mode = resolution_mode

        
    def signal_func(self):
        self.model.logger.debug('prepare to change resolution')
        self.model.ready_to_change_resolution.acquire()
        self.model.ask_to_change_resolution = True
        self.model.logger.debug('wait to change resolution')
        self.model.ready_to_change_resolution.acquire()
        self.model.change_resolution(self.resolution_mode)
        self.model.logger.debug('changed resolution')
        self.model.ask_to_change_resolution = False
        self.model.prepare_acquisition(False)
        self.model.logger.debug('wake up data thread ')
        self.model.ready_to_change_resolution.release()
        return True

    def data_func(self):
        print('the camera is:', self.model.camera.serial_number)
        return True

    def generate_meta_data(self, *args):
        print('This frame: change resolution', self.resolution_mode, self.model.frame_id)
        return True

class Snap:
    def __init__(self, model):
        self.model = model

        self.config_table={'signal':{},
                            'data': {'main': dummy_True}}

    def generate_meta_data(self, *args):
        print('This frame: snap one frame', self.model.frame_id)
        return True