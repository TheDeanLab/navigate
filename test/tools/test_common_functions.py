# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
#

# Standard library imports
import os
import unittest
from multiprocessing import Manager
from multiprocessing.managers import DictProxy, ListProxy

# Third party imports

# Local application imports
import navigate.tools.common_functions as common_functions


def func1():
    print("Function 1 called")


def func2():
    print("Function 2 called")


def func3():
    print("Function 3 called")


class CombineFuncsTestCase(unittest.TestCase):
    def test_combine_funcs(self):
        combined_func = common_functions.combine_funcs(func1, func2, func3)
        # Redirect stdout to capture print statements
        import sys
        from io import StringIO

        original_stdout = sys.stdout
        sys.stdout = StringIO()

        combined_func()

        # Get the printed output
        output = sys.stdout.getvalue()

        # Reset stdout
        sys.stdout = original_stdout

        # Check if the functions were called and printed in the expected order
        expected_output = "Function 1 called\nFunction 2 called\nFunction 3 called\n"
        self.assertEqual(output, expected_output)


class BuildRefNameTestCase(unittest.TestCase):
    def test_build_ref_name(self):
        separator = "_"
        args = ["John", "Doe", 30]
        ref_name = common_functions.build_ref_name(separator, *args)
        expected_ref_name = "John_Doe_30"
        self.assertEqual(ref_name, expected_ref_name)

    def test_build_ref_name_with_custom_separator(self):
        separator = "-"
        args = ["Jane", "Smith", 25]
        ref_name = common_functions.build_ref_name(separator, *args)
        expected_ref_name = "Jane-Smith-25"
        self.assertEqual(ref_name, expected_ref_name)

    def test_build_ref_name_with_empty_arguments(self):
        separator = "_"
        args = []
        ref_name = common_functions.build_ref_name(separator, *args)
        self.assertEqual(ref_name, "")


class CopyProxyObjectTestCase(unittest.TestCase):
    def test_copy_proxy_object_with_dict_proxy(self):
        manager = Manager()
        original_dict = manager.dict({"key1": "value1", "key2": ["value2"]})
        copied_dict = common_functions.copy_proxy_object(original_dict)
        self.assertIsNot(original_dict, copied_dict)
        assert isinstance(copied_dict, dict)
        assert isinstance(original_dict, DictProxy)
        assert copied_dict["key1"] == "value1"
        assert copied_dict["key2"] == ["value2"]

    def test_copy_proxy_object_with_list_proxy(self):
        manager = Manager()
        original_list = manager.list(["item1", {"key": "value"}])
        copied_list = common_functions.copy_proxy_object(original_list)
        self.assertIsNot(original_list, copied_list)
        assert isinstance(copied_list, list)
        assert isinstance(original_list, ListProxy)
        assert copied_list[0] == "item1"
        assert copied_list[1] == {"key": "value"}

    def test_copy_proxy_object_with_non_proxy_object(self):
        non_proxy_object = {"key": "value"}
        copied_object = common_functions.copy_proxy_object(non_proxy_object)
        self.assertIs(non_proxy_object, copied_object)
        assert copied_object["key"] == "value"
        assert isinstance(copied_object, dict)


class TestLoadModuleFromFile(unittest.TestCase):
    def setUp(self):
        dummy_module = """
class DummyModule:
    def __init__(self):
        self.dummy_variable = "hello"

    def dummy_function(self):
        print(self.dummy_variable)

        """
        with open("dummy_module.py", "w") as f:
            f.write(dummy_module)

    def tearDown(self):
        os.remove("dummy_module.py")

    def test_load_module(self):
        module = common_functions.load_module_from_file(
            "DummyModule", "./dummy_module.py"
        )
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, "DummyModule"))
        self.assertTrue(hasattr(module.DummyModule, "dummy_function"))

    def test_invalid_module_file(self):

        with self.assertRaises(FileNotFoundError):
            common_functions.load_module_from_file(
                "nonexistent_module", "./dummy_module2.py"
            )


if __name__ == "__main__":
    unittest.main()
