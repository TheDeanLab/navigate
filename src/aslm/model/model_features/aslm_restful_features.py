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

        self.service_url = self.model.rest_api_config.Ilastik['url']
        self.project_file = None

        self.config_table={'data': {'main': self.data_func}}

    def data_func(self, frame_ids):
        # Ilastik process multiple images in sequence.
        img_data = [base64.b64encode(self.model.data_buffer[idx]) for idx in frame_ids]
        json_data = {
            'dtype': 'uint16', 
            'shape': (self.model.img_height, self.model.img_width),
            'image': [img.decode('utf-8') for img in img_data]
            }

        response = requests.post(f"{self.service_url}/segmentation", json=json_data, stream=True)
        print('get response:', response.status_code)
        if response.status_code == 200:
            # segmentation_mask is a dictionary like object with keys 'arr_0', 'arr_1'...
            segmentation_mask = numpy.load(BytesIO(response.raw.read()))
            # display segmentation
            for idx in range(len(segmentation_mask)):
                self.model.event_queue.put(('ilastik_mask', segmentation_mask['arr_{}'.format(idx)]))
        else:
            print('There is something wrong!')
