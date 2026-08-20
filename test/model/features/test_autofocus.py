# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
from queue import Empty, Full
from unittest.mock import MagicMock, patch

# Third party imports
import numpy as np

# Local imports
from navigate.model.features.autofocus import power_tent
from navigate.model.features.autofocus import Autofocus
from navigate.model.features.autofocus import autofocus_bounds_error
from navigate.model.features.autofocus import plan_autofocus_positions
from navigate.model.utils.exceptions import UserVisibleException
from test.model.dummy import DummyModel


class TestPowerTentFunction(unittest.TestCase):
    def test_power_tent(self):
        # Test with known parameters and expected result
        x = 2.0
        x_offset = 1.0
        y_offset = 0.0
        amplitude = 2.0
        sigma = 0.5
        alpha = 2.0

        # Calculate the expected result manually
        expected_result = y_offset + amplitude * (
            1 - np.abs(sigma * (x - x_offset)) ** alpha
        )

        # Call the function and check if the result is close to the expected result
        result = power_tent(x, x_offset, y_offset, amplitude, sigma, alpha)
        self.assertAlmostEqual(result, expected_result, places=6)

    def test_power_tent_boundary_cases(self):
        # Test some boundary cases
        x_offset = 0.0
        y_offset = 0.0
        amplitude = 1.0
        sigma = 1.0
        alpha = 1.0

        # Test at x = x_offset, should be y_offset + amplitude
        result = power_tent(x_offset, x_offset, y_offset, amplitude, sigma, alpha)
        self.assertAlmostEqual(result, y_offset + amplitude, places=6)

        # Test at x = x_offset + 1, should be y_offset
        result = power_tent(x_offset + 1, x_offset, y_offset, amplitude, sigma, alpha)
        self.assertAlmostEqual(result, y_offset, places=6)


class TestAutofocusScanPlanning(unittest.TestCase):
    def test_plan_autofocus_positions_with_odd_frame_count(self):
        self.assertEqual(
            plan_autofocus_positions(0, 500, 50),
            tuple(range(-250, 251, 50)),
        )

    def test_plan_autofocus_positions_with_even_frame_count(self):
        self.assertEqual(
            plan_autofocus_positions(0, 10, 2),
            (-6, -4, -2, 0, 2, 4),
        )

    def test_plan_autofocus_positions_preserves_center_and_partial_range(self):
        self.assertEqual(
            plan_autofocus_positions(12.5, 5, 2),
            (10.5, 12.5, 14.5),
        )

    def test_autofocus_bounds_error_reports_each_violation(self):
        lower = autofocus_bounds_error("coarse", (-10, 0, 10), 0, 100, "f")
        upper = autofocus_bounds_error("fine", (90, 100, 110), 0, 100, "f")
        both = autofocus_bounds_error("coarse", (-10, 50, 110), 0, 100, "f")

        self.assertEqual(
            lower,
            "The requested coarse scan (-10 to 10 µm) exceeds the focus-stage "
            "limits (0 to 100 µm).",
        )
        self.assertEqual(
            upper,
            "The requested fine scan (90 to 110 µm) exceeds the focus-stage "
            "limits (0 to 100 µm).",
        )
        self.assertEqual(
            both,
            "The requested coarse scan (-10 to 110 µm) exceeds the focus-stage "
            "limits (0 to 100 µm).",
        )

    def test_autofocus_bounds_error_accepts_positions_at_limits(self):
        self.assertIsNone(autofocus_bounds_error("coarse", (0, 50, 100), 0, 100, "f"))

    def test_autofocus_bounds_error_preserves_near_boundary_violation(self):
        error = autofocus_bounds_error("fine", (999.9, 1000.0001), 0, 1000, "f")

        self.assertEqual(
            error,
            "The requested fine scan (999.9 to 1000.0001 µm) exceeds the "
            "focus-stage limits (0 to 1000 µm).",
        )


