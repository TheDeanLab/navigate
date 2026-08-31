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

# Standard Library Imports
import random
import pytest
import os
from queue import Queue
from types import SimpleNamespace
from typing import Any, Iterable, Iterator, Optional
from multiprocessing import Manager
from unittest.mock import MagicMock, patch
import multiprocessing

# Third Party Imports

# Local Imports

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def _receive_last_frame_id(show_img_pipe: Any, max_messages: int = 20) -> Optional[int]:
    last_frame_id = None
    for _ in range(max_messages):
        message = show_img_pipe.recv()
        if message == "stop":
            break
        if isinstance(message, int):
            last_frame_id = message
    return last_frame_id


class FakeReadablePipe:
    def __init__(self, messages: Iterable[Any]) -> None:
        self.messages: Iterator[Any] = iter(messages)

    def recv(self) -> Any:
        return next(self.messages)


def test_receive_last_frame_id_handles_coalesced_batches() -> None:
    show_img_pipe = FakeReadablePipe([0, 2, "stop"])

    assert _receive_last_frame_id(show_img_pipe) == 2


@pytest.fixture(scope="module")
def model():
    from logging import NullHandler
    from logging.handlers import QueueListener
    from types import SimpleNamespace
    from pathlib import Path

    from navigate.model.model import Model
    from navigate.config.config import (
        load_configs,
        verify_experiment_config,
        verify_waveform_constants,
        verify_configuration,
        verify_positions_config,
    )
    from navigate.log_files.log_functions import log_setup
    from navigate.tools.file_functions import load_yaml_file

    with Manager() as manager:

        # Use configuration files that ship with the code base
        configuration_directory = Path.joinpath(
            Path(__file__).resolve().parent.parent.parent,
            "src",
            "navigate",
            "config",
        )
        configuration_path = Path.joinpath(
            configuration_directory, "configuration.yaml"
        )
        experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
        waveform_constants_path = Path.joinpath(
            configuration_directory, "waveform_constants.yml"
        )
        gui_configuration_path = Path.joinpath(
            configuration_directory, "gui_configuration.yml"
        )
        rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")
        multi_positions_path = Path.joinpath(
            configuration_directory, "multi_positions.yml"
        )

        event_queue = MagicMock()

        configuration = load_configs(
            manager,
            configuration=configuration_path,
            experiment=experiment_path,
            waveform_constants=waveform_constants_path,
            rest_api_config=rest_api_path,
            gui=gui_configuration_path,
        )
        verify_configuration(manager, configuration)
        verify_experiment_config(manager, configuration)
        verify_waveform_constants(manager, configuration)

        positions = load_yaml_file(multi_positions_path)
        positions = verify_positions_config(positions)
        configuration["multi_positions"] = positions

        log_queue = multiprocessing.Queue()
        log_listener = QueueListener(log_queue, NullHandler())
        log_listener.start()

        model = Model(
            args=SimpleNamespace(synthetic_hardware=True),
            configuration=configuration,
            event_queue=event_queue,
            log_queue=log_queue,
        )

        model.__test_manager = manager

        yield model
        # Restore file handlers before closing the queue-backed handlers.
        log_setup("logging.yml")
        log_listener.stop()
        log_queue.close()
        log_queue.join_thread()


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_single_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "single"
    state["is_save"] = False

    n_frames_expected = len(
        list(filter(lambda channel: channel["is_selected"], state["channels"].values()))
    )

    show_img_pipe = model.create_pipe("show_img_pipe")
    try:
        model.run_command("acquire")
        last_frame_id = _receive_last_frame_id(show_img_pipe)
        assert last_frame_id == n_frames_expected - 1
    finally:
        if model.data_thread is not None:
            model.data_thread.join()
        model.release_pipe("show_img_pipe")


def test_run_acquisition_marks_finite_signal_completion_for_data_thread():
    from navigate.model.model import Model

    model = SimpleNamespace(
        signal_container=SimpleNamespace(end_flag=False, is_closed=False),
        stop_send_signal=False,
        stop_acquisition=False,
        imaging_mode="single",
        is_data_thread_on=True,
        logger=MagicMock(),
    )

    def snap_image():
        model.signal_container.end_flag = True

    model.snap_image = snap_image

    Model.run_acquisition(model)

    assert model.stop_acquisition is True
    assert model.signal_acquisition_complete is True


