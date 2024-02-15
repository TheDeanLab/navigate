# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

import unittest
from unittest.mock import patch
from navigate.model.plugins_model import PluginsModel


class TestPluginsModel(unittest.TestCase):
    @patch("os.path.join")
    @patch("pathlib.Path.resolve")
    def test_initialization(self, mock_resolve, mock_join):
        mock_resolve.return_value.parent.parent = "mocked_path"
        mock_join.return_value = "mocked_path/plugins"
        model = PluginsModel()
        self.assertEqual(model.plugins_path, "mocked_path/plugins")

    @patch("navigate.config.config.get_navigate_path")
    @patch("os.makedirs")
    def test_load_plugins(
        self,
        mock_get_nav_path,
        mock_makedirs,
    ):
        mock_get_nav_path.return_value = "mocked_navigate_path"
        model = PluginsModel()
        devices_dict, plugin_acquisition_modes = model.load_plugins()
        self.assertIsInstance(devices_dict, dict)
        self.assertIsInstance(plugin_acquisition_modes, dict)
