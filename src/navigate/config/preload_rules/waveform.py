# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

from multiprocessing.managers import DictProxy

from navigate.config.config import update_config_dict
from navigate.config.preload import PreloadContext, PreloadRule


def ensure_waveform_constants_root(context: PreloadContext) -> None:
    """Ensure waveform constants root is a shared dictionary."""
    if type(context.configuration["waveform_constants"]) is not DictProxy:
        update_config_dict(
            context.manager, context.configuration, "waveform_constants", {}
        )


def repair_remote_focus_constants(context: PreloadContext) -> None:
    """Verify remote-focus waveform constants."""
    manager = context.manager
    configuration = context.configuration
    waveform_root = configuration["waveform_constants"]
    if (
        "remote_focus_constants" not in waveform_root.keys()
        or type(waveform_root["remote_focus_constants"]) is not DictProxy
    ):
        update_config_dict(manager, waveform_root, "remote_focus_constants", {})

    waveform_dict = waveform_root["remote_focus_constants"]
    for microscope_name in configuration["configuration"]["microscopes"].keys():
        config_dict = configuration["configuration"]["microscopes"][microscope_name]
        if (
            microscope_name not in waveform_dict.keys()
            or type(waveform_dict[microscope_name]) is not DictProxy
        ):
            update_config_dict(manager, waveform_dict, microscope_name, {})

        lasers = []
        for laser in config_dict["laser"]:
            laser_wavelength = f"{laser['wavelength']}nm"
            lasers.append(laser_wavelength)

        for zoom in config_dict["zoom"]["position"].keys():
            if (
                zoom not in waveform_dict[microscope_name].keys()
                or type(waveform_dict[microscope_name][zoom]) is not DictProxy
            ):
                update_config_dict(manager, waveform_dict[microscope_name], zoom, {})

            for laser in lasers:
                if (
                    laser not in waveform_dict[microscope_name][zoom].keys()
                    or type(waveform_dict[microscope_name][zoom][laser])
                    is not DictProxy
                ):
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name][zoom],
                        laser,
                        {
                            "amplitude": 0,
                            "offset": 0,
                        },
                    )
                else:
                    for k in [
                        "amplitude",
                        "offset",
                    ]:
                        if k not in waveform_dict[microscope_name][zoom][laser].keys():
                            waveform_dict[microscope_name][zoom][laser][k] = (
                                config_dict["remote_focus"].get(k, "0")
                            )
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][laser][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][laser][k] = (
                                    config_dict["remote_focus"].get(k, "0")
                                )

            for k in list(waveform_dict[microscope_name][zoom].keys()):
                if k not in lasers:
                    waveform_dict[microscope_name][zoom].pop(k)

        for k in list(waveform_dict[microscope_name].keys()):
            if k not in config_dict["zoom"]["position"].keys():
                waveform_dict[microscope_name].pop(k)

    for k in list(waveform_dict.keys()):
        if k not in configuration["configuration"]["microscopes"].keys():
            waveform_dict.pop(k)


def repair_galvo_constants(context: PreloadContext) -> None:
    """Verify galvo waveform constants."""
    manager = context.manager
    configuration = context.configuration
    waveform_root = configuration["waveform_constants"]
    if (
        "galvo_constants" not in waveform_root.keys()
        or type(waveform_root["galvo_constants"]) is not DictProxy
    ):
        update_config_dict(manager, waveform_root, "galvo_constants", {})

    waveform_dict = waveform_root["galvo_constants"]
    galvo_num = 0
    for microscope_name in configuration["configuration"]["microscopes"].keys():
        galvo_num = max(
            galvo_num,
            len(
                configuration["configuration"]["microscopes"][microscope_name]["galvo"]
            ),
        )

    for i in range(galvo_num):
        waveform_dict = configuration["waveform_constants"]["galvo_constants"]
        galvo_ref = f"Galvo {i}"
        if (
            galvo_ref not in waveform_dict.keys()
            or type(waveform_dict[galvo_ref]) is not DictProxy
        ):
            update_config_dict(manager, waveform_dict, galvo_ref, {})
        waveform_dict = waveform_dict[galvo_ref]
        for microscope_name in configuration["configuration"]["microscopes"].keys():
            if (
                len(
                    configuration["configuration"]["microscopes"][microscope_name][
                        "galvo"
                    ]
                )
                <= i
            ):
                continue
            config_dict = configuration["configuration"]["microscopes"][microscope_name]
            if (
                microscope_name not in waveform_dict.keys()
                or type(waveform_dict[microscope_name]) is not DictProxy
            ):
                update_config_dict(manager, waveform_dict, microscope_name, {})

            galvo_config = {
                "amplitude": "0",
                "offset": 0,
                "rising_ramp": 50,
                "frequency": 10,
            }
            for zoom in config_dict["zoom"]["position"].keys():
                if (
                    zoom not in waveform_dict[microscope_name].keys()
                    or type(waveform_dict[microscope_name][zoom]) is not DictProxy
                ):
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name],
                        zoom,
                        galvo_config,
                    )
                else:
                    for k in galvo_config.keys():
                        if k not in waveform_dict[microscope_name][zoom].keys():
                            waveform_dict[microscope_name][zoom][k] = config_dict[
                                "galvo"
                            ][i].get(k, galvo_config[k])
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][k] = config_dict[
                                    "galvo"
                                ][i].get(k, "0")
            for k in list(waveform_dict[microscope_name].keys()):
                if k not in config_dict["zoom"]["position"].keys():
                    waveform_dict[microscope_name].pop(k)
        for k in list(waveform_dict.keys()):
            if k not in configuration["configuration"]["microscopes"].keys():
                waveform_dict.pop(k)


def repair_other_constants(context: PreloadContext) -> None:
    """Verify miscellaneous waveform constants."""
    manager = context.manager
    configuration = context.configuration
    waveform_dict = configuration["waveform_constants"]
    microscope_name = configuration["configuration"]["microscopes"].keys()[0]
    camera_config = configuration["configuration"]["microscopes"][microscope_name][
        "camera"
    ]
    other_constants_dict = {
        "remote_focus_settle_duration": "0",
        "percent_smoothing": "0",
        "remote_focus_delay": "0",
        "remote_focus_ramp_falling": "5",
        "camera_settle_duration": "0",
        "camera_delay": camera_config.get(
            "delay", camera_config.get("delay_percent", "1.0")
        ),
    }
    if (
        "other_constants" not in waveform_dict.keys()
        or type(waveform_dict["other_constants"]) is not DictProxy
    ):
        update_config_dict(
            manager,
            waveform_dict,
            "other_constants",
            other_constants_dict,
        )
    for k in other_constants_dict.keys():
        try:
            float(waveform_dict["other_constants"][k])
        except (ValueError, KeyError):
            waveform_dict["other_constants"][k] = other_constants_dict[k]


WAVEFORM_CONSTANTS_RULES = [
    PreloadRule("waveform_constants", "root", ensure_waveform_constants_root),
    PreloadRule(
        "waveform_constants",
        "remote_focus_constants",
        repair_remote_focus_constants,
    ),
    PreloadRule("waveform_constants", "galvo_constants", repair_galvo_constants),
    PreloadRule("waveform_constants", "other_constants", repair_other_constants),
]
