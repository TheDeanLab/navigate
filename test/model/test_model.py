# Copyright (c) 2021-2023  The University of Texas Southwestern Medical Center.
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
import random
import pytest
import os
from multiprocessing import Manager

# from time import sleep

manager = Manager()


@pytest.fixture(scope="module")
def model():
    from types import SimpleNamespace
    from pathlib import Path

    from aslm.model.model import Model
    from multiprocessing import Queue
    from aslm.config.config import (
        load_configs,
        verify_experiment_config,
        verify_waveform_constants,
    )

    # Use configuration files that ship with the code base
    configuration_directory = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "src", "aslm", "config"
    )
    configuration_path = Path.joinpath(configuration_directory, "configuration.yaml")
    experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
    waveform_constants_path = Path.joinpath(
        configuration_directory, "waveform_constants.yml"
    )
    rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")

    event_queue = Queue()

    configuration = load_configs(
        manager,
        configuration=configuration_path,
        experiment=experiment_path,
        waveform_constants=waveform_constants_path,
        rest_api_config=rest_api_path,
    )
    verify_experiment_config(manager, configuration)
    verify_waveform_constants(manager, configuration)

    model = Model(
        args=SimpleNamespace(synthetic_hardware=True),
        configuration=configuration,
        event_queue=event_queue,
    )

    yield model
    while not event_queue.empty():
        event_queue.get()
    event_queue.close()
    event_queue.join_thread()


def test_single_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "single"
    state["is_save"] = False

    n_frames = state["selected_channels"]

    show_img_pipe = model.create_pipe("show_img_pipe")

    model.run_command("acquire")

    image_id = show_img_pipe.recv()
    n_images = 0
    max_iters = 10
    while image_id != "stop" and max_iters > 0:
        image_id = show_img_pipe.recv()
        n_images += 1
        max_iters -= 1

    assert n_images == n_frames
    model.data_thread.join()
    model.release_pipe("show_img_pipe")


def test_multiposition_acquisition(model):
    """Test that the multiposition acquisition works as expected.

    This test is meant to confirm that if the multi position check box is set,
    but there aren't actually any positions in the multi-position table, that the
    acquisition proceeds as if it is not a multi position acquisition.

    Sleep statements are used to ensure that the event queue has ample opportunity to
    be populated with the disable_multiposition event. This is because the event queue
    is a multiprocessing.Queue, which is not thread safe.
    """
    from aslm.config.config import update_config_dict

    state = model.configuration["experiment"]["MicroscopeState"]

    # def check_queue(event, event_queue):
    #     """Check if the event queue contains the event. If it does, return True.
    #     Otherwise, return False.
    #
    #     Parameters
    #     ----------
    #     event : str
    #         The event to check for in the event queue.
    #     event_queue : multiprocessing.Queue
    #         The event queue to check.
    #     """
    #     while not event_queue.empty():
    #         ev, _ = event_queue.get()
    #         if ev == event:
    #             return True
    #     return False

    # Multiposition is selected and actually is True
    state["is_multiposition"] = True
    update_config_dict(
        manager,
        model.configuration["experiment"],
        "MultiPositions",
        {"x": 10.0, "y": 10.0, "z": 10.0, "theta": 10.0, "f": 10.0},
    )
    model.run_command("acquire")
    # sleep(1)
    # assert (
    #     check_queue(event="disable_multiposition", event_queue=model.event_queue)
    #     is False
    # )
    assert state["is_multiposition"] is True

    # Multiposition is selected but not actually  True
    update_config_dict(manager, model.configuration["experiment"], "MultiPositions", [])
    model.run_command("acquire")
    # sleep(1)
    # # Check that the event queue is called with the disable_multiposition statement
    # assert (
    #     check_queue(event="disable_multiposition", event_queue=model.event_queue)
    #     is True
    # )
    assert state["is_multiposition"] is False


