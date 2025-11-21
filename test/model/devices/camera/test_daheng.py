# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
import pytest
from typing import Tuple
from unittest.mock import patch, MagicMock
import logging
import io

# Third Party Imports
import numpy as np
from numpy.testing import assert_array_equal

# Local Imports
from navigate.model.utils.exceptions import UserVisibleException

try:
    import gxipy  # noqa: F401
except:

    @pytest.fixture(autouse=True)
    def mock_daheng_module():
        fake_gx = MagicMock()
        with patch.dict("sys.modules", {"gxipy": fake_gx}):
            yield fake_gx


@pytest.fixture
def mock_daheng_sdk():
    """Patch Daheng SDK (gxipy) and return mocked device + subsystems."""
    with patch(
        "navigate.model.devices.camera.daheng.gx.DeviceManager"
    ) as mock_device_manager:
        device = _create_mock_device(mock_device_manager)
        feature_control = _create_mock_feature_control()
        data_stream, raw_image = _create_mock_image_pipeline()

        _attach_mock_interfaces_to_device(device, feature_control, data_stream)

        yield {
            "device": device,
            "feature_control": feature_control,
            "data_stream": data_stream,
            "raw_image": raw_image,
        }


def _attach_mock_interfaces_to_device(device, feature_control, data_stream):
    """
    Attach core SDK interfaces to a mock Daheng device.

    In the gxipy SDK, once a device is opened, it provides two key subsystems:

    - feature_control (via get_remote_device_feature_control()):
        This is the interface for configuring camera hardware settings such as
        exposure time, gain, trigger mode, binning, resolution, and ROI.
        The SDK exposes these through feature "objects" with .get()/.set() methods.

    - data_stream (accessed as a property):
        This handles actual image acquisition. It provides methods to start/stop
        streaming and to retrieve frames via .snap_image().

    This function sets up mock versions of those subsystems to a MagicMock-based
    device object, enabling testable interaction without requiring physical hardware.

    Parameters
    ----------
    device : MagicMock
        The mocked gxipy.Device object to configure.

    feature_control : MagicMock
        Mocked feature control interface to simulate hardware parameters.

    data_stream : MagicMock
        Mocked data stream interface to simulate image capture.
    """
    device.get_remote_device_feature_control.return_value = feature_control
    device.data_stream = data_stream


def _create_mock_device(mock_device_manager) -> MagicMock:
    """
    Create a fake Daheng device and configure DeviceManager return values.

    This sets up:
    - update_device_list() -> None
    - get_device_list() -> list with one fake serial number
    - open_device_by_index(i) -> the mock device

    Returns
    -------
    MagicMock
        A fake Daheng device object.
    """
    mock_device = MagicMock(name="FakeDevice")

    mock_device_manager.return_value.update_device_list.return_value = None
    mock_device_manager.return_value.get_device_list.return_value = [{"sn": "1234"}]
    mock_device_manager.return_value.open_device_by_index.return_value = mock_device

    return mock_device


def _create_mock_feature_control() -> MagicMock:
    """
    Create a fake FeatureControl interface that simulates Daheng camera settings.

    Simulates:
    - get_string_feature("DeviceSerialNumber").get() -> "1234"
    - get_int_feature(...).get() -> 2048
    - get_enum_feature(...).set(...) -> None

    Returns
    -------
    MagicMock
        A mock feature_control object.
    """
    mock_feature_control = MagicMock(name="FakeFeatureControl")
    mock_feature_control.get_string_feature.return_value.get.return_value = "1234"
    mock_feature_control.get_int_feature.side_effect = lambda name: MagicMock(
        get=MagicMock(return_value=2048)
    )
    mock_feature_control.get_enum_feature.return_value.set.return_value = None
    return mock_feature_control


def _create_mock_image_pipeline() -> Tuple[MagicMock, MagicMock]:
    """
    Create a mocked data stream and raw image pipeline.

    Simulates:
    - data_stream.snap_image() -> mock_raw_image
    - raw_image.get_numpy_array() -> np.zeros((2048, 2048), dtype=np.uint16)

    Returns
    -------
    Tuple[MagicMock, MagicMock]
        (mock_data_stream, mock_raw_image)
    """
    stream = MagicMock(name="FakeDataStream")
    image = MagicMock(name="FakeRawImage")
    stream.snap_image.return_value = image
    image.get_numpy_array.return_value = np.zeros((2048, 2048), dtype=np.uint16)
    return stream, image


