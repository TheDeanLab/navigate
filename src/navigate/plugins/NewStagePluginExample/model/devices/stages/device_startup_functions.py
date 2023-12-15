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
#
import importlib
from multiprocessing.managers import ListProxy

from navigate.model.device_startup_functions import (
    auto_redial,
    device_not_found,
    DummyDeviceConnection,
)

DEVICE_TYPE_NAME = "stage"  # Same as in configuraion.yaml, for example "stage", "filter_wheel", "remote_focus_device"...
DEVICE_REF_LIST = [
    "type",
    "serial_number",
]  # the reference value from configuration.yaml


def load_device(configuration, is_synthetic=False):
    return DummyDeviceConnection()


def start_device(microscope_name, device_connection, configuration, id=0):
    device_config = configuration["configuration"]["microscopes"][microscope_name][
        "stage"
    ]["hardware"]

    if type(device_config) == ListProxy:
        device_type = device_config[id]["type"]
    else:
        device_type = device_config["type"]

    if device_type == "CustomStage":
        custom_device = importlib.import_module(
            "navigate.plugins.NewStagePluginExample.model.devices.stages.custom_stage"
        )
        return custom_device.CustomStage(
            microscope_name, device_connection, configuration, id
        )
    else:
        device_not_found(microscope_name, device_type)