def test_change_resolution(model):
    """
    Note: The stage position check is an absolute mess due to us instantiating two
    SyntheticStages--one for each microsocpe. We have to continuously reset the
    stage positions to all zeros and make the configuration.yaml that comes with the
    software have negative stage bounds.
    """
    scopes = random.choices(
        model.configuration["configuration"]["microscopes"].keys(), k=10
    )
    zooms = [
        random.choice(
            model.configuration["configuration"]["microscopes"][scope]["zoom"][
                "position"
            ].keys()
        )
        for scope in scopes
    ]
    axes = ["x", "y", "z", "theta", "f"]

    for scope, zoom in zip(scopes, zooms):
        # reset stage axes to all zeros, to match default SyntheticStage behaviour
        for microscope in model.microscopes:
            for ax in axes:
                model.microscopes[microscope].stages[ax].move_absolute(
                    {ax + "_abs": 0}, wait_until_done=True
                )

        former_offset_dict = model.configuration["configuration"]["microscopes"][
            model.configuration["experiment"]["MicroscopeState"]["microscope_name"]
        ]["stage"]
        former_pos_dict = model.get_stage_position()
        former_zoom = model.configuration["experiment"]["MicroscopeState"]["zoom"]
        model.active_microscope.zoom.set_zoom(former_zoom)
        print(f"{model.active_microscope_name}: {former_pos_dict}")

        print(
            f"CHANGING {model.active_microscope_name} at "
            f'{model.configuration["experiment"]["MicroscopeState"]["zoom"]} to {scope}'
            f" at {zoom}"
        )
        model.configuration["experiment"]["MicroscopeState"]["microscope_name"] = scope
        model.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
        solvent = model.configuration["experiment"]["Saving"]["solvent"]

        model.change_resolution(scope)

        self_offset_dict = model.configuration["configuration"]["microscopes"][scope][
            "stage"
        ]
        pos_dict = model.get_stage_position()

        print(f"{model.active_microscope_name}: {pos_dict}")

        # reset stage axes to all zeros, to match default SyntheticStage behaviour
        for ax in model.active_microscope.stages:
            print(f"axis {ax}")
            try:
                shift_ax = float(
                    model.active_microscope.zoom.stage_offsets[solvent][ax][
                        former_zoom
                    ][zoom]
                )
                print(f"shift_ax {shift_ax}")
            except (TypeError, KeyError):
                shift_ax = 0
            assert (
                pos_dict[ax + "_pos"]
                - self_offset_dict[ax + "_offset"]
                + former_offset_dict[ax + "_offset"]
                - shift_ax
            ) == 0

        assert model.active_microscope_name == scope
        assert model.active_microscope.zoom.zoomvalue == zoom


def test_get_feature_list(model):
    feature_lists = model.feature_list

    assert model.get_feature_list(0) == ""
    assert model.get_feature_list(len(feature_lists) + 1) == ""

    from aslm.model.features.feature_related_functions import (
        convert_str_to_feature_list,
    )

    for i in range(len(feature_lists)):
        feature_str = model.get_feature_list(i + 1)
        if "shared_list" not in feature_str:
            assert convert_str_to_feature_list(feature_str) == feature_lists[i]


def test_load_feature_list_from_str(model):
    feature_lists = model.feature_list

    l = len(feature_lists)  # noqa
    model.load_feature_list_from_str('[{"name": PrepareNextChannel}]')
    assert len(feature_lists) == l + 1
    from aslm.model.features.feature_related_functions import (
        convert_feature_list_to_str,
    )

    assert (
        convert_feature_list_to_str(feature_lists[-1])
        == '[{"name": PrepareNextChannel,},]'
    )
    del feature_lists[-1]
    feature_str = '[{"name": LoopByCount,"args": ([1, 2.0, True, False, \'abc\'],)},]'
    model.load_feature_list_from_str(feature_str)
    assert len(feature_lists) == l + 1
    assert convert_feature_list_to_str(feature_lists[-1]) == feature_str
    del feature_lists[-1]


def test_load_feature_records(model):
    feature_lists = model.feature_list
    l = len(feature_lists)  # noqa

    from aslm.config.config import get_aslm_path
    from aslm.tools.file_functions import save_yaml_file, load_yaml_file
    from aslm.model.features.feature_related_functions import (
        convert_feature_list_to_str,
    )

    feature_lists_path = get_aslm_path() + "/feature_lists"

    if not os.path.exists(feature_lists_path):
        os.makedirs(feature_lists_path)
    save_yaml_file(
        feature_lists_path,
        {
            "module_name": None,
            "feature_list_name": "Test Feature List 1",
            "feature_list": "[({'name': PrepareNextChannel}, "
            "{'name': LoopByCount, 'args': (3,)})]",
        },
        "__test_1.yml",
    )

    model.load_feature_records()
    assert len(feature_lists) == l + 1
    assert (
        convert_feature_list_to_str(feature_lists[-1])
        == '[({"name": PrepareNextChannel,},{"name": LoopByCount,"args": (3,)},),]'
    )

    del feature_lists[-1]
    os.remove(f"{feature_lists_path}/__test_1.yml")

    model.load_feature_records()
    assert len(feature_lists) == l
    feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
    assert feature_records == []
    os.remove(f"{feature_lists_path}/__sequence.yml")