@pytest.fixture
def camera(mock_daheng_sdk):
    """
    Return a DahengCamera instance connected via mocked SDK.

    The mock_daheng_sdk fixture is required to patch the SDK and simulate hardware.
    It's not used directly in this function, but must be active when connect() is called.
    """
    # Use the patched classmethod to simulate SDK connection.
    # This is where mock_daheng_sdk enters.
    from navigate.model.devices.camera.daheng import DahengCamera

    # Minimal config object matching Navigate's expected schema
    config = {
        "configuration": {
            "microscopes": {
                "test_scope": {
                    "camera": {
                        "hardware": {
                            "serial_number": "1234",
                        }
                    }
                }
            }
        }
    }

    camera = DahengCamera(
        microscope_name="test_scope",
        device_connection=mock_daheng_sdk["device"],
        configuration=config,
    )

    # Initialize and return the test camera instance
    return camera


@patch("navigate.model.devices.camera.daheng.gx.DeviceManager")
def test_connect_without_serial(mock_dm):
    """
    Test that DahengCamera.connect() connects to the first camera if no serial number is provided.

    This uses patching to replace the actual DeviceManager with a mock,
    simulating a single connected camera with serial '1234'.
    """

    mock_device = MagicMock()

    # Simulate SDK returning one device with serial '1234'
    mock_dm.return_value.get_device_list.return_value = [{"sn": "1234"}]

    # Simulate opening that device returns our mock_device
    mock_dm.return_value.open_device_by_index.return_value = mock_device

    # Call connect without specifying serial number
    from navigate.model.devices.camera.daheng import DahengCamera

    device = DahengCamera.connect()

    # Verify that we get the mocked device object
    assert device == mock_device


@patch("navigate.model.devices.camera.daheng.gx.DeviceManager")
def test_connect_invalid_serial_raises(mock_dm):
    """
    Test that DahengCamera.connect() raises a UserVisibleException if the
    specified serial number does not match any connected camera.

    This verifies the fallback else-block logic in the for-loop of connect().
    """
    # Simulate one connected device with serial '1234'
    mock_dm.return_value.get_device_list.return_value = [{"sn": "1234"}]

    from navigate.model.devices.camera.daheng import DahengCamera

    # Attempt to connect with a non-existent serial number
    with pytest.raises(
        UserVisibleException, match="Daheng camera with serial INVALID_SN not found."
    ):
        DahengCamera.connect(serial_number="INVALID_SN")


def test_str(camera):
    """
    Test the string representation of the DahengCamera object.

    Ensures that the __str__ method includes the camera model name,
    serial number, and connection status in the returned string.
    """
    result = str(camera)
    assert "MER2_1220_32U3C Camera" in result
    assert "Serial: 1234" in result
    assert "Connected" in result


def test_camera_connected(camera):
    """
    Test that the camera object reports a connected state after setup.

    This relies on the 'camera' fixture, which internally calls DahengCamera.connect()
    and initializes the SDK state. Verifies that is_connected is True and the
    device serial number is correctly cached.
    """
    assert camera.is_connected
    assert camera.device_serial_number == "1234"


def test_disconnect_clears_state(camera):
    """
    Test that disconnect() resets internal state and marks camera as disconnected.
    """
    camera.disconnect()
    assert camera.device is None
    assert camera.feature_control is None
    assert camera.is_connected is False
    assert camera.serial_number == "UNKNOWN"


def test_set_exposure_time(camera):
    """
    Test that set_exposure_time() updates internal state and calls correct SDK feature.
    """
    camera.set_exposure_time(0.1)

    # Internal caching of exposure time (in seconds)
    assert camera._exposure_time == 0.1

    # Verifies that the SDK was told to get the 'ExposureTime' feature
    camera.feature_control.get_float_feature.assert_called_with("ExposureTime")


def test_set_gain(camera):
    """
    Ensure set_gain() calls the Gain feature with the expected float value.
    """
    camera.set_gain(5.0)
    camera.feature_control.get_float_feature.assert_called_with("Gain")
    camera.feature_control.get_float_feature.return_value.set.assert_called_with(5.0)


def test_set_binning(camera):
    """
    Test that set_binning() parses input string, updates binning values,
    and accesses correct SDK features.
    """
    result = camera.set_binning("2x2")
    assert result is True
    assert camera.x_binning == 2
    assert camera.y_binning == 2

    # Check that the SDK was asked for the correct feature names at least once
    camera.feature_control.get_int_feature.assert_any_call("BinningHorizontal")
    camera.feature_control.get_int_feature.assert_any_call("BinningVertical")


