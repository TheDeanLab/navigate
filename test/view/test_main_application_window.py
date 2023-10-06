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

# Standard Library Imports
import tkinter as tk
import unittest
from unittest.mock import patch

# Third Party Imports
import pytest

# Local Imports
from aslm.view.main_application_window import MainApp


@pytest.mark.skip('_tkinter.TclError: image "pyimage43" doesn\'t exist')
def test_mainapp():
    """
    Tests that the main application and all its widgets gets created and does not
    throw any exceptions. Test will fail if any exceptions.

    Parameters
    ----------
    None

    Returns
    -------
    bool : bool
        True or False as to whether the test passed
    """
    root = tk.Tk()
    main_app = MainApp(root)
    root.update()
    bool = isinstance(main_app, MainApp)
    root.destroy()

    assert bool


class TestMainApplicationWindowWithPatch(unittest.TestCase):
    """This was an elaborate attempt to get our code coverage for
    the main application window to 100%. Was entirely pointless. I should use
    my time more effectively.

    Essentially making sure that our try/except call is working as expected.
    """

    def setUp(self):
        # Create a root Tkinter window for testing
        self.root = tk.Tk()

    def tearDown(self):
        # Destroy the root window after each test
        self.root.destroy()

    @patch(
        target="aslm.view.main_application_window.Path.joinpath",
        side_effect=tk.TclError,
    )
    @patch(target="aslm.view.main_application_window.SettingsNotebook", autospec=True)
    def test_main_app_with_patched_joinpath(
        self, mock_settings_notebook, mock_joinpath
    ):
        # Create an instance of main_application_window
        MainApp(self.root)
        self.root.update()


class TestMainApplicationWindowWithoutPatch(unittest.TestCase):
    def setUp(self):
        # Create a root Tkinter window for testing
        self.root = tk.Tk()

    def tearDown(self):
        # Destroy the root window after each test
        self.root.destroy()

    def test_main_app_without_patched_joinpath(self):
        # Create an instance of main_application_window
        MainApp(self.root)
        self.root.update()
