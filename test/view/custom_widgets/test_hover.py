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
import tkinter as tk
from tkinter import ttk

# Third Party Imports

# Local Imports
from navigate.view.custom_widgets.hover import (
    Hover,
    HoverMixin,
    HoverButton,
    HoverTkButton,
    HoverRadioButton,
    HoverCheckButton,
)


class TestHover(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.widget = tk.Label(self.root, text="Test Widget")
        self.hover = Hover(widget=self.widget, text="Hover Text")

    def tearDown(self):
        self.root.destroy()

    def test_initialization(self):
        # Test the initialization of the Hover class
        self.assertEqual(self.hover.widget, self.widget)
        self.assertIsNone(self.hover.tipwindow)
        self.assertIsNone(self.hover.id)
        self.assertEqual(self.hover.x, 0)
        self.assertEqual(self.hover.y, 0)
        self.assertEqual(self.hover.text, "Hover Text")
        self.assertIsNone(self.hover.description)
        self.assertEqual(self.hover.type, "free")

    def test_set_and_get_description(self):
        # Test the setdescription and getdescription methods
        self.hover.setdescription("Test Description")
        self.assertEqual(self.hover.getdescription(), "Test Description")

    def test_update_and_get_type(self):
        # Test the update_type and get_type methods
        self.hover.update_type("error")
        self.assertEqual(self.hover.get_type(), "error")

    def test_showtip(self):
        # Test the showtip method for the description type
        self.hover.setdescription("Test Tip")
        self.hover.update_type("description")
        self.hover.showtip(self.hover.getdescription())
        self.assertIsNotNone(self.hover.tipwindow)
        self.hover.hidetip()

    def test_seterror(self):
        # Test the seterror method
        self.hover.seterror("Error Message")
        self.assertEqual(self.hover.get_type(), "error")
        self.assertEqual(self.hover.text, "Error Message")
        self.hover.hidetip()

    def test_show_and_hide_events(self):
        # Test the show and hide event handlers
        self.hover.setdescription("Test Description")
        self.hover.update_type("free")

        self.hover.show(None)  # Simulate <Enter> event
        self.assertEqual(self.hover.get_type(), "description")
        self.assertIsNotNone(self.hover.tipwindow)

        self.hover.hide(None)  # Simulate <Leave> event
        self.assertEqual(self.hover.get_type(), "free")
        self.assertIsNone(self.hover.tipwindow)


class TestHoverMixin(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()

    def tearDown(self):
        self.root.destroy()

    def test_hover_mixin(self):
        class TestWidget(HoverMixin, ttk.Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        widget = TestWidget(self.root)
        self.assertIsInstance(widget.hover, Hover)


class TestHoverButton(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.button = HoverButton(self.root, text="Hover Button")

    def tearDown(self):
        self.root.destroy()

    def test_hover_button(self):
        self.assertIsInstance(self.button.hover, Hover)
        self.assertEqual(self.button.cget("text"), "Hover Button")


class TestHoverTkButton(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.button = HoverTkButton(self.root, text="Hover Tk Button")

    def tearDown(self):
        self.root.destroy()

    def test_hover_tk_button(self):
        self.assertIsInstance(self.button.hover, Hover)
        self.assertEqual(self.button.cget("text"), "Hover Tk Button")


class TestHoverRadioButton(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.radio_button = HoverRadioButton(self.root, text="Hover Radio Button")

    def tearDown(self):
        self.root.destroy()

    def test_hover_radio_button(self):
        self.assertIsInstance(self.radio_button.hover, Hover)
        self.assertEqual(self.radio_button.cget("text"), "Hover Radio Button")


class TestHoverCheckButton(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.check_button = HoverCheckButton(self.root, text="Hover Check Button")

    def tearDown(self):
        self.root.destroy()

    def test_hover_check_button(self):
        self.assertIsInstance(self.check_button.hover, Hover)
        self.assertEqual(self.check_button.cget("text"), "Hover Check Button")


if __name__ == "__main__":
    unittest.main()
