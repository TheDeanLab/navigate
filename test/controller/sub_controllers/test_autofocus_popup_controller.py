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

# Standard library imports

# Third party imports
import pytest
import numpy as np

# Local application imports
from aslm.controller.sub_controllers import AutofocusPopupController
from aslm.view.popups.autofocus_setting_popup import AutofocusPopup


class TestAutofocusPopupController:
    """Class for testing autofocus popup controller

    Attributes
    ----------
    af_controller : AutofocusPopupController
        Controller for autofocus popup

    Methods
    -------
    test_init()
        Tests that the controller is initialized correctly
    test_attr()
        Tests that the attributes are initialized correctly
    test_populate_experiment_values()
        Tests that the values are populated correctly
    test_update_experiment_values()
        Tests that the values are updated correctly
    test_start_autofocus()
        Tests that the start autofocus function works correctly
    test_display_plot()
        Tests that the display plot function works correctly
    """

    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        """Setup for testing autofocus popup controller

        Parameters
        ----------
        dummy_controller : DummyController
            Dummy controller for testing

        Returns
        -------
        None
        """
        autofocus_popup = AutofocusPopup(dummy_controller.view)
        self.autofocus_controller = AutofocusPopupController(
            autofocus_popup, dummy_controller
        )

    def test_init(self):
        """Tests that the controller is initialized correctly

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            If the controller is not initialized correctly
        """
        assert isinstance(self.autofocus_controller, AutofocusPopupController)
        assert self.autofocus_controller.view.popup.winfo_exists() == 1

    def test_attr(self):
        """Tests that the attributes are initialized correctly

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            If the attributes are not initialized correctly
        """

        # Listing off attributes to check existence
        attrs = [
            "autofocus_fig",
            "autofocus_coarse",
            "autofocus_fine",
            "widgets",
            "setting_dict",
        ]

        for attr in attrs:
            assert hasattr(self.autofocus_controller, attr)

    def test_populate_experiment_values(self):
        """Tests that the values are populated correctly

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            If the values are not populated correctly
        """
        for k in self.autofocus_controller.widgets:
            assert self.autofocus_controller.widgets[k].get() == str(
                self.autofocus_controller.setting_dict[k]
            )
            # Some values are ints but Tkinter only uses strings

    def test_update_experiment_values(self):
        """Tests that the values are updated correctly

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            If the values are not updated correctly
        """
        # Changing values
        self.autofocus_controller.widgets["coarse_range"].set(200)
        self.autofocus_controller.widgets["coarse_step_size"].set(30)
        self.autofocus_controller.view.stage_vars[0].set(False)
        self.autofocus_controller.widgets["fine_range"].set(25)
        self.autofocus_controller.widgets["fine_step_size"].set(2)
        self.autofocus_controller.view.stage_vars[1].set(False)

        # Updating file
        self.autofocus_controller.update_experiment_values()

        # Checking values match
        for k in self.autofocus_controller.widgets:
            assert self.autofocus_controller.widgets[k].get() == str(
                self.autofocus_controller.setting_dict[k]
            )

        assert (
            self.autofocus_controller.view.stage_vars[0].get()
            == self.autofocus_controller.setting_dict["coarse_selected"]
        )

        assert (
            self.autofocus_controller.view.stage_vars[1].get()
            == self.autofocus_controller.setting_dict["fine_selected"]
        )

    def test_start_autofocus(self):
        """Tests that the start autofocus function works correctly

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            If the start autofocus function does not work correctly
        """

        # Calling function
        self.autofocus_controller.start_autofocus()

        # Checking message sent
        res = self.autofocus_controller.parent_controller.pop()
        assert res == "autofocus"

    def test_display_plot(self):
        """Tests that the display plot function works correctly

        Todo: Retrieve data from axessubplot instance and
        check that it is correct

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        AssertionError
            If the display plot function does not work correctly
        """
        # Make this robust by sending data and then
        # checking each plot is plotting correct data low priority

        x_data = np.linspace(start=69750.0, stop=70250.0, num=101)
        y_data = np.random.rand(101)
        data = [x_data, y_data]
        self.autofocus_controller.display_plot(data)
        pass
