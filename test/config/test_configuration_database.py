# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

from navigate.config.configuration_database import (
    camera_hardware_widgets,
    daq_hardware_widgets,
    hardware_wizard_metadata,
    stage_hardware_widgets,
)


def test_daq_hardware_widgets_include_trigger_reset_count():
    widget = daq_hardware_widgets["trigger_reset_count"]

    assert widget[0] == "Trigger Reset Count"
    assert widget[1] == "Input"
    assert widget[2] == "int"
    assert widget[3] is None
    assert "0" in widget[4]
    assert "disabled" in widget[4]
    assert "unstable" in widget[4]


def test_hardware_wizard_metadata_has_shell_for_every_hardware_tab():
    expected_tabs = {
        "Camera",
        "Data Acquisition Card",
        "Filter Wheel",
        "Galvo",
        "Lasers",
        "Remote Focus Devices",
        "Adaptive Optics",
        "Shutters",
        "Stages",
        "Zoom Device",
    }
    assert set(hardware_wizard_metadata) == expected_tabs


def test_camera_wizard_metadata_covers_all_fields():
    fields = hardware_wizard_metadata["Camera"]["fields"]
    expected_field_keys = {
        key
        for key, value in camera_hardware_widgets.items()
        if key != "frame_config" and value[1] not in {"Button", "Label"}
    }
    assert set(fields) == expected_field_keys
    assert hardware_wizard_metadata["Camera"]["device_field"] == "hardware/type"
    assert fields["hardware/type"]["importance"] == "required"
    assert fields["hardware/camera_connection"]["applies_to"] == [
        "Photometrics Iris 15B"
    ]


def test_daq_wizard_metadata_covers_all_fields():
    fields = hardware_wizard_metadata["Data Acquisition Card"]["fields"]
    expected_field_keys = {
        key
        for key, value in daq_hardware_widgets.items()
        if key != "frame_config" and value[1] not in {"Button", "Label"}
    }
    assert set(fields) == expected_field_keys
    assert fields["sample_rate"]["importance"] == "required"
    assert fields["trigger_reset_count"]["importance"] == "advanced"


def test_stage_wizard_metadata_covers_all_fields():
    fields = hardware_wizard_metadata["Stages"]["fields"]
    expected_field_keys = {
        key
        for key, value in stage_hardware_widgets.items()
        if key != "frame_config" and value[1] not in {"Button", "Label"}
    }
    assert set(fields) == expected_field_keys
    assert hardware_wizard_metadata["Stages"]["device_field"] == "type"
    assert fields["volts_per_micron"]["applies_to"] == ["NI Analog/Digital Device"]
    assert fields["controllername"]["applies_to"] == ["Physik Instrumente"]
