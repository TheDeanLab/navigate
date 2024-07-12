# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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


# Standard Library Import
import base64
import unittest
import json
import logging
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO

# Third Party Imports
import numpy as np

# Local Imports
from navigate.model.features.restful_features import (
    prepare_service,
    IlastikSegmentation,
)


class TestPrepareService(unittest.TestCase):
    def setUp(self):
        self.service_url = "http://example.com/ilastik"
        self.project_file = "path/to/project.ilp"
        self.expected_url = f"{self.service_url}/load?project={self.project_file}"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            "mymodule"
        )  # Replace with the actual logger name used

    @patch("navigate.model.features.restful_features.requests.get")
    def test_prepare_service_success(self, mock_get):
        expected_response = {"status": "success", "data": "segmentation data"}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(expected_response)
        mock_get.return_value = mock_response

        response = prepare_service(self.service_url, project_file=self.project_file)

        self.assertEqual(response, expected_response)
        mock_get.assert_called_once_with(self.expected_url)

    @patch("navigate.model.features.restful_features.requests.get")
    def test_prepare_service_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = "Error"
        mock_get.return_value = mock_response

        response = prepare_service(self.service_url, project_file=self.project_file)

        self.assertIsNone(response)
        mock_get.assert_called_once_with(self.expected_url)

    def test_prepare_service_non_ilastik_url(self):
        non_ilastik_url = "http://example.com/not_ilastik"
        response = prepare_service(non_ilastik_url, project_file=self.project_file)

        self.assertIsNone(response)


class TestIlastikSegmentation(unittest.TestCase):
    def setUp(self):
        # Set up a mock model object
        shape = (2048, 2048)
        self.mock_model = Mock()
        self.mock_model.configuration = {
            "rest_api_config": {"Ilastik": {"url": "http://example.com/ilastik"}},
            "experiment": {
                "MicroscopeState": {"microscope_name": "Nanoscale", "zoom": "1.0"},
                "CameraParameters": {"x_pixels": "2048", "y_pixels": "2048"},
                "StageParameters": {
                    "x": "100",
                    "y": "100",
                    "z": "50",
                    "theta": "0",
                    "f": "1.0",
                },
            },
            "configuration": {
                "microscopes": {
                    "Nanoscale": {"zoom": {"pixel_size": {"N/A": "1.0", "1.0": "1.0"}}}
                }
            },
        }
        self.mock_model.data_buffer = {
            0: np.random.randint(0, 65536, size=shape, dtype=np.uint16),
            1: np.random.randint(0, 65536, size=shape, dtype=np.uint16),
        }

        self.mock_model.img_height = shape[0]
        self.mock_model.img_width = shape[1]
        self.mock_model.display_ilastik_segmentation = True
        self.mock_model.mark_ilastik_position = False
        self.mock_model.event_queue = MagicMock()

        self.ilastik_segmentation = IlastikSegmentation(self.mock_model)

    @patch("requests.post")
    def test_data_func_success(self, mock_post):
        frame_ids = [0, 1]
        expected_json_data = {
            "dtype": "uint16",
            "shape": (self.mock_model.img_height, self.mock_model.img_width),
            "image": [
                base64.b64encode(self.mock_model.data_buffer[0]).decode("utf-8"),
                base64.b64encode(self.mock_model.data_buffer[1]).decode("utf-8"),
            ],
        }

        # Create a valid numpy array to simulate the response
        array_data = np.array([np.zeros((2048, 2048, 1), dtype=np.uint16)])
        buffer = BytesIO()
        np.savez(buffer, *array_data)
        buffer.seek(0)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raw.read.return_value = buffer.read()
        mock_post.return_value = mock_response

        self.ilastik_segmentation.data_func(frame_ids)

        mock_post.assert_called_once_with(
            "http://example.com/ilastik/segmentation",
            json=expected_json_data,
            stream=True,
        )
        self.mock_model.event_queue.put.assert_called()

        # Test with self.model.mark_ilastik_position set to True
        self.mock_model.mark_ilastik_position = True
        self.mock_model.event_queue.reset_mock()

        self.mock_model.ilastik_target_labels = range(1)
        self.ilastik_segmentation.update_setting()
        self.ilastik_segmentation.data_func(frame_ids)
        assert self.mock_model.event_queue.put.call_count == 2
        # self.mock_model.event_queue.put.assert_called_with(("multiposition"))
        called_args, _ = self.mock_model.event_queue.put.call_args
        assert "multiposition" in called_args[0]

    @patch("requests.post")
    def test_data_func_failure(self, mock_post):
        frame_ids = [0, 1]
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = "Error"
        mock_post.return_value = mock_response

        with patch("builtins.print") as mocked_print:
            self.ilastik_segmentation.data_func(frame_ids)
            mocked_print.assert_called_once_with("There is something wrong!")

    def test_update_setting(self):
        self.ilastik_segmentation.update_setting()

        self.assertEqual(self.ilastik_segmentation.resolution, "Nanoscale")
        self.assertEqual(self.ilastik_segmentation.zoom, "1.0")
        self.assertEqual(self.ilastik_segmentation.pieces_num, 1)
        self.assertEqual(self.ilastik_segmentation.pieces_size, 2048)
        self.assertEqual(self.ilastik_segmentation.posistion_step_size, 2048)
        self.assertEqual(self.ilastik_segmentation.x_start, -924)
        self.assertEqual(self.ilastik_segmentation.y_start, -924)

    def test_init_func_update_settings(self):
        with patch.object(
            self.ilastik_segmentation, "update_setting"
        ) as mock_update_setting:
            self.ilastik_segmentation.resolution = "DifferentResolution"
            self.ilastik_segmentation.zoom = "DifferentZoom"
            self.ilastik_segmentation.init_func()
            mock_update_setting.assert_called_once()

    def test_mark_position(self):
        mask = np.zeros((2048, 2048, 1), dtype=np.uint16)
        mask[0:1024, 0:1024, 0] = 1  # Mock some segmentation data
        self.mock_model.ilastik_target_labels = [1]

        self.ilastik_segmentation.update_setting()
        self.ilastik_segmentation.mark_position(mask)

        self.mock_model.event_queue.put.assert_called()


if __name__ == "__main__":
    unittest.main()