def test_run_data_process_drains_pending_frames_after_signal_completion():
    from navigate.model.model import Model

    class FakeCamera:
        def __init__(self):
            self.frames = [[0, 1, 2]]

        def get_new_frame(self):
            return self.frames.pop(0)

    class FakeDataContainer:
        root = object()
        is_closed = False

        def __init__(self):
            self.end_flag = False
            self.received_frames = []

        def run(self, frame_ids):
            self.received_frames.extend(frame_ids)
            self.end_flag = True

    class FakePipe:
        def __init__(self):
            self.sent = []

        def send(self, value):
            self.sent.append(value)

    data_container = FakeDataContainer()
    show_img_pipe = FakePipe()
    model = SimpleNamespace(
        active_microscope=SimpleNamespace(camera=FakeCamera()),
        ask_to_pause_data_thread=False,
        camera_wait_iterations=1,
        data_container=data_container,
        event_queue=MagicMock(),
        imaging_mode="single",
        logger=MagicMock(),
        pause_data_ready_lock=MagicMock(locked=MagicMock(return_value=False)),
        show_img_pipe=show_img_pipe,
        signal_acquisition_complete=True,
        stop_acquisition=True,
    )
    model.end_acquisition = MagicMock()
    model._should_drain_signal_completed_frames = (
        Model._should_drain_signal_completed_frames.__get__(model, type(model))
    )

    Model.run_data_process(model)

    assert data_container.received_frames == [0, 1, 2]
    assert show_img_pipe.sent == [2, "stop"]


def test_live_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "live"
    selected_channels = [
        ch for ch in state["channels"].values() if ch.get("is_selected", False)
    ]
    multi_channel = len(selected_channels) > 1

    n_images = 0
    seen_channels = set()

    show_img_pipe = model.create_pipe("show_img_pipe")

    model.run_command("acquire")

    while True:
        image_id = show_img_pipe.recv()
        if image_id == "stop":
            break
        channel_id = model.active_microscope.current_channel
        seen_channels.add(channel_id)
        n_images += 1
        if n_images >= 30:
            model.run_command("stop")
    if multi_channel:
        assert len(seen_channels) > 1
    model.data_thread.join()
    model.release_pipe("show_img_pipe")


def test_autofocus_live_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "live"
    selected_channels = [
        ch for ch in state["channels"].values() if ch.get("is_selected", False)
    ]
    multi_channel = len(selected_channels) > 1

    n_images = 0
    seen_channels = set()

    show_img_pipe = model.create_pipe("show_img_pipe")

    model.run_command("acquire")

    while True:
        image_id = show_img_pipe.recv()
        if image_id == "stop":
            break
        channel_id = model.active_microscope.current_channel
        seen_channels.add(channel_id)
        n_images += 1
        if n_images >= 100:
            model.run_command("stop")
        elif n_images == 30:
            model.run_command("autofocus")

    model.data_thread.join()
    model.release_pipe("show_img_pipe")
    if multi_channel:
        assert len(seen_channels) > 1


def test_autofocus_live_injection_preserves_channel_args(model):
    original_is_acquiring = model.is_acquiring
    original_imaging_mode = model.imaging_mode
    original_signal_container = getattr(model, "signal_container", None)
    original_data_container = getattr(model, "data_container", None)
    model.is_acquiring = True
    model.imaging_mode = "live"
    model.signal_container = MagicMock()
    model.data_container = MagicMock()

    try:
        with patch(
            "navigate.model.model.load_features",
            return_value=(MagicMock(), MagicMock()),
        ) as load_features:
            model.run_command(
                "autofocus",
                "stage",
                "f",
                "channel_2",
                "capture_reference",
                "channel_2",
            )

        feature_spec = load_features.call_args.args[1]
        assert feature_spec[0]["name"].__name__ == "Autofocus"
        assert feature_spec[0]["args"] == (
            "stage",
            "f",
            "channel_2",
            "capture_reference",
            "channel_2",
        )
    finally:
        model.is_acquiring = original_is_acquiring
        model.imaging_mode = original_imaging_mode
        model.signal_container = original_signal_container
        model.data_container = original_data_container