def test_set_invalid_ROI(camera):
    """
    Test that set_ROI() returns False and logs a warning when given invalid dimensions.
    """
    # Set invalid ROI parameters
    roi_width = 9000
    roi_height = 2048
    center_x = 1000
    center_y = 1000

    logger = logging.getLogger("model")
    logger.propagate = False  # prevent sending logs to root CLI handler

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)

    camera.stop_acquisition()
    handler.flush()
    result = camera.set_ROI(
        roi_width=roi_width, roi_height=roi_height, center_x=center_x, center_y=center_y
    )
    assert result is False
    assert f"Invalid ROI dimensions: {roi_width}x{roi_height}" in stream.getvalue()
    logger.removeHandler(handler)


def test_snap_image_returns_numpy_array(camera):
    """
    Test that snap_image() calls the SDK and returns a NumPy array.

    The camera fixture uses the mock_daheng_sdk fixture to simulate:
    - A data stream whose snap_image() returns a fake image object
    - An image object whose get_numpy_array() returns np.ndarray representing a fake image (zeros)

    """
    result = camera.snap_image()
    expected = np.zeros((2048, 2048), dtype=np.uint16)
    assert_array_equal(result, expected)
    camera.data_stream.snap_image.assert_called_once()


def test_snap_software_triggered_invalid_config(camera):
    """
    Test that snap_software_triggered() raises if trigger config is invalid.

    This mocks the 'TriggerMode' and 'TriggerSource' enum features to return
    incorrect values ('OFF' and 'HARDWARE'), and verifies that the method
    raises a UserVisibleException with a helpful message.
    """
    # Override trigger mode/source with bad values
    mock_enum_feature = MagicMock()
    mock_enum_feature.get_current_entry.return_value.get_symbolic.side_effect = [
        "OFF",
        "HARDWARE",
    ]
    camera.feature_control.get_enum_feature.return_value = mock_enum_feature

    with pytest.raises(
        UserVisibleException, match="TriggerMode='ON' and TriggerSource='SOFTWARE'"
    ):
        camera.snap_software_triggered()


def test_send_software_trigger(camera):
    """
    Test that send_software_trigger() calls the correct Daheng SDK command.

    Verifies that the camera issues a 'TriggerSoftware' command via the
    command feature interface and that send_command() is called exactly once.
    """
    camera.send_software_trigger()
    camera.feature_control.get_command_feature.assert_called_with("TriggerSoftware")
    camera.feature_control.get_command_feature.return_value.send_command.assert_called_once()


def test_set_trigger_mode(camera):
    """
    Test that set_trigger_mode() calls the correct enum feature and sets it to 'ON'.
    """
    camera.set_trigger_mode("ON")
    camera.feature_control.get_enum_feature.assert_called_with("TriggerMode")
    camera.feature_control.get_enum_feature.return_value.set.assert_called_with("ON")


def test_set_trigger_source(camera):
    """
    Test that set_trigger_source() selects the correct SDK enum feature and sets it to 'LINE1'.

    'LINE1' refers to a physical input pin used for hardware triggering,
    typically driven by a DAQ, microcontroller, or timing controller.
    """
    camera.set_trigger_source("LINE1")
    camera.feature_control.get_enum_feature.assert_called_with("TriggerSource")
    camera.feature_control.get_enum_feature.return_value.set.assert_called_with("LINE1")


def test_initialize_and_start_acquisition(camera):
    """
    Test that initialize_image_series and start_acquisition correctly
    update internal state and interact with the SDK.
    """
    # Create a fake image buffer with shape matching camera resolution
    fake_buffer = [MagicMock(name=f"Frame{i}") for i in range(5)]
    number_of_frames = 5

    # Initialize acquisition
    camera.initialize_image_series(
        data_buffer=fake_buffer, number_of_frames=number_of_frames
    )

    # Assert acquisition is marked as started
    assert camera.is_acquiring is True
    assert camera._number_of_frames == number_of_frames
    assert camera._frames_received == 0
    assert camera._data_buffer == fake_buffer

    # Start the acquisition and verify SDK interaction
    camera.data_stream.start_stream.assert_called_once()
    camera.feature_control.get_command_feature.assert_called_with("AcquisitionStart")
    camera.feature_control.get_command_feature.return_value.send_command.assert_called_once()


