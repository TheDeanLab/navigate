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
import base64
import requests
import numpy
import json
from io import BytesIO
from math import ceil

import logging
# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

def prepare_service(service_url, **kwargs):
    service_url = service_url.rstrip('/')
    if service_url.endswith('ilastik'):
        r = requests.get(f"{service_url}/load?project={kwargs['project_file']}")
        logger.info(f'get response:{r.status_code}, {r.content}')
        if r.status_code == 200:
            return json.loads(r.content)
    return None

class IlastikSegmentation:
    def __init__(self, model):
        self.model = model

        self.service_url = self.model.configuration['rest_api_config']['Ilastik']['url']
        self.project_file = None

        self.resolution = None
        self.zoom = None
        self.pieces_num = 1
        self.pieces_size = 1

        self.config_table={'data': {'init': self.init_func,
                                    'main': self.data_func}}

    def init_func(self, *args):
        if self.resolution != self.model.configuration['experiment']['MicroscopeState']['resolution_mode'] \
            or self.zoom != self.model.configuration['experiment']['MicroscopeState']['zoom']:
            self.update_setting()

    def data_func(self, frame_ids):
        # Ilastik process multiple images in sequence.
        img_data = [base64.b64encode(self.model.data_buffer[idx]) for idx in frame_ids]
        json_data = {
            'dtype': 'uint16', 
            'shape': (self.model.img_height, self.model.img_width),
            'image': [img.decode('utf-8') for img in img_data]
            }

        response = requests.post(f"{self.service_url}/segmentation", json=json_data, stream=True)
        if response.status_code == 200:
            # segmentation_mask is a dictionary like object with keys 'arr_0', 'arr_1'...
            segmentation_mask = numpy.load(BytesIO(response.raw.read()))
            # display segmentation
            for idx in range(len(segmentation_mask)):
                segmentation_id = 'arr_{}'.format(idx)
                if self.model.display_ilastik_segmentation: 
                    self.model.event_queue.put(('ilastik_mask', segmentation_mask[segmentation_id]))
                # mark position
                if self.model.mark_ilastik_position:
                    self.mark_position(segmentation_mask[segmentation_id])
        else:
            print('There is something wrong!')

    def update_setting(self):
        self.resolution = self.model.configuration['experiment']['MicroscopeState']['resolution_mode']
        self.zoom = self.model.configuration['experiment']['MicroscopeState']['zoom']
        # Get current mag
        current_microscope_name = self.model.configuration['experiment']['MicroscopeState']['microscope_name']
        curr_pixel_size = float(self.model.configuration['configuration']['microscopes'][current_microscope_name]['zoom']['pixel_size'][self.zoom])
        # target resolution is 'high'
        high_res_microscope_name = self.model.configuration['configuration']['gui']['resolution_modes']['high']
        pixel_size = float(self.model.configuration['configuration']['microscopes'][high_res_microscope_name]['zoom']['pixel_size']['N/A'])
        # calculate pieces
        self.pieces_num = int(curr_pixel_size / pixel_size)
        self.pieces_size = ceil(float(self.model.configuration['experiment']['CameraParameters']['x_pixels']) / self.pieces_num)
        self.posistion_step_size = self.pieces_size * pixel_size
        # calculate corner (x,y)
        curr_fov_x = float(self.model.configuration['experiment']['CameraParameters']['x_pixels']) * curr_pixel_size
        curr_fov_y = float(self.model.configuration['experiment']['CameraParameters']['y_pixels']) * curr_pixel_size
        self.x_start = float(self.model.configuration['experiment']['StageParameters']['x']) - curr_fov_x/2
        self.y_start = float(self.model.configuration['experiment']['StageParameters']['y']) - curr_fov_y/2

    def mark_position(self, mask):
        # target_label = self.model.ilastik_target
        target_label = self.model.ilastik_target_labels
        lx, rx = 0, self.pieces_size
        # get current z, theta, focus
        # TODO: are they same as high resolution?
        z = self.model.configuration['experiment']['StageParameters']['z']
        theta = self.model.configuration['experiment']['StageParameters']['theta']
        f = self.model.configuration['experiment']['StageParameters']['f']
        pos_x, pos_y = self.x_start, self.y_start
        table_values = []
        for i in range(self.pieces_num):
            ly, ry = 0, self.pieces_size
            for j in range(self.pieces_num):
                for k in target_label:
                    if numpy.any(mask[lx:rx, ly:ry, 0] == k):
                        table_values.append([pos_x, pos_y, z, theta, f])
                        break
                pos_y += self.posistion_step_size
                ly += self.pieces_size
                ry += self.pieces_size
            lx += self.pieces_size
            rx += self.pieces_size
            pos_x += self.posistion_step_size
            pos_y = self.y_start
        self.model.event_queue.put(('multiposition', table_values))