def test_reset_feature_list_reports_injected_autofocus_completion(model):
    """Restoring live features reports completion of the injected sequence."""
    original_event_queue = model.event_queue
    original_signal_container = getattr(model, "signal_container", None)
    original_data_container = getattr(model, "data_container", None)
    model.event_queue = Queue()
    model.signal_container = MagicMock()
    model.data_container = MagicMock()
    model.data_container.end_flag = True
    model.injected_flag.value = True

    try:
        with patch(
            "navigate.model.model.load_features",
            return_value=(MagicMock(), MagicMock()),
        ):
            model.reset_feature_list()

        assert model.event_queue.get_nowait() == (
            "autofocus_sequence_complete",
            None,
        )
        assert model.injected_flag.value is False
    finally:
        model.event_queue = original_event_queue
        model.signal_container = original_signal_container
        model.data_container = original_data_container


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test hangs entire workflow on GitHub.")
def test_multiposition_acquisition(model):
    """Test that the multiposition acquisition works as expected.

    This test is meant to confirm that if the multi position check box is set,
    but there aren't actually any positions in the multi-position table, that the
    acquisition proceeds as if it is not a multi position acquisition.

    Sleep statements are used to ensure that the event queue has ample opportunity to
    be populated with the disable_multiposition event. This is because the event queue
    is a multiprocessing.Queue, which is not thread safe.
    """
    # from time import sleep
    from navigate.config.config import update_config_dict

    # def check_queue(event, event_queue):
    #     """Check if the event queue contains the event. If it does, return True.
    #     Otherwise, return False.

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

    _ = model.create_pipe("show_img_pipe")

    # Multiposition is selected and actually is True
    model.configuration["experiment"]["MicroscopeState"]["is_multiposition"] = True
    update_config_dict(
        model.__test_manager,  # noqa
        model.configuration,
        "multi_positions",
        [["X", "Y", "Z", "THETA", "F"], [10.0, 10.0, 10.0, 10.0, 10.0]],
    )
    model.configuration["experiment"]["MicroscopeState"]["image_mode"] = "z-stack"
    model.configuration["experiment"]["MicroscopeState"]["number_z_steps"] = 10

    model.configuration["experiment"]["MicroscopeState"]["step_size"] = 5.0
    model.configuration["experiment"]["MicroscopeState"]["end_position"] = (
        model.configuration["experiment"]["MicroscopeState"]["start_position"] + 15.0
    )
    model.run_command("acquire")

    # sleep(1)
    # assert (
    #     check_queue(event="disable_multiposition", event_queue=model.event_queue)
    #     is False
    # )
    assert (
        model.configuration["experiment"]["MicroscopeState"]["is_multiposition"] is True
    )
    model.data_thread.join()

    # Multiposition is selected but not actually  True
    update_config_dict(
        model.__test_manager,
        model.configuration,
        "multi_positions",
        [],  # noqa
    )

    model.run_command("acquire")
    # sleep(1)
    # # Check that the event queue is called with the disable_multiposition statement
    # assert (
    #     check_queue(event="disable_multiposition", event_queue=model.event_queue)
    #     is True
    # )
    assert (
        model.configuration["experiment"]["MicroscopeState"]["is_multiposition"]
        is False
    )
    model.data_thread.join()
    model.release_pipe("show_img_pipe")


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

    from navigate.model.features.feature_related_functions import (
        convert_feature_list_to_str,
    )

    for i in range(len(feature_lists)):
        feature_str = model.get_feature_list(i + 1)
        if "shared_list" not in feature_str:
            assert feature_str == convert_feature_list_to_str(feature_lists[i])
            # assert convert_str_to_feature_list(feature_str) == feature_lists[i]


def test_load_feature_list_from_str(model):
    feature_lists = model.feature_list

    l = len(feature_lists)  # noqa
    model.load_feature_list_from_str('[{"name": PrepareNextChannel}]')
    assert len(feature_lists) == l + 1
    from navigate.model.features.feature_related_functions import (
        convert_feature_list_to_str,
    )

    assert (
        convert_feature_list_to_str(feature_lists[-1])
        == '[{"name": PrepareNextChannel,},]'
    )
    del feature_lists[-1]
    feature_str = '[{"name": LoopByCount,"args": ([1, 2.0, True, False, \'abc\'],),},]'
    model.load_feature_list_from_str(feature_str)
    assert len(feature_lists) == l + 1
    assert convert_feature_list_to_str(feature_lists[-1]) == feature_str
    del feature_lists[-1]


def test_load_feature_records(model, tmp_path, monkeypatch):
    feature_lists = model.feature_list
    l = len(feature_lists)  # noqa

    from navigate.tools.file_functions import save_yaml_file, load_yaml_file
    from navigate.model.features.feature_related_functions import (
        convert_feature_list_to_str,
    )

    navigate_home = tmp_path / "navigate_home"
    monkeypatch.setattr(
        "navigate.model.model.get_navigate_path",
        lambda: str(navigate_home),
    )
    feature_lists_path = navigate_home / "feature_lists"

    if not os.path.exists(feature_lists_path):
        os.makedirs(feature_lists_path)

    feature_records = load_yaml_file(feature_lists_path / "__sequence.yml")
    if not feature_records:
        feature_records = []

    save_yaml_file(
        str(feature_lists_path),
        {
            "module_name": None,
            "feature_list_name": "Test Feature List 5",
            "feature_list": "[({'name': PrepareNextChannel}, "
            "{'name': LoopByCount, 'args': (3,),})]",
        },
        "__test_1.yml",
    )

    model.load_feature_records()
    assert len(feature_lists) == l + len(feature_records) + 1
    assert (
        convert_feature_list_to_str(feature_lists[-1])
        == '[({"name": PrepareNextChannel,},{"name": LoopByCount,"args": (3,),},),]'
    )

    del feature_lists[-1]
    os.remove(feature_lists_path / "__test_1.yml")

    model.load_feature_records()
    assert len(feature_lists) == l + len(feature_records) * 2
    feature_records_2 = load_yaml_file(feature_lists_path / "__sequence.yml")
    assert feature_records == feature_records_2
    os.remove(feature_lists_path / "__sequence.yml")
