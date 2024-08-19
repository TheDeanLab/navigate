from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, ANY
import pytest
import numpy


class DummySplashScreen:
    def destroy(self):
        pass


@pytest.fixture(scope="session")
def controller(tk_root):
    from navigate.controller.controller import Controller

    base_directory = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "src", "navigate"
    )
    configuration_directory = Path.joinpath(base_directory, "config")

    configuration_path = Path.joinpath(configuration_directory, "configuration.yaml")
    experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
    waveform_constants_path = Path.joinpath(
        configuration_directory, "waveform_constants.yml"
    )
    rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")
    waveform_templates_path = Path.joinpath(
        configuration_directory, "waveform_templates.yml"
    )
    gui_configuration_path = Path.joinpath(
        configuration_directory, "gui_configuration.yml"
    )
    args = SimpleNamespace(synthetic_hardware=True)

    controller = Controller(
        tk_root,
        DummySplashScreen(),
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        gui_configuration_path,
        args,
    )
    # To make sure the testcases won't hang on because of the model.event_queue
    # The changes here won't affect other testcases,
    # because the testcases from other files use DummyController
    # and DummyModel instead of this controller fixture
    controller.model = MagicMock()
    controller.threads_pool = MagicMock()
    controller.model.get_offset_variance_maps.return_value = (None, None)

    yield controller

    try:
        controller.execute("exit")
    except SystemExit:
        pass


def test_update_buffer(controller):
    camera_parameters = controller.configuration["experiment"]["CameraParameters"]
    controller.update_buffer()
    assert controller.img_width == camera_parameters["img_x_pixels"]
    assert controller.img_height == camera_parameters["img_y_pixels"]

    # Make sure that the get_data_buffer method is not called.
    assert controller.model.get_data_buffer.called is False

    # Change the buffer size
    controller.configuration["experiment"]["CameraParameters"]["img_x_pixels"] = 100
    controller.configuration["experiment"]["CameraParameters"]["img_y_pixels"] = 100
    controller.update_buffer()

    # Make sure that the get_data_buffer method is called.
    assert controller.model.get_data_buffer.called is True

    # Confirm that the buffer size has been updated.
    assert controller.img_width == 100
    assert controller.img_height == 100

    assert True


def test_change_microscope(controller):
    # Get the microscopes from the configuration file
    microscopes = controller.configuration["configuration"]["microscopes"]

    # Iterate through the microscopes and change the microscope
    for microscope_name in microscopes.keys():

        # Patch the configuration_controller
        controller.configuration_controller.change_microscope = MagicMock()

        # Default zoom is '0.63x'
        zoom = microscopes[microscope_name]["zoom"]["position"].keys()[0]
        controller.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom

        # Change the microscope without passing the zoom
        controller.change_microscope(microscope_name)
        assert (
            controller.configuration["experiment"]["MicroscopeState"]["microscope_name"]
            == microscope_name
        )

        # Confirm that the zoom has not changed.
        assert controller.configuration["experiment"]["MicroscopeState"]["zoom"] == zoom

        # Call it and pass the zoom
        zoom = microscopes[microscope_name]["zoom"]["position"].keys()[-1]
        controller.change_microscope(microscope_name, zoom)
        assert controller.configuration["experiment"]["MicroscopeState"]["zoom"] == zoom

        # Make sure that the configuration_controller has been called.
        assert controller.configuration_controller.change_microscope.called is True

        # Have configuration controller return False
        controller.configuration_controller.change_microscope.return_value = False

        # Patch the stage controller, channels_tab_controller...
        controller.stage_controller.initialize = MagicMock()
        controller.channels_tab_controller.initialize = MagicMock()
        camera_setting_controller = controller.camera_setting_controller
        camera_setting_controller.update_camera_device_related_setting = MagicMock()
        camera_setting_controller.calculate_physical_dimensions = MagicMock()
        controller.camera_view_controller.update_snr = MagicMock()

        # Call change microscope, assert patched methods are not called
        controller.change_microscope(microscope_name)
        assert controller.stage_controller.initialize.called is False
        assert controller.channels_tab_controller.initialize.called is False
        assert (
            camera_setting_controller.update_camera_device_related_setting.called
            is False
        )
        assert camera_setting_controller.calculate_physical_dimensions.called is False
        assert controller.camera_view_controller.update_snr.called is False

        # Have configuration controller return True
        controller.configuration_controller.change_microscope.return_value = True

        # Call change microscope, assert patched methods are called
        controller.change_microscope(microscope_name)
        assert controller.stage_controller.initialize.called is True
        assert controller.channels_tab_controller.initialize.called is True
        assert (
            camera_setting_controller.update_camera_device_related_setting.called
            is True
        )
        assert camera_setting_controller.calculate_physical_dimensions.called is True
        assert controller.camera_view_controller.update_snr.called is True

        # Test waveform popup controller.
        controller.waveform_popup_controller = MagicMock()
        controller.change_microscope(microscope_name)
        assert (
            controller.waveform_popup_controller.populate_experiment_values.called
            is True
        )

        assert True