class TestAutofocusClass(unittest.TestCase):
    def setUp(self):
        # Initialize an instance of the Autofocus class for testing
        model = DummyModel()
        model.active_microscope_name = "Mesoscale"
        self.autofocus = Autofocus(model=model, device="stage", device_ref="f")

    def test_get_autofocus_frame_num(self):
        # Test the get_autofocus_frame_num method
        settings = {
            "coarse_selected": True,
            "coarse_range": 8.0,
            "coarse_step_size": 2.0,
            "fine_selected": True,
            "fine_range": 5.0,
            "fine_step_size": 1.0,
        }
        self.autofocus.model.configuration = {
            "experiment": {
                "AutoFocusParameters": {"Mesoscale": {"stage": {"f": settings}}}
            }
        }
        # Both Fine and Coarse Selected
        frames = self.autofocus.get_autofocus_frame_num()
        self.assertEqual(frames, 11)  # Expected number of frames

        # Only Coarse Selected
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["fine_selected"] = False
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["coarse_selected"] = True
        autofocus = Autofocus(
            model=self.autofocus.model, device="stage", device_ref="f"
        )
        frames = autofocus.get_autofocus_frame_num()
        self.assertEqual(frames, 5)  # Expected number of frames

        # Only Fine Selected
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["fine_selected"] = True
        self.autofocus.model.configuration["experiment"]["AutoFocusParameters"][
            "Mesoscale"
        ]["stage"]["f"]["coarse_selected"] = False
        autofocus = Autofocus(
            model=self.autofocus.model, device="stage", device_ref="f"
        )
        frames = autofocus.get_autofocus_frame_num()
        self.assertEqual(frames, 6)  # Expected number of frames

    def test_get_steps(self):
        # Test the get_steps method
        steps, pos_offset = self.autofocus.get_steps(10.0, 2.0)
        self.assertEqual(steps, 6)  # Expected number of steps
        self.assertEqual(pos_offset, 8.0)  # Expected position offset

    def configure_stage_bounds(self, minimum=0, maximum=1000, enabled=True):
        stage = MagicMock()
        stage.stage_limits = enabled
        stage.f_min = minimum
        stage.f_max = maximum
        self.autofocus.model.active_microscope.stages = {"f": stage}
        return stage

    def set_scan_settings(
        self,
        *,
        coarse_selected=True,
        coarse_range=500,
        coarse_step_size=50,
        fine_selected=False,
        fine_range=50,
        fine_step_size=5,
        focus_position=0,
    ):
        settings = self.autofocus.model.configuration["experiment"][
            "AutoFocusParameters"
        ]["Mesoscale"]["stage"]["f"]
        settings.update(
            {
                "coarse_selected": coarse_selected,
                "coarse_range": coarse_range,
                "coarse_step_size": coarse_step_size,
                "fine_selected": fine_selected,
                "fine_range": fine_range,
                "fine_step_size": fine_step_size,
            }
        )
        self.autofocus.model.configuration["experiment"]["StageParameters"][
            "f"
        ] = focus_position

    def test_run_rejects_invalid_coarse_scan_before_preparing_acquisition(self):
        self.configure_stage_bounds()
        self.set_scan_settings()
        model = self.autofocus.model
        model.prepare_acquisition = MagicMock()
        model.event_queue = MagicMock()
        model.show_img_pipe = MagicMock()
        model.is_acquiring = True

        self.autofocus.run()

        model.prepare_acquisition.assert_not_called()
        model.event_queue.put.assert_called_once_with(
            (
                "warning",
                "The requested coarse scan (-250 to 250 µm) exceeds the "
                "focus-stage limits (0 to 1000 µm).",
            )
        )
        model.show_img_pipe.send.assert_called_once_with("stop")
        self.assertFalse(model.is_acquiring)

    def test_initial_scan_bounds_ignore_disabled_soft_limits(self):
        self.configure_stage_bounds(enabled=False)
        self.set_scan_settings()

        self.assertIsNone(self.autofocus.get_initial_scan_bounds_error())

    def test_run_rejects_when_no_valid_scan_mode_is_selected(self):
        self.set_scan_settings(
            coarse_selected=True,
            coarse_range=0,
            fine_selected=True,
            fine_range=0,
        )
        model = self.autofocus.model
        model.prepare_acquisition = MagicMock()
        model.event_queue = MagicMock()
        model.show_img_pipe = MagicMock()
        model.is_acquiring = True

        self.autofocus.run()

        model.prepare_acquisition.assert_not_called()
        model.event_queue.put.assert_called_once_with(
            (
                "warning",
                "Coarse/Fine settings error!\n\n"
                "Select at least one mode: Coarse or Fine.\n"
                "Please ensure the range and step size are greater than zero.",
            )
        )
        model.show_img_pipe.send.assert_called_once_with("stop")
        self.assertFalse(model.is_acquiring)

    def test_negative_scan_settings_are_normalized_before_frame_counting(self):
        self.set_scan_settings(
            coarse_selected=True,
            coarse_range=-10,
            coarse_step_size=-2,
            fine_selected=False,
        )

        self.assertEqual(self.autofocus.get_autofocus_frame_num(), 6)
        self.assertEqual(self.autofocus.coarse_range, 10)
        self.assertEqual(self.autofocus.coarse_step_size, 2)

    def test_fine_only_scan_is_validated_at_current_position(self):
        self.configure_stage_bounds()
        self.set_scan_settings(
            coarse_selected=False,
            fine_selected=True,
            fine_range=50,
            fine_step_size=5,
            focus_position=995,
        )

        self.assertEqual(
            self.autofocus.get_initial_scan_bounds_error(),
            "The requested fine scan (970 to 1020 µm) exceeds the focus-stage "
            "limits (0 to 1000 µm).",
        )

    def test_combined_fine_scan_is_validated_after_coarse_result(self):
        self.configure_stage_bounds()
        self.set_scan_settings(
            coarse_selected=True,
            coarse_range=5,
            coarse_step_size=5,
            fine_selected=True,
            fine_range=50,
            fine_step_size=5,
            focus_position=500,
        )
        self.autofocus.model.active_microscope.prepare_next_channel = MagicMock()
        self.autofocus.pre_func_signal()
        self.autofocus.signal_id = self.autofocus.coarse_steps
        self.autofocus.model.stop_acquisition = False
        self.autofocus.autofocus_pos_queue.put(995)
        self.autofocus.model.move_stage = MagicMock(return_value=True)

        with self.assertRaisesRegex(
            UserVisibleException,
            r"requested fine scan \(970 to 1020 µm\)",
        ):
            self.autofocus.in_func_signal()

        self.autofocus.model.move_stage.assert_not_called()
        self.assertTrue(self.autofocus.autofocus_frame_queue.empty())

    def test_combined_scan_uses_frozen_fine_settings(self):
        self.configure_stage_bounds(minimum=-1000, maximum=1000)
        self.set_scan_settings(
            coarse_selected=True,
            coarse_range=5,
            coarse_step_size=5,
            fine_selected=True,
            fine_range=20,
            fine_step_size=5,
            focus_position=100,
        )
        model = self.autofocus.model
        model.active_microscope.prepare_next_channel = MagicMock()
        model.stop_acquisition = False
        model.move_stage = MagicMock(return_value=True)
        model.logger = MagicMock()
        self.autofocus.pre_func_signal()
        self.autofocus.signal_id = self.autofocus.coarse_steps
        self.autofocus.autofocus_pos_queue.put(100)
        model.configuration["experiment"]["AutoFocusParameters"]["Mesoscale"]["stage"][
            "f"
        ]["fine_range"] = 0

        self.autofocus.in_func_signal()

        model.move_stage.assert_called_once_with({"f_abs": 90}, wait_until_done=True)

    def test_failed_stage_move_does_not_queue_measurement(self):
        self.autofocus.model.logger = MagicMock()
        self.autofocus.model.move_stage = MagicMock(return_value=False)
        self.autofocus.coarse_positions = (10,)
        self.autofocus.coarse_steps = 1
        self.autofocus.signal_id = 0
        self.autofocus.total_frame_num = 1

        with self.assertRaisesRegex(
            UserVisibleException,
            r"could not move the focus stage to 10 µm",
        ):
            self.autofocus.in_func_signal()

        self.assertTrue(self.autofocus.autofocus_frame_queue.empty())

    def test_successful_stage_move_queues_measurement(self):
        self.autofocus.model.logger = MagicMock()
        self.autofocus.model.move_stage = MagicMock(return_value=True)
        self.autofocus.coarse_positions = (10,)
        self.autofocus.coarse_steps = 1
        self.autofocus.signal_id = 0
        self.autofocus.total_frame_num = 1

        self.autofocus.in_func_signal()

        self.assertEqual(
            self.autofocus.autofocus_frame_queue.get_nowait(),
            (self.autofocus.model.frame_id, 1, 10),
        )

    def test_wait_for_focus_position_stops_after_cancellation(self):
        """A stop request releases an autofocus focus-position handoff."""
        self.autofocus.model.stop_acquisition = False

        def stop_while_waiting(timeout):
            self.assertEqual(timeout, 0.1)
            self.autofocus.model.stop_acquisition = True
            raise Empty

        with patch.object(
            self.autofocus.autofocus_pos_queue,
            "get",
            side_effect=stop_while_waiting,
        ):
            focus_position = self.autofocus._wait_for_focus_position()

        self.assertIsNone(focus_position)

    def test_wait_for_focus_position_returns_available_position(self):
        """An available data-thread focus position passes to the signal thread."""
        self.autofocus.model.stop_acquisition = False
        self.autofocus.autofocus_pos_queue.put(123.4)

        focus_position = self.autofocus._wait_for_focus_position()

        self.assertEqual(focus_position, 123.4)

    def test_in_func_signal_skips_fine_move_when_cancelled(self):
        """Cancellation during the coarse-to-fine handoff performs no further move."""
        self.autofocus.coarse_steps = 5
        self.autofocus.signal_id = 5
        self.autofocus.total_frame_num = 10
        self.autofocus.init_pos = 0.0
        self.autofocus.fine_pos_offset = 1.0
        self.autofocus.fine_step_size = 0.1
        self.autofocus.model.move_stage = MagicMock()

        with patch.object(
            self.autofocus,
            "_wait_for_focus_position",
            return_value=None,
        ):
            result = self.autofocus.in_func_signal()

        self.assertIsNone(result)
        self.autofocus.model.move_stage.assert_not_called()

    def test_in_func_signal_skips_final_move_when_cancelled(self):
        """Cancellation at the final handoff leaves the focus stage untouched."""
        self.autofocus.coarse_steps = 5
        self.autofocus.signal_id = 11
        self.autofocus.total_frame_num = 10
        self.autofocus.model.stop_acquisition = True
        self.autofocus.model.logger = MagicMock()
        self.autofocus.model.move_stage = MagicMock()
        self.autofocus.autofocus_pos_queue.put(123.4)

        result = self.autofocus.in_func_signal()

        self.assertIsNone(result)
        self.autofocus.model.move_stage.assert_not_called()

    def test_run_loads_autofocus_feature_without_preparing_channel(self):
        model = DummyModel()
        model.prepare_acquisition = MagicMock()
        model.active_microscope.prepare_channel = MagicMock()
        model.active_microscope.prepare_next_channel = MagicMock()
        model.run_acquisition = MagicMock()
        model.run_data_process = MagicMock()
        autofocus = Autofocus(
            model=model,
            device="stage",
            device_ref="f",
            target_channel="channel_2",
        )

        with (
            patch(
                "navigate.model.features.autofocus.load_features",
                return_value=(MagicMock(), MagicMock()),
            ) as load_features_mock,
            patch("navigate.model.features.autofocus.threading.Thread") as thread,
        ):
            autofocus.run()

        model.active_microscope.prepare_channel.assert_not_called()
        model.active_microscope.prepare_next_channel.assert_not_called()
        self.assertEqual(thread.return_value.start.call_count, 2)
        feature_args = load_features_mock.call_args.args[1][0]["args"]
        self.assertEqual(
            feature_args[-1],
            {
                "coarse_selected": True,
                "coarse_range": 500.0,
                "coarse_step_size": 50.0,
                "fine_selected": True,
                "fine_range": 50.0,
                "fine_step_size": 5.0,
            },
        )

    def test_pre_func_signal_prepares_requested_channel(self):
        model = DummyModel()
        model.active_microscope.prepare_channel = MagicMock()
        model.active_microscope.prepare_next_channel = MagicMock()
        autofocus = Autofocus(
            model=model,
            device="stage",
            device_ref="f",
            target_channel="channel_2",
        )

        autofocus.pre_func_signal()

        model.active_microscope.prepare_channel.assert_called_once_with("channel_2")
        model.active_microscope.prepare_next_channel.assert_not_called()

    def test_pre_func_signal_prepares_next_channel_without_target_channel(self):
        model = DummyModel()
        model.active_microscope.prepare_channel = MagicMock()
        model.active_microscope.prepare_next_channel = MagicMock()
        autofocus = Autofocus(model=model, device="stage", device_ref="f")

        autofocus.pre_func_signal()

        model.active_microscope.prepare_channel.assert_not_called()
        model.active_microscope.prepare_next_channel.assert_called_once_with()

    def test_end_func_data_reports_best_focus_for_channel(self):
        model = DummyModel()
        model.event_queue = MagicMock()
        model.logger = MagicMock()
        autofocus = Autofocus(
            model=model,
            device="stage",
            device_ref="f",
            target_channel="channel_2",
            calibration_action="populate_defocus",
            reference_channel="channel_1",
        )
        autofocus.get_frames_num = 2
        autofocus.total_frame_num = 1
        autofocus.plot_data = []
        autofocus.focus_pos = 123.4

        autofocus.end_func_data()

        model.event_queue.put.assert_any_call(
            (
                "autofocus_complete",
                {
                    "channel": "channel_2",
                    "focus_position": 123.4,
                    "device": "stage",
                    "device_ref": "f",
                    "calibration_action": "populate_defocus",
                    "reference_channel": "channel_1",
                    "set_defocus_for_all_flag": False,
                },
            )
        )

    def test_in_func_data_publishes_defensive_progress_snapshots(self):
        model = self.autofocus.model
        model.autofocus_progress_queue = MagicMock()
        model.logger = MagicMock()
        self.autofocus.pre_func_data()
        self.autofocus.total_frame_num = 2
        self.autofocus.autofocus_frame_queue.put((0, 2, 10.0))
        self.autofocus.autofocus_frame_queue.put((1, 1, 20.0))

        with patch(
            "navigate.model.features.autofocus.fast_normalized_dct_shannon_entropy",
            side_effect=(np.array([1.0]), np.array([2.0])),
        ):
            self.autofocus.in_func_data([0, 1])

        progress_calls = [
            call for call in model.autofocus_progress_queue.put_nowait.call_args_list
        ]
        self.assertEqual(
            progress_calls,
            [
                unittest.mock.call([[10.0, 1.0]]),
                unittest.mock.call([[10.0, 1.0], [20.0, 2.0]]),
            ],
        )

        self.autofocus.plot_data[0][1] = 999.0
        self.assertEqual(progress_calls[0].args[0], [[10.0, 1.0]])

    def test_full_progress_queue_replaces_stale_snapshot_without_blocking_events(self):
        model = self.autofocus.model
        model.event_queue = MagicMock()
        model.autofocus_progress_queue = MagicMock()
        model.autofocus_progress_queue.put_nowait.side_effect = [Full, None]
        model.autofocus_progress_queue.get_nowait.return_value = [[0.0, 0.0]]
        model.logger = MagicMock()
        self.autofocus.pre_func_data()
        self.autofocus.total_frame_num = 2
        self.autofocus.autofocus_frame_queue.put((0, 2, 10.0))

        with patch(
            "navigate.model.features.autofocus.fast_normalized_dct_shannon_entropy",
            return_value=np.array([1.0]),
        ):
            self.autofocus.in_func_data([0])

        self.assertEqual(self.autofocus.plot_data, [[10.0, 1.0]])
        model.autofocus_progress_queue.get_nowait.assert_called_once_with()
        self.assertEqual(
            model.autofocus_progress_queue.put_nowait.call_args_list,
            [
                unittest.mock.call([[10.0, 1.0]]),
                unittest.mock.call([[10.0, 1.0]]),
            ],
        )
        model.event_queue.put_nowait.assert_not_called()


if __name__ == "__main__":
    unittest.main()
