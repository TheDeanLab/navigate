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
#

# Standard library imports

# Third party imports
import pytest

# Local imports
from navigate.controller.sub_controllers import AcquireBarController
from navigate.view.popups.acquire_popup import (
    AcquirePopUp,
)
from navigate.model.data_sources import FILE_TYPES


class TestAcquireBarController:
    """Tests for the AcquireBarController class"""

    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        """Setup for the TestAcquireBarController class

        Parameters
        ----------
        dummy_controller : DummyController
            Instance of the DummyController class
        """
        c = dummy_controller
        v = dummy_controller.view

        self.acquire_bar_controller = AcquireBarController(v.acquire_bar, c)
        self.acquire_bar_controller.populate_experiment_values()

    def test_init(self):
        """Tests the initialization of the AcquireBarController class

        Raises
        ------
        AssertionError
            If the initialization of the AcquireBarController class is not correct
        """
        assert isinstance(self.acquire_bar_controller, AcquireBarController)

    def test_attr(self):
        """Tests the attributes of the AcquireBarController class

        Raises
        ------
        AssertionError
            If the attributes of the AcquireBarController class are not correct
        """
        # Listing off attributes to check existence
        attrs = ["mode", "is_save", "mode_dict"]

        for attr in attrs:
            assert hasattr(self.acquire_bar_controller, attr)

    @pytest.mark.parametrize(
        "mode,mode_expected,value_expected",
        [
            ("live", "indeterminate", None),
            ("single", "determinate", 0),
            ("customized", "indeterminate", None),
            ("z-stack", "determinate", 0),
        ],
    )
    def test_progress_bar(self, mode, mode_expected, value_expected):
        """Tests the progress bar of the AcquireBarController class

        Parameters
        ----------
        mode : str
            Mode of the progress bar
        mode_expected : str
            Expected mode of the progress bar
        value_expected : int
            Expected value of the progress bar


        Raises
        ------
        AssertionError
            If the progress bar of the AcquireBarController class is not correct
        """

        # Startup progress bars
        images_received = 0
        mode = mode
        stop = False
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.acquire_bar_controller.parent_controller.configuration[
                "experiment"
            ][
                "MicroscopeState"
            ],
            mode=mode,
            stop=stop,
        )

        progress_mode = str(self.acquire_bar_controller.view.CurAcq["mode"])
        ovr_mode = str(self.acquire_bar_controller.view.OvrAcq["mode"])

        assert progress_mode == mode_expected, (
            f"Wrong progress bar mode ({progress_mode}) "
            f"relative to microscope mode ({mode})"
        )
        assert ovr_mode == mode_expected, (
            f"Wrong progress bar mode ({progress_mode}) "
            f"relative to microscope mode ({mode})"
        )

        if value_expected is not None:
            progress_start = int(self.acquire_bar_controller.view.CurAcq["value"])
            ovr_start = int(self.acquire_bar_controller.view.OvrAcq["value"])
            assert (
                progress_start == value_expected
            ), "Wrong starting value for progress bar"
            assert ovr_start == value_expected, "Wrong starting value for progress bar"

        # Updating progress bar
        images_received = 1
        while images_received < 6:
            self.acquire_bar_controller.progress_bar(
                images_received=images_received,
                microscope_state=self.acquire_bar_controller.parent_controller.configuration[
                    "experiment"
                ][
                    "MicroscopeState"
                ],
                mode=mode,
                stop=stop,
            )
            making_progress = float(self.acquire_bar_controller.view.CurAcq["value"])
            ovr_progress = float(self.acquire_bar_controller.view.OvrAcq["value"])
            assert (
                making_progress > 0
            ), f"Progress bar should be moving in {mode} mode (making_progress)"
            assert (
                ovr_progress > 0
            ), f"Progress bar should be moving in {mode} mode (ovr_progress)"
            images_received += 1

        # Stopping progress bar
        self.acquire_bar_controller.progress_bar(
            images_received=images_received,
            microscope_state=self.acquire_bar_controller.parent_controller.configuration[
                "experiment"
            ][
                "MicroscopeState"
            ],
            mode=mode,
            stop=True,
        )

        after_stop = float(self.acquire_bar_controller.view.CurAcq["value"])
        after_ovr = float(self.acquire_bar_controller.view.OvrAcq["value"])

        assert after_stop == 0, "Progress Bar did not stop"
        assert after_ovr == 0, "Progress Bar did not stop"

    @pytest.mark.parametrize("mode", ["live", "single", "z-stack", "customized"])
    def test_get_set_mode(self, mode):
        """Tests the get_mode and set_mode methods of the AcquireBarController class

        Parameters
        ----------
        mode : str
            Mode of the progress bar


        Raises
        ------
        AssertionError
            If the get_mode and set_mode methods of the
            AcquireBarController class are not correct
        """
        self.acquire_bar_controller.set_mode(mode)
        test = self.acquire_bar_controller.get_mode()
        assert test == mode, "Mode not set correctly"
        # assert imaging mode is updated in the experiment
        assert (
            self.acquire_bar_controller.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["image_mode"]
            == mode
        )

    def test_set_save(self):
        """Tests the set_save method of the AcquireBarController class


        Raises
        ------
        AssertionError
            If the set_save method of the AcquireBarController class is not correct
        """

        # Assuming save state starts as False
        self.acquire_bar_controller.set_save_option(True)
        assert self.acquire_bar_controller.is_save is True, "Save option not correct"

        # Return value to False
        self.acquire_bar_controller.set_save_option(False)
        assert (
            self.acquire_bar_controller.is_save is False
        ), "Save option did not return to original value"

    def test_stop_acquire(self):
        """Tests the stop_acquire method of the AcquireBarController class


        Raises
        ------
        AssertionError
            If the stop_acquire method of the AcquireBarController class is not correct
        """

        # Stopping acquisition
        self.acquire_bar_controller.stop_acquire()
        assert self.acquire_bar_controller.view.acquire_btn["text"] == "Acquire"

    @pytest.mark.parametrize(
        "user_mode,expected_mode",
        [
            ("Continuous Scan", "live"),
            ("Z-Stack", "z-stack"),
            ("Single Acquisition", "single"),
            ("Customized", "customized"),
        ],
    )
    def test_update_microscope_mode(self, user_mode, expected_mode):
        """Tests the update_microscope_mode method of the AcquireBarController class

        Parameters
        ----------
        user_mode : str
            Mode of the progress bar
        expected_mode : str
            Expected state of the progress bar


        Raises
        ------
        AssertionError
            If the update_microscope_mode method of
            the AcquireBarController class is not correct
        """
        # Assuming mode starts on live
        self.acquire_bar_controller.mode = "live"

        # Setting to mode specified by user
        self.acquire_bar_controller.view.pull_down.set(user_mode)

        # Generate event that calls update microscope mode
        self.acquire_bar_controller.view.pull_down.event_generate(
            "<<ComboboxSelected>>"
        )

        # Checking that new mode gets set by function
        assert self.acquire_bar_controller.mode == expected_mode
        assert (
            self.acquire_bar_controller.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["image_mode"]
            == expected_mode
        )

        # Resetting to live
        self.acquire_bar_controller.view.pull_down.set("Continuous Scan")
        self.acquire_bar_controller.view.pull_down.event_generate(
            "<<ComboboxSelected>>"
        )
        assert self.acquire_bar_controller.mode == "live"

    def test_populate_experiment_values(self):
        """Tests the populate_experiment_values method of the AcquireBarController class


        Raises
        ------
        AssertionError
            If the populate_experiment_values method
            of the AcquireBarController class is not correct
        """

        # Calling function to populate values
        self.acquire_bar_controller.populate_experiment_values()

        # Checking values are what we expect
        for key, value in self.acquire_bar_controller.saving_settings.items():
            assert (
                self.acquire_bar_controller.saving_settings[key]
                == self.acquire_bar_controller.parent_controller.configuration[
                    "experiment"
                ]["Saving"][key]
            )

        # Assuming default value in exp file,
        # can be altered TODO maybe set default to current date
        assert self.acquire_bar_controller.saving_settings["date"] == "2022-06-07"
        assert (
            self.acquire_bar_controller.mode
            == self.acquire_bar_controller.parent_controller.configuration[
                "experiment"
            ]["MicroscopeState"]["image_mode"]
        )

    @pytest.mark.parametrize(
        "text,is_acquiring, save,mode,file_types,choice",
        [
            ("Stop", False, None, "live", [], None),
            ("Stop", True, None, "live", [], None),
            ("Acquire", True, True, "live", [], None),
            ("Acquire", False, True, "live", [], None),
            ("Acquire", False, False, "z-stack", [], None),
            ("Acquire", False, True, "z-stack", FILE_TYPES, "Done"),
            ("Acquire", False, True, "z-stack", FILE_TYPES, "Cancel"),
        ],
    )
    def test_launch_popup_window(
        self, text, is_acquiring, save, mode, file_types, choice
    ):
        """Tests the launch_popup_window method of the AcquireBarController class

        This is the largest test for this controller.
        It will test multiple functions that are all used together
        and difficult to isolate.

        Funcs Tested:
        launch_popup_window
        update_file_type
        launch_acquisition
        update_experiment_values
        acquire_pop.popup.dismiss # This will be double tested in view

        Parameters
        ----------
        text : str
            Text of the button that is clicked
        save : bool
            Whether or not to save the image
        mode : str
            Mode of the progress bar
        file_types : list
            List of file types to save as
        choice : str
            Choice of the user in the popup window


        Raises
        ------
        AssertionError
            If the launch_popup_window method of the
            AcquireBarController class is not correct
        """

        # Setup Gui for test
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")
        self.acquire_bar_controller.view.acquire_btn.configure(text=text)
        self.acquire_bar_controller.is_save = save
        self.acquire_bar_controller.set_mode(mode)
        self.acquire_bar_controller.is_acquiring = is_acquiring

        # Test based on setup, launches popup
        self.acquire_bar_controller.view.acquire_btn.invoke()

        # Checking things are what we expect
        if text == "Stop":
            assert self.acquire_bar_controller.view.acquire_btn["text"] == "Stop"
            if is_acquiring:
                assert (
                    str(self.acquire_bar_controller.view.acquire_btn["state"])
                    == "disabled"
                )
                res = self.acquire_bar_controller.parent_controller.pop()
                assert res == "stop_acquire"
            else:
                assert (
                    str(self.acquire_bar_controller.view.acquire_btn["state"])
                    == "normal"
                )
                res = self.acquire_bar_controller.parent_controller.pop()
                assert res == "Empty command list"

        if text == "Acquire":
            if is_acquiring:
                assert (
                    str(self.acquire_bar_controller.view.acquire_btn["state"])
                    == "normal"
                )
                res = self.acquire_bar_controller.parent_controller.pop()
                assert res == "Empty command list"
                return
            # First scenario Save is on and in live mode
            if save is True and mode == "live":
                assert self.acquire_bar_controller.view.acquire_btn["text"] == "Acquire"
                assert (
                    str(self.acquire_bar_controller.view.acquire_btn["state"])
                    == "disabled"
                )
                res = self.acquire_bar_controller.parent_controller.pop()
                print(res)
                print(self.acquire_bar_controller.parent_controller.pop())
                assert res == "acquire"

            # Second scenario Save is off and mode is not live
            if save is False and mode != "live":
                assert self.acquire_bar_controller.view.acquire_btn["text"] == "Acquire"
                assert (
                    str(self.acquire_bar_controller.view.acquire_btn["state"])
                    == "disabled"
                )
                res = self.acquire_bar_controller.parent_controller.pop()
                assert res == "acquire"

            # Third and final scenario Save is on and mode is not live
            if save is True and mode != "live":

                # Checking if popup created
                assert isinstance(self.acquire_bar_controller.acquire_pop, AcquirePopUp)
                assert self.acquire_bar_controller.acquire_pop.popup.winfo_exists() == 1

                # Testing update_file_type if list exists
                widgets = self.acquire_bar_controller.acquire_pop.get_widgets()
                if len(file_types) > 0:
                    for file in file_types:
                        widgets["file_type"].set(file)
                        assert (
                            self.acquire_bar_controller.saving_settings["file_type"]
                            == file
                        )
                    # Resetting file type back to orginal
                    widgets["file_type"].set("TIFF")
                    assert (
                        self.acquire_bar_controller.saving_settings["file_type"]
                        == "TIFF"
                    )

                # Check that loop thru saving settings is correct
                for k, v in self.acquire_bar_controller.saving_settings.items():
                    if widgets.get(k, None):
                        value = widgets[k].get().strip()
                        assert value == v

                # Grabbing buttons to test
                buttons = self.acquire_bar_controller.acquire_pop.get_buttons()

                if choice == "Cancel":
                    # Testing cancel button

                    buttons["Cancel"].invoke()  # Call to dismiss popup
                    # Check toplevel gone
                    assert (
                        self.acquire_bar_controller.acquire_pop.popup.winfo_exists()
                        == 0
                    )
                    assert (
                        str(self.acquire_bar_controller.view.acquire_btn["state"])
                        == "normal"
                    )
                elif choice == "Done":
                    # Testing done button

                    # Update experiment values test
                    # Changing popup vals to test update
                    # experiment values inside launch acquisition
                    widgets["user"].set("John")
                    widgets["tissue"].set("Heart")
                    widgets["celltype"].set("34T")
                    widgets["label"].set("BCB")
                    widgets["solvent"].set("uDISCO")
                    widgets["file_type"].set("OME-TIFF")
                    widgets["misc"].set("This is a test!")

                    # Launch acquisition start/test
                    buttons["Done"].invoke()  # Call to launch acquisition

                    # Check if update experiment values works correctly
                    pop_vals = self.acquire_bar_controller.acquire_pop.get_variables()
                    for k, v in self.acquire_bar_controller.saving_settings.items():
                        if pop_vals.get(k, None):
                            value = pop_vals[k].strip()
                            assert value == v

                    # Check command sent to controller
                    # and if acquire button changed to Stop
                    res = self.acquire_bar_controller.parent_controller.pop()
                    assert res == "acquire_and_save"
                    assert (
                        str(self.acquire_bar_controller.view.acquire_btn["state"])
                        == "disabled"
                    )
                    assert (
                        self.acquire_bar_controller.acquire_pop.popup.winfo_exists()
                        == 0
                    )

    def test_frequent_start_and_stop_acquisition(self):
        # set up
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")
        self.acquire_bar_controller.view.acquire_btn.configure(text="Acquire")
        self.acquire_bar_controller.is_save = False
        self.acquire_bar_controller.set_mode("live")
        self.acquire_bar_controller.is_acquiring = False

        # start acquisition
        self.acquire_bar_controller.view.acquire_btn.invoke()
        assert self.acquire_bar_controller.view.acquire_btn["text"] == "Acquire"
        assert str(self.acquire_bar_controller.view.acquire_btn["state"]) == "disabled"
        assert self.acquire_bar_controller.is_acquiring is True
        # assert dummy_controller_to_test_acquire_bar.acquisition_count == 1
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "acquire"

        # not in acquisition, click the "Acquire" button several times
        self.acquire_bar_controller.view.acquire_btn.invoke()
        assert self.acquire_bar_controller.view.acquire_btn["text"] == "Acquire"
        assert str(self.acquire_bar_controller.view.acquire_btn["state"]) == "disabled"
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "Empty command list"
        self.acquire_bar_controller.view.acquire_btn.invoke()
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "Empty command list"

        # in acquisition, click "Stop" button several times
        self.acquire_bar_controller.view.acquire_btn.configure(state="normal")
        self.acquire_bar_controller.view.acquire_btn.configure(text="Stop")
        self.acquire_bar_controller.is_acquiring = True

        self.acquire_bar_controller.view.acquire_btn.invoke()
        assert self.acquire_bar_controller.view.acquire_btn["text"] == "Stop"
        assert str(self.acquire_bar_controller.view.acquire_btn["state"]) == "disabled"
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "stop_acquire"
        self.acquire_bar_controller.view.acquire_btn.invoke()
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "Empty command list"
        self.acquire_bar_controller.view.acquire_btn.invoke()
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "Empty command list"
        self.acquire_bar_controller.view.acquire_btn.invoke()
        res = self.acquire_bar_controller.parent_controller.pop()
        assert res == "Empty command list"
