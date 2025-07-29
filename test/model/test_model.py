# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from multiprocessing import Manager
from unittest.mock import MagicMock
import matplotlib.pyplot as plt
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Or INFO

# Third Party Imports

# Local Imports
from navigate.model.devices.camera.synthetic_threaded import SyntheticThreadedCamera
from navigate.model.devices.galvo.synthetic_threaded import SyntheticThreadedGalvo

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.fixture(scope="module")
def model():
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
    from navigate.tools.file_functions import load_yaml_file

    with Manager() as manager:

        # Use configuration files that ship with the code base
        configuration_directory = Path.joinpath(
            Path(__file__).resolve().parent.parent.parent, "src", "navigate", "config"
        )
        configuration_path = Path.joinpath(
            configuration_directory, "configuration.yaml"
        )
        experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
        waveform_constants_path = Path.joinpath(
            configuration_directory, "waveform_constants.yml"
        )
        rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")
        multi_positions_path = Path.joinpath(configuration_directory, "multi_positions.yml")

        event_queue = MagicMock()

        configuration = load_configs(
            manager,
            configuration=configuration_path,
            experiment=experiment_path,
            waveform_constants=waveform_constants_path,
            rest_api_config=rest_api_path,
        )
        verify_configuration(manager, configuration)
        verify_experiment_config(manager, configuration)
        verify_waveform_constants(manager, configuration)

        positions = load_yaml_file(multi_positions_path)
        positions = verify_positions_config(positions)
        configuration["multi_positions"] = positions

        model = Model(
            args=SimpleNamespace(synthetic_hardware=True),
            configuration=configuration,
            event_queue=event_queue,
        )

        model.__test_manager = manager

        yield model
        # while not event_queue.empty():
        #     event_queue.get()
        # event_queue.close()
        # event_queue.join_thread()



def test_single_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "single"
    state["is_save"] = False

    n_frames = len(list(filter(lambda channel: channel["is_selected"], state["channels"].values())))

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


def test_live_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "live"

    n_images = 0
    pre_channel = 0

    show_img_pipe = model.create_pipe("show_img_pipe")

    model.run_command("acquire")

    while True:
        image_id = show_img_pipe.recv()
        if image_id == "stop":
            break
        channel_id = model.active_microscope.current_channel
        assert channel_id != pre_channel
        pre_channel = channel_id
        n_images += 1
        if n_images >= 30:
            model.run_command("stop")
    model.data_thread.join()
    model.release_pipe("show_img_pipe")


def test_run_threaded_camera_acquisition(model):
    number_of_frames = 5
    image_list = run_threaded_camera_acquisition(model, number_of_frames)
    logger.debug(f"Number of images: {len(image_list)}")

    assert len(image_list) == number_of_frames, f"Expected {number_of_frames} images, got {len(image_list)}"
    assert isinstance(image_list[-1], np.ndarray), "Last item is not a NumPy array"

def test_run_threaded_galvo(model):
    """
    Test that a SyntheticThreadedGalvo can start and stop waveform playback
    in a separate thread, and behaves as expected.
    """

    logger = logging.getLogger("navigate.model.devices.galvo.synthetic_threaded")
    logger.setLevel(logging.DEBUG)

    galvo = SyntheticThreadedGalvo(
        model.active_microscope_name,
        None,  # synthetic DAQ (not used)
        model.configuration,
        device_id=0,
        use_threading=True
    )

    microscope = model.get_active_microscope()
    exposure_times, sweep_times = microscope.calculate_exposure_sweep_times()
    galvo.adjust_waveforms(exposure_times, sweep_times)

    # --- Assertions before starting ---
    assert not galvo.active, "Galvo should not be active before starting"
    assert galvo.thread is None, "Galvo thread should be None before starting"

    galvo.start_threaded_output()

    # --- Assertions after starting ---
    assert galvo.active, "Galvo should be marked active after start"
    assert galvo.thread is not None and galvo.thread.is_alive(), "Galvo thread should be alive after start"

    # Let it run briefly.
    time.sleep(0.01)

    galvo.stop_threaded_output()

    # --- Assertions after stopping ---
    assert not galvo.active, "Galvo should not be active after stop"
    assert galvo.thread is None, "Galvo thread should be None after stop"

    logger.debug("Galvo thread start/stop test passed.")

def test_run_camera_galvo_threaded_acquisition(model):
    """ Test that we can perform an acquisition with camera and galvo working in separate threads. """
    image_list, synthetic_camera, synthetic_galvo = run_camera_galvo_threaded_acquisition(model)
    
    model.logger.info(f"Captured {len(image_list)} images.")
    
    assert image_list, "No images were captured."
    assert isinstance(image_list[-1], np.ndarray), "Last item is not a NumPy array."

    shapes = {img.shape for img in image_list}
    assert len(shapes) == 1, "Inconsistent image shapes"

    assert synthetic_galvo.thread is None, "Galvo thread should be None after stop"
    assert synthetic_camera.thread is None, "Camera thread should be None after stop" 