def test_initialize_start_and_receive_image(camera):
    """
    Test full acquisition flow:
    - initialize_image_series()
    - start_acquisition()
    - get_new_frame() to simulate image reception

    Verifies that the SDK methods are called, internal state is updated,
    and image data is written to the circular buffer.
    """
    fake_buffer = [MagicMock(name=f"Frame{i}") for i in range(3)]
    number_of_frames = 3

    camera.initialize_image_series(
        data_buffer=fake_buffer, number_of_frames=number_of_frames
    )

    # Simulate receiving frames
    for i in range(3):
        frame_indices = camera.get_new_frame()
        assert frame_indices == [i]
        fake_buffer[i].__setitem__.assert_called()  # Simulates [:, :] = image_data

    # Circular buffer check
    wraparound = camera.get_new_frame()
    assert wraparound == [0]


def test_stop_acquisition(camera):
    """
    Test that stop_acquisition() stops both the command and data stream,
    clears acquisition state, and accesses the correct command feature.
    """
    # Pretend acquisition is running
    camera.is_acquiring = True

    # Run method
    camera.stop_acquisition()

    # Ensure the correct SDK command was accessed and triggered
    camera.feature_control.get_command_feature.assert_called_with("AcquisitionStop")
    camera.feature_control.get_command_feature.return_value.send_command.assert_called_once()

    # Ensure the data stream was stopped
    camera.data_stream.stop_stream.assert_called_once()

    # Verify internal state was updated
    assert camera.is_acquiring is False


def test_stop_acquisition_when_disconnected(camera):
    """
    Test that stop_acquisition() logs a warning and does not raise
    when called on a disconnected camera.
    """
    camera.is_connected = False

    logger = logging.getLogger("model")
    logger.propagate = False  # prevent sending logs to root CLI handler

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)

    camera.stop_acquisition()
    handler.flush()

    assert "not connected" in stream.getvalue()

    logger.removeHandler(handler)


def test_set_sensor_mode_logs(camera):
    """
    Test that set_sensor_mode() logs a warning for unsupported modes.

    If an invalid mode is specified, the camera will be set to Normal
    mode (using global shutter).
    """
    camera.set_sensor_mode("InvalidModeName")
    camera.device.SensorShutterMode.set.assert_called_with(0)
    assert camera._scan_mode == 0


def test_snap_software_triggered_success(camera):
    """
    Test that snap_software_triggered() works when trigger config is correct.

    Mocks TriggerMode='ON' and TriggerSource='SOFTWARE', verifies that the
    method sends a software trigger, captures an image, and returns the result.

    Uses side_effect to return two enum values from a shared enum feature mock.
    """
    # Patch enum feature to simulate correct trigger mode and source
    mock_enum_feature = MagicMock()

    # First call to get_symbolic() returns 'ON', second returns 'SOFTWARE'
    mock_enum_feature.get_current_entry.return_value.get_symbolic.side_effect = [
        "ON",
        "SOFTWARE",
    ]
    camera.feature_control.get_enum_feature.return_value = mock_enum_feature

    # Snap image - behind the scenes, this calls data_stream.snap_image() which
    # is mocked during setup to return a fake image whose get_numpy_array() method
    # returns np.ndarray representing a fake image.
    result = camera.snap_software_triggered()

    expected = np.zeros((2048, 2048), dtype=np.uint16)
    assert_array_equal(result, expected)

    # Ensure the correct trigger command was issued via SDK
    camera.feature_control.get_command_feature.return_value.send_command.assert_called_with()


def test_get_new_frame(camera):
    """
    Test that get_new_frame() returns correct buffer index in sequence,
    and wraps around when the number of received frames exceeds the buffer length.

    This simulates a circular buffer behavior across multiple frames.
    """
    number_of_images = 3
    buffer = [MagicMock() for _ in range(number_of_images)]

    # Initialize image acquisition
    camera.initialize_image_series(
        data_buffer=buffer, number_of_frames=number_of_images
    )
    camera._frames_received = 0

    # First full loop through buffer
    for i in range(number_of_images):
        result = camera.get_new_frame()
        assert result == [i]

    # Wraparound: next result should start from 0 again
    result = camera.get_new_frame()
    assert result == [0]

    result = camera.get_new_frame()
    assert result == [1]


def test_close_image_series(camera):
    """
    Test that close_image_series() stops acquisition and clears buffer state.

    This ensures the SDK stream is stopped and internal flags like
    is_acquiring and _data_buffer are reset properly.

    The data_stream is mocked in the camera fixture (via mock_daheng_sdk).
    """
    camera.is_acquiring = True
    camera._data_buffer = [MagicMock(), MagicMock()]  # Simulate buffered frames

    camera.close_image_series()

    # Acquisition state should be cleared
    assert camera.is_acquiring is False
    assert camera._data_buffer == None

    # SDK stream should be stopped
    camera.data_stream.stop_stream.assert_called_once()