def test_initialize_cam_view(controller):
    minmax_values = [0, 2**16 - 1]
    image_metrics = [1, 0, 0]
    controller.initialize_cam_view()

    assert (
        controller.camera_view_controller.image_palette["Min"].get() == minmax_values[0]
    )
    assert (
        controller.camera_view_controller.image_palette["Max"].get() == minmax_values[1]
    )
    assert (
        controller.camera_view_controller.image_metrics["Frames"].get()
        == image_metrics[0]
    )

    assert True


def test_populate_experiment_setting(controller):
    controller.populate_experiment_setting(in_initialize=False)
    assert True


def test_prepare_acquire_data(controller):

    # Test without warning message
    controller.set_mode_of_sub = MagicMock()
    assert controller.prepare_acquire_data() is True
    assert controller.set_mode_of_sub.called is True

    # Test with warning message. Challenging since controller is local.
    # with patch('controller.tkinter.messagebox.showerror') as mock_showerror:
    #     controller.update_experiment_setting.return_value = "Warning!"
    #     assert controller.prepare_acquire_data() is False
    #     mock_showerror.assert_called_once()

    assert True


def test_set_mode_of_sub(controller):
    modes = ["customized", "stop", "live"]

    for mode in modes:
        controller.set_mode_of_sub(mode=mode)

    assert True


def test_execute_joystick_toggle(controller):
    # joystick_toggle
    controller.threads_pool.createThread = MagicMock()
    controller.stage_controller.joystick_is_on = False
    controller.execute("joystick_toggle")
    assert controller.threads_pool.createThread.called is False

    controller.stage_controller.joystick_is_on = True
    controller.execute("joystick_toggle")
    assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_stop_stage(controller):
    controller.threads_pool.createThread = MagicMock()
    controller.execute(command="stop_stage")
    assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_move_stage_and_update_info(controller):
    positions = {"x": 51, "y": 52.0, "z": -530.3, "theta": 1, "f": 0}

    controller.execute("move_stage_and_update_info", positions)
    for axis, value in positions.items():
        assert (
            float(controller.stage_controller.widget_vals[axis].get())
            == positions[axis]
        )

    assert True


def test_execute_move_stage_and_acquire_image(controller):
    positions = {"x": 51, "y": 52.0, "z": -530.3, "theta": 1, "f": 0}
    controller.model.move_stage = MagicMock()
    controller.threads_pool.createThread = MagicMock()
    controller.execute("move_stage_and_acquire_image", positions)

    assert controller.model.move_stage.called is True

    for axis, value in positions.items():
        assert (
            float(controller.stage_controller.widget_vals[axis].get())
            == positions[axis]
        )

    assert controller.threads_pool.createThread.called is True
    assert True


def test_execute_get_stage_position(controller):
    # Set the positions in the GUI
    set_positions = {"x": 51, "y": 52.0, "z": -530.3, "theta": 1, "f": 0}
    controller.execute("move_stage_and_update_info", set_positions)

    # Get the positions from the GUI
    get_positions = controller.execute("get_stage_position")
    assert type(get_positions) is dict

    axes = ["x", "y", "z", "theta", "f"]
    for axis in axes:
        assert axis in get_positions.keys()

    # assert that get_positions is equal to set_positions
    assert get_positions == set_positions

    assert True


def test_execute_mark_position(controller):

    set_positions = {"x": 51, "y": 52.0, "z": -530.3, "theta": 1, "f": 0}
    controller.execute("mark_position", set_positions)

    # Get the positions from the multiposition table. Returns a list of lists.
    get_positions = controller.multiposition_tab_controller.get_positions()

    # Assert that the last position in get_positions is equal to set_positions
    assert get_positions[-1] == [
        set_positions["x"],
        set_positions["y"],
        set_positions["z"],
        set_positions["theta"],
        set_positions["f"],
    ]

    assert True


def test_execute_resolution(controller):
    pass


def test_execute_set_save(controller):

    for save_data in [True, False]:
        controller.execute("set_save", save_data)
        assert controller.acquire_bar_controller.is_save == save_data
        assert (
            controller.configuration["experiment"]["MicroscopeState"]["is_save"]
            == save_data
        )

    assert True


