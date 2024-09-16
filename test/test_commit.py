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

# Standard Library Imports
import unittest
from unittest.mock import patch
import subprocess

# Third Party Imports

# Local Imports
from navigate._commit import get_git_revision_hash, get_version_from_file


class TestGetGitRevisionHash(unittest.TestCase):
    def test_return_type(self):
        """Test that the function returns a string."""
        result = get_git_revision_hash()
        self.assertIsInstance(result, str)

    @patch("navigate._commit.subprocess.check_output")
    def test_if_not_git_repo(self, mock_check_output):
        mock_check_output.side_effect = [
            b"true",
            # Mock the return value for ["git", "rev-parse", "--is-inside-work-tree"]
            b"dummy_commit_hash"
            # Mock the return value for ["git", "rev-parse", "HEAD"]
        ]
        result = get_git_revision_hash()

        # Verify the correct calls were made to subprocess.check_output
        mock_check_output.assert_any_call(
            ["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.DEVNULL
        )
        mock_check_output.assert_any_call(["git", "rev-parse", "HEAD"])

        # Assert the returned commit hash
        self.assertEqual(result, "dummy_commit_hash")

    @patch("navigate._commit.subprocess.check_output")
    def test_not_git_repo(self, mock_check_output):
        # throw subprocess.CalledProcessError
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "git")

        result = get_git_revision_hash()

        # Assert that None is returned
        self.assertIsNone(result)


class TestGetVersionFromFile(unittest.TestCase):
    def test_file_found(self):
        result = get_version_from_file()
        self.assertIsInstance(result, str)
        self.assertIsNot(result, "unknown")

    @patch("builtins.open")
    def test_file_not_found(self, mock_open):
        mock_open.side_effect = FileNotFoundError
        result = get_version_from_file()
        self.assertEqual(result, "unknown")
