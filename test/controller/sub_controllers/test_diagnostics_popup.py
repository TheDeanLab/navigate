# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def diagnostics_controller(dummy_view, dummy_controller):
    from navigate.view.popups.diagnostics_popup import DiagnosticsPopup
    from navigate.controller.sub_controllers import diagnostics_popup as diag_module

    with patch.object(diag_module, "load_performance_log", return_value=[]):
        popup = DiagnosticsPopup(dummy_view)
        controller = diag_module.DiagnosticsPopupController(popup, dummy_controller)

    yield controller

    try:
        if controller.view.popup.winfo_exists():
            controller.view.popup.destroy()
    except Exception:
        pass


def test_extract_times_filters_by_kind():
    from navigate.controller.sub_controllers.diagnostics_popup import (
        DiagnosticsPopupController,
    )

    log_content = [
        {"kind": "Acquire Image", "duration_ns": 1_000_000_000},
        {"kind": "Acquire Image", "duration_ns": 2_000_000_000},
        {"kind": "Histogram", "duration_ns": 500_000_000},
    ]

    times = DiagnosticsPopupController.extract_times(
        log_content, kind="Acquire Image"
    )
    assert times == pytest.approx([1.0, 2.0])

    assert DiagnosticsPopupController.extract_times(
        log_content, kind="Missing"
    ) is None
    assert DiagnosticsPopupController.extract_times(None, kind="Acquire Image") is None
    assert DiagnosticsPopupController.extract_times("bad", kind="Acquire Image") is None


def test_reset_plots_sets_timestamp_and_calls_populate(diagnostics_controller):
    controller = diagnostics_controller

    with patch(
        "navigate.controller.sub_controllers.diagnostics_popup.time.time",
        return_value=123.0,
    ):
        controller.populate_plots = MagicMock()
        controller.reset_plots()

    assert controller.reset_timestamp == 123.0
    controller.populate_plots.assert_called_once()


def test_filter_log_since_reset(diagnostics_controller):
    controller = diagnostics_controller
    controller.reset_timestamp = 100.0

    log_content = [
        {"timestamp": 50, "kind": "Acquire Image", "duration_ns": 1},
        {"timestamp": 100, "kind": "Acquire Image", "duration_ns": 2},
        {"timestamp": 150, "kind": "Acquire Image", "duration_ns": 3},
        "bad",
        {"kind": "Acquire Image", "duration_ns": 4},
    ]

    filtered = controller._filter_log_since_reset(log_content)
    assert filtered == [
        {"timestamp": 100, "kind": "Acquire Image", "duration_ns": 2},
        {"timestamp": 150, "kind": "Acquire Image", "duration_ns": 3},
    ]


def test_populate_plots_handles_no_data(diagnostics_controller):
    from navigate.controller.sub_controllers import diagnostics_popup as diag_module

    with patch.object(diag_module, "load_performance_log", return_value=None):
        diagnostics_controller.populate_plots()


def test_close_popup_removes_controller(diagnostics_controller, dummy_controller):
    dummy_controller.diagnostics_controller = diagnostics_controller
    diagnostics_controller.close_popup()
    assert not hasattr(dummy_controller, "diagnostics_controller")
