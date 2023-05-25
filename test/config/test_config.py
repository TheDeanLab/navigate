# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
#

# Standard Imports
import pathlib
import unittest
from multiprocessing import Manager
from multiprocessing.managers import ListProxy, DictProxy


# Third Party Imports

# Local Imports
import aslm.config.config as config


def test_config_methods():
    methods = dir(config)
    desired_methods = [
        "Path",
        "__builtins__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
        "build_nested_dict",
        "get_aslm_path",
        "get_configuration_paths",
        "isfile",
        "load_configs",
        "os",
        "platform",
        "shutil",
        "sys",
        "update_config_dict",
        "yaml",
    ]
    for method in methods:
        assert method in desired_methods


def test_get_aslm_path():
    """Test that the ASLM path is a string."""
    assert isinstance(config.get_aslm_path(), str)
    path_string = config.get_aslm_path()
    assert ".ASLM" in path_string


# Write a test for config.get_configuration_paths()
def test_get_configuration_paths():
    """Test that the configuration paths are a list."""
    paths = config.get_configuration_paths()
    for path in paths:
        assert isinstance(path, pathlib.Path)
    assert len(paths) == 5


class TestBuildNestedDict(unittest.TestCase):
    def setUp(self):
        self.manager = Manager()
        self.parent_dict = {}
        self.key_name = "nested_dict"

    def tearDown(self):
        self.manager.shutdown()

    def test_build_nested_dict_with_string_data(self):
        string_data = "string"
        expected_result = {"nested_dict": "string"}

        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, string_data
        )

        self.assertEqual(self.parent_dict, expected_result)
        self.assertEqual(self.parent_dict[self.key_name], "string")
        assert isinstance(self.parent_dict, dict)

    def test_build_nested_dict_with_list_data(self):
        list_data = ["string1", "string2"]

        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, list_data
        )

        assert isinstance(self.parent_dict, dict)
        assert isinstance(self.parent_dict[self.key_name], ListProxy)
        for i in range(2):
            assert self.parent_dict[self.key_name][i] == list_data[i]

    def test_build_nested_dict_with_dict_data(self):
        dict_data = {"key1": "string1", "key2": "string2"}

        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, dict_data
        )

        assert isinstance(self.parent_dict, dict)
        assert isinstance(self.parent_dict[self.key_name], DictProxy)
        for key in dict_data.keys():
            assert self.parent_dict[self.key_name][key] == dict_data[key]

    def test_update_config_dict_with_bad_string(self):
        test_entry = "string"
        dict_data = {"key1": "string1", "key2": "string2"}
        # Build the nested config
        parent_dict = config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, dict_data
        )

        # Update the nested config
        parent_dict = config.update_config_dict(
            self.manager, parent_dict, self.key_name, test_entry
        )
        assert parent_dict is False