def test_autofocus_live_acquisition(model):
    state = model.configuration["experiment"]["MicroscopeState"]
    state["image_mode"] = "live"

    n_images = 0
    pre_channel = 0
    autofocus = False

    show_img_pipe = model.create_pipe("show_img_pipe")

    model.run_command("acquire")

    while True:
        image_id = show_img_pipe.recv()
        if image_id == "stop":
            break
        channel_id = model.active_microscope.current_channel
        if not autofocus:
            assert channel_id != pre_channel
        pre_channel = channel_id
        n_images += 1
        if n_images >= 100:
            model.run_command("stop")
        elif n_images >= 70:
            autofocus = False
        elif n_images == 30:
            autofocus = True
            model.run_command("autofocus")

    model.data_thread.join()
    model.release_pipe("show_img_pipe")


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
        [[10.0, 10.0, 10.0, 10.0, 10.0]],
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


def test_load_feature_records(model):
    feature_lists = model.feature_list
    l = len(feature_lists)  # noqa

    from navigate.config.config import get_navigate_path
    from navigate.tools.file_functions import save_yaml_file, load_yaml_file
    from navigate.model.features.feature_related_functions import (
        convert_feature_list_to_str,
    )

    feature_lists_path = get_navigate_path() + "/feature_lists"

    if not os.path.exists(feature_lists_path):
        os.makedirs(feature_lists_path)

    feature_records = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
    if not feature_records:
        feature_records = []

    save_yaml_file(
        feature_lists_path,
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
    os.remove(f"{feature_lists_path}/__test_1.yml")

    model.load_feature_records()
    assert len(feature_lists) == l + len(feature_records) * 2
    feature_records_2 = load_yaml_file(f"{feature_lists_path}/__sequence.yml")
    assert feature_records == feature_records_2
    os.remove(f"{feature_lists_path}/__sequence.yml")

def run_threaded_camera_acquisition(model, number_of_frames) -> None:
    synthetic_camera = SyntheticThreadedCamera(model.active_microscope_name, None, model.configuration, use_threading = True) # Synthetic camera has "None" hardware. 
    synthetic_camera.start_threaded_acquisition()
    image_list = []

    for _ in range(number_of_frames):
        image = synthetic_camera.get_image_from_queue(timeout=2)
        if image is not None:
            image_list.append(image)
        else: 
            model.logger.warning("Warning: Timed out waiting for image.")
            break
    
    synthetic_camera.stop_threaded_acquisition()
    model.logger.info("Acquisition stopped.")

    return image_list

def _show_image(images, frame):
    """ Can be helpful during debugging."""
    if not images:
        logger.debug("No images to display.")
        return
    img = images[frame]
    plt.imshow(img, cmap="gray")
    plt.title(f"Image {frame}")
    plt.colorbar()
    plt.show()

def run_camera_galvo_threaded_acquisition(model):
    """ Run an acquisition with camera and galvo working in separate threads. 
    The camera snaps images while the galvo moves through all of its waveforms. """
    # Initialize camera.
    synthetic_camera = SyntheticThreadedCamera(
    model.active_microscope_name,
    None,
    model.configuration, 
    use_threading = True
    )

    # Initialize galvo.
    synthetic_galvo = SyntheticThreadedGalvo(
    model.active_microscope_name,
    None,  # Can use synthetic DAQ here if available.
    model.configuration,
    device_id=0,
    use_threading=True
    )

    # Prepare waveforms for galvo.
    microscope = model.get_active_microscope()
    exposure_times, sweep_times = microscope.calculate_exposure_sweep_times()
    synthetic_galvo.adjust_waveforms(exposure_times, sweep_times)

    # Start threads and their tasks.
    synthetic_camera.start_threaded_acquisition() 
    synthetic_galvo.start_threaded_output() 
    
    image_list = []

    start_time = time.time()
    timeout = 10  # Seconds.

    # Run the threaded acquisition - camera is snapping and galvo is moving simultaneously.
    try:
        while not synthetic_galvo.stop_event.is_set():
            image = synthetic_camera.get_image_from_queue(timeout=2)
            
            if image is not None:
                image_list.append(image)
            else: 
                model.logger.warning("Warning: Timed out waiting for image.")
                break

            if time.time() - start_time > timeout:
                model.logger.warning("Timeout reached waiting for galvo to finish.")
                break

    finally: # Make sure we always stop the threads.      
        synthetic_camera.stop_threaded_acquisition() 
        model.logger.info("Camera thread stopped.")
        synthetic_galvo.stop_threaded_output()
        model.logger.info("Galvo thread stopped.")   

    return image_list, synthetic_camera, synthetic_galvo
