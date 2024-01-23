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

# Standard library imports
import unittest
import os
from datetime import datetime
import json

# Third party imports

# Local application imports
from navigate.tools.file_functions import create_save_path, save_yaml_file, delete_folder, load_yaml_file


class CreateSavePathTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.save_root = "test_dir"
        os.mkdir(self.save_root)
        self.date_string = str(datetime.now().date())

    def tearDown(self) -> None:
        delete_folder("test_dir")

    def test_existing_root_directory_no_existing_cell_directories(self):
        """Test 1: Testing with existing root directory and no existing cell
        directories."""
        saving_settings = {
            "root_directory": self.save_root,
            "user": "John Doe",
            "tissue": "Liver",
            "celltype": "Hepatocyte",
            "label": "Sample1",
        }
        expected_save_directory = os.path.join(
            self.save_root,
            "John-Doe",
            "Liver",
            "Hepatocyte",
            "Sample1",
            self.date_string,
            "Cell_001",
        )
        save_directory = create_save_path(saving_settings)

        # Assert that the save directory is correct
        self.assertEqual(save_directory, expected_save_directory)

        # Assert that the save directory and cell directory are created
        self.assertTrue(os.path.exists(save_directory))

        # Delete the created directory
        self.tearDown()

    def test_existing_root_directory_existing_cell_directories(self):
        """Test 2: Testing with existing root directory and existing cell
        sub-directory."""

        os.makedirs(
            os.path.join(
                self.save_root,
                "John-Doe",
                "Liver",
                "Hepatocyte",
                "Sample1",
                self.date_string,
                "Cell_001",
            )
        )

        saving_settings = {
            "root_directory": self.save_root,
            "user": "John Doe",
            "tissue": "Liver",
            "celltype": "Hepatocyte",
            "label": "Sample1",
        }

        save_directory = create_save_path(saving_settings)

        # Assert that the save directory is correct
        self.assertEqual(
            save_directory,
            os.path.join(
                self.save_root,
                "John-Doe",
                "Liver",
                "Hepatocyte",
                "Sample1",
                self.date_string,
                "Cell_002",
            ),
        )

        # Assert that the save directory and cell directory are created
        self.assertTrue(os.path.exists(save_directory))

        # Delete the created directory
        self.tearDown()

    def test_spaces_in_strings(self):
        saving_settings = {
            "root_directory": self.save_root,
            "user": "John Doe",
            "tissue": "Liver Tissue",
            "celltype": "Hepatocyte Cell Type",
            "label": "Sample 1",
        }

        save_directory = create_save_path(saving_settings)
        expected_save_directory = os.path.join(
            self.save_root,
            "John-Doe",
            "Liver-Tissue",
            "Hepatocyte-Cell-Type",
            "Sample-1",
            self.date_string,
            "Cell_001",
        )

        # Assert that the save directory is correct
        self.assertEqual(save_directory, expected_save_directory)

        # Assert that the save directory and cell directory are created
        self.assertTrue(os.path.exists(save_directory))

        # Delete the created directory
        self.tearDown()


class SaveYAMLFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.mkdir("test_dir")
        self.save_root = "test_dir"

    def tearDown(self) -> None:
        delete_folder("test_dir")

    def test_save_yaml_file_success(self):
        content_dict = {"name": "John Doe", "age": 30, "location": "New York"}

        result = save_yaml_file(self.save_root, content_dict)

        # Assert that the file was saved successfully
        self.assertTrue(result)

        # Assert that the file exists
        file_path = os.path.join(self.save_root, "experiment.yml")
        self.assertTrue(os.path.exists(file_path))

        # Assert that the file content is correct
        with open(file_path, "r") as f:
            saved_content = json.load(f)
        self.assertEqual(saved_content, content_dict)

    def test_save_yaml_file_failure(self):
        # Test with non-existing directory
        content_dict = {"name": "John Doe", "age": 30, "location": "New York"}

        result = save_yaml_file(
            os.path.join(self.save_root, "does-not-exist"), content_dict
        )

        # Assert that the file save failed
        self.assertFalse(
            result,
            "File save should have failed. Function does not "
            "create the path if it does not exist.",
        )

        # Assert that the file does not exist
        file_path = os.path.join(self.save_root, "experiment.yml")
        self.assertFalse(os.path.exists(file_path))


class TestDeleteFolder(unittest.TestCase):
    def setUp(self) -> None:
        os.mkdir("test_dir")
        self.save_root = "test_dir"

    def test_delete_folder(self):
        delete_folder(self.save_root)
        self.assertFalse(os.path.exists(self.save_root))


class TestLoadYamlFile(unittest.TestCase):

    def setUp(self) -> None:
        os.mkdir("test_dir")
        self.save_root = "test_dir"

    def tearDown(self) -> None:
        delete_folder("test_dir")

    def test_load_existing_yaml_file(self):
        content_dict = {"name": "John Doe", "age": 30, "location": "New York"}

        result = save_yaml_file(self.save_root, content_dict, "test.yml")
        file_path = os.path.join(self.save_root, "test.yml")
        result = load_yaml_file(file_path)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        assert result == content_dict

    def test_load_nonexistent_yaml_file(self):
        file_path = os.path.join(self.save_root, "test.yml")
        result = load_yaml_file(file_path)
        self.assertIsNone(result)

    def test_load_invalid_yaml_file(self):
        file_path = os.path.join(self.save_root, "test.yml")
        with open(file_path, "w") as f:
            f.write("""
{"name": "John Doe", "age": 30, "locati            
            """)
        result = load_yaml_file(file_path)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