def test_execute_update_setting(controller):
    controller.threads_pool.createThread = MagicMock()
    args = ["resolution", {"resolution_mode", "1x"}]
    controller.execute("update_setting", args)
    assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_stage_limits(controller):
    controller.threads_pool.createThread = MagicMock()
    for stage_limits in [True, False]:
        controller.threads_pool.createThread.reset_mock()
        controller.execute("stage_limits", stage_limits)
        assert controller.stage_controller.stage_limits == stage_limits
        assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_autofocus(controller):
    # Create mock objects
    controller.threads_pool.createThread = MagicMock()

    # Test non-acquiring case
    controller.acquire_bar_controller.is_acquiring = False
    controller.execute("autofocus")
    controller.threads_pool.createThread.assert_called_with(
        "camera", controller.capture_image, args=("autofocus", "live")
    )

    # Test the acquiring case
    controller.acquire_bar_controller.mode = "live"
    controller.acquire_bar_controller.is_acquiring = True
    controller.threads_pool.createThread.reset_mock()
    controller.execute("autofocus")
    controller.threads_pool.createThread.assert_called_once()
    controller.threads_pool.createThread.assert_any_call("model", ANY)
    args, kwargs = controller.threads_pool.createThread.call_args
    assert args[0] == "model"

    # Confirm that the lambda is callable.
    assert callable(args[1])

    assert True


def test_execute_eliminate_tiles(controller):
    controller.threads_pool.createThread = MagicMock()

    # Populate Feature List
    controller.menu_controller.feature_list_names = ["Remove Empty Tiles"]

    # Set the mode to live
    controller.acquire_bar_controller.set_mode("live")

    # Execute the command
    controller.execute("eliminate_tiles")
    assert controller.acquire_bar_controller.get_mode() == "customized"

    # Assert that the thread pool is called
    assert controller.threads_pool.createThread.called is True

    assert True


def test_execute_load_features(controller):
    controller.threads_pool.createThread = MagicMock()

    controller.execute("load_features")
    controller.threads_pool.createThread.assert_any_call("model", ANY)
    args, kwargs = controller.threads_pool.createThread.call_args
    assert args[0] == "model"
    assert callable(args[1])

    assert True


def test_execute_acquire_and_save_return(controller):

    # Prepare mock objects.
    controller.prepare_acquire_data = MagicMock()
    controller.acquire_bar_controller.stop_acquire = MagicMock()
    controller.camera_setting_controller.calculate_physical_dimensions = MagicMock()

    # Prepare mock returns
    controller.prepare_acquire_data.return_value = False

    # Test and make sure return is called
    controller.execute("acquire_and_save")
    assert controller.acquire_bar_controller.stop_acquire.called is True
    assert (
        controller.camera_setting_controller.calculate_physical_dimensions.called
        is False
    )

    assert True


def test_execute_acquire_and_acquire_and_save(controller):
    # The modes "customized" & "live" results in the thread not being called.
    # TODO: Figure out why the thread is not being called.

    # controller.plugin_acquisition_modes = {}
    # controller.threads_pool.createThread = MagicMock()
    #
    # for statement in ["acquire", "acquire_and_save"]:
    #     for mode in ["z-stack", "single"]:
    #         controller.acquire_bar_controller.mode = mode
    #         controller.execute(statement)
    #         controller.threads_pool.createThread.assert_called_with(
    #             "camera",
    #             controller.capture_image,
    #             args=(
    #                 "acquire",
    #                 controller.acquire_bar_controller.mode,
    #             ),
    #         )
    #         controller.stop_acquisition_flag = True
    #         controller.threads_pool.createThread.reset_mock()

    pass


def test_execute_stop_acquire(controller):
    # TODO: Currently hangs indefinitely.
    # Prepare mock objects.
    # controller.show_img_pipe.poll = MagicMock()
    # controller.show_img_pipe.recv = MagicMock()
    # controller.sloppy_stop = MagicMock()
    # controller.threads_pool.createThread = MagicMock()
    #
    # # Prepare mock returns
    # controller.show_img_pipe.poll.return_value = True
    #
    # # Test and make sure return is called
    # controller.stop_acquisition_flag = False
    # controller.execute("acquire", "continuous")
    # controller.execute("stop_acquire")
    pass


def test_execute_exit(controller):
    # Essentially already tested by teardown of controller fixture.
    pass


def test_execute_adaptive_optics(controller):
    controller.threads_pool.createThread = MagicMock()
    for command in [
        "flatten_mirror",
        "zero_mirror",
        "set_mirror",
        "set_mirror_from_wcs",
    ]:
        controller.execute(command)
        controller.threads_pool.createThread.assert_called_with("model", ANY)
        args, kwargs = controller.threads_pool.createThread.call_args
        assert args[0] == "model"
        assert callable(args[1])

    controller.execute("tony_wilson")
    controller.threads_pool.createThread.assert_called_with(
        "camera", controller.capture_image, args=("tony_wilson", "live")
    )


def test_execute_random(controller):
    controller.threads_pool.createThread = MagicMock()
    for command in ["random1", "random2"]:
        controller.execute(command)
        controller.threads_pool.createThread.assert_called_with("model", ANY)
        args, kwargs = controller.threads_pool.createThread.call_args
        assert args[0] == "model"
        assert callable(args[1])

    assert True


def test_capture_image(controller):

    count = 0
    def get_image_id():
        nonlocal count
        count += 1
        if count >= 10:
            return "stop"
        return numpy.random.randint(0, 10)
    
    width = controller.configuration["experiment"]["CameraParameters"]["img_x_pixels"]
    height = controller.configuration["experiment"]["CameraParameters"]["img_y_pixels"]
    images = numpy.random.rand(10, width, height)
    controller.data_buffer = images
    work_thread = MagicMock()
    work_thread.join = MagicMock()
    controller.threads_pool.createThread = MagicMock()
    controller.threads_pool.createThread.return_value = work_thread
    controller.show_img_pipe.recv = get_image_id
    controller.show_img_pipe.poll = MagicMock()
    controller.show_img_pipe.poll.return_value = False

    # Deal with stop_acquire
    controller.sloppy_stop = MagicMock()
    controller.menu_controller.feature_id_val.set = MagicMock()

    # Deal with camera view controller trying to launch a thread
    controller.camera_view_controller.is_displaying_image = MagicMock()
    controller.camera_view_controller.is_displaying_image.return_value = True

    for command in ["acquire"]:  # "autofocus"
        for mode in ["continuous", "live", "z-stack", "single"]:
            controller.capture_image(command, mode)

            # Evaluate calls
            controller.threads_pool.createThread.assert_called_with("model", ANY)
            args, kwargs = controller.threads_pool.createThread.call_args
            assert args[0] == "model"
            assert callable(args[1])

            controller.stop_acquisition_flag = True
            controller.threads_pool.createThread.reset_mock()

    assert controller.acquire_bar_controller.framerate != 0
    assert controller.camera_setting_controller.framerate_widgets[
        "max_framerate"
    ].get() != str(0)

    assert True


def test_launch_additional_microscope():
    # This looks awful to test...
    pass


def test_move_stage(controller):
    pos_dict = {"x": 1, "y": 2.0, "z": 3.14, "theta": 400, "f": 5.01}
    controller.model.move_stage = MagicMock()
    controller.move_stage(pos_dict)
    controller.model.move_stage.assert_called_with(pos_dict)


def test_stop_stage(controller):
    controller.model.stop_stage = MagicMock()
    controller.stop_stage()
    controller.model.stop_stage.assert_called_with()


def test_update_stage_controller_silent(controller):
    pos_dict = {"x": 1, "y": 2.0, "z": 3.14, "theta": 400, "f": 5.01}
    controller.update_stage_controller_silent(pos_dict)
    for axis, value in pos_dict.items():
        assert (
            float(controller.stage_controller.widget_vals[axis].get()) == pos_dict[axis]
        )


@pytest.mark.parametrize(
    "acquisition_mode, sensor_mode, readout_direction, template_name, "
    "expected_template_name",
    [
        ("live", "Normal", "", "Bidirectional", "Default"),
        ("z-stack", "Normal", "", "Bidirectional", "Default"),
        ("customized", "Normal", "", "Bidirectional", "Bidirectional"),
        ("live", "Light-Sheet", "Top-To-Bottom", "Bidirectional", "Default"),
        ("live", "Light-Sheet", "Bidirectional", "Bidirectional", "Bidirectional"),
        (
            "customized",
            "Light-Sheet",
            "Bidirectional",
            "Bidirectional",
            "Bidirectional",
        ),
        ("z-stack", "Light-Sheet", "Bidirectional", "Default", "Bidirectional"),
        ("z-stack", "Light-Sheet", "Top-To-Bottom", "Default", "Default"),
    ],
)
def test_waveform_template(
    controller,
    acquisition_mode,
    sensor_mode,
    readout_direction,
    template_name,
    expected_template_name,
):
    controller.configuration["experiment"]["MicroscopeState"][
        "waveform_template"
    ] = template_name
    controller.configuration["experiment"]["MicroscopeState"][
        "image_mode"
    ] = acquisition_mode
    controller.configuration["experiment"]["CameraParameters"]["number_of_pixels"] = 10
    controller.populate_experiment_setting(in_initialize=True)

    controller.camera_setting_controller.mode_widgets["Readout"].set(readout_direction)
    controller.camera_setting_controller.mode_widgets["Sensor"].set(sensor_mode)
    controller.update_experiment_setting()

    assert (
        controller.configuration["experiment"]["MicroscopeState"]["waveform_template"]
        == expected_template_name
    )

    assert True
