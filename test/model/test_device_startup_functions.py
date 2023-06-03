import unittest
from unittest.mock import MagicMock

from aslm.model.device_startup_functions import auto_redial, load_camera_connection


class AutoRedialTests(unittest.TestCase):
    def test_auto_redial_success(self):
        # Mock the function
        func_mock = MagicMock(return_value="Success")

        # Call auto_redial with a successful function call
        result = auto_redial(func_mock, args=(1, 2, 3), n_tries=3)

        # Assert that the function was called once
        func_mock.assert_called_once_with(1, 2, 3)

        # Assert the result is as expected
        self.assertEqual(result, "Success")

    def test_auto_redial_retry(self):
        # Mock the function to raise an exception twice and then return a result
        func_mock = MagicMock()
        func_mock.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            "Success",
        ]

        # Call auto_redial with the function that raises exceptions
        result = auto_redial(func_mock, args=(1,), n_tries=3, exception=Exception)

        # Assert that the function was called three times (two retries)
        self.assertEqual(func_mock.call_count, 3)
        func_mock.assert_called_with(1)

        # Assert the result is as expected
        self.assertEqual(result, "Success")

    def test_auto_redial_retry_failure(self):
        # Mock the function to always raise an exception
        func_mock = MagicMock(side_effect=Exception("Connection failed"))

        # Call auto_redial with the function that always raises an exception
        # Assert that it raises the exception after reaching the maximum number of
        # retries
        with self.assertRaises(Exception):
            auto_redial(func_mock, args=(1,), n_tries=3, exception=Exception)

        # Assert that the function was called three times (maximum retries)
        self.assertEqual(func_mock.call_count, 3)
        func_mock.assert_called_with(1)


class LoadCameraConnectionTests(unittest.TestCase):
    def test_load_camera_connection_hamamatsu(self):
        # Mock the configuration dictionary
        configuration_mock = {
            "configuration": {"hardware": {"camera": [{"type": "HamamatsuOrca"}]}}
        }

        # Mock the HamamatsuController class and its DCAM method
        HamamatsuControllerMock = MagicMock()
        HamamatsuControllerMock.DCAM.return_value = "CameraController"

        # Mock the importlib.import_module function to return the
        # HamamatsuControllerMock
        importlib_mock = MagicMock()
        importlib_mock.import_module.return_value = HamamatsuControllerMock

        # Patch the importlib.import_module function
        with unittest.mock.patch("my_module.importlib.import_module", importlib_mock):
            # Call load_camera_connection with the mock configuration and camera_id
            result = load_camera_connection(configuration_mock, camera_id=0)

        # Assert that the importlib.import_module function was called with the
        # correct argument
        importlib_mock.import_module.assert_called_once_with(
            "aslm.model.devices.APIs.hamamatsu.HamamatsuAPI"
        )

        # Assert that the HamamatsuController.DCAM method was called with the correct
        # argument
        HamamatsuControllerMock.DCAM.assert_called_once_with(0)

        # Assert the result is as expected
        self.assertEqual(result, "CameraController")

    def test_load_camera_connection_synthetic(self):
        # Mock the configuration dictionary
        # configuration_mock = {
        #     "configuration": {"hardware": {"camera": [{"type": "SyntheticCamera"}]}}
        # }
        pass
        # # Call load_camera_connection with the mock configuration and is_synthetic=
        # True
        # result = load_camera_connection(configuration_mock, is_synthetic=True)
        #
        # # Assert that the result is an instance of the SyntheticCameraController class
        # self.assertIsInstance(result, SyntheticCameraController)


if __name__ == "__main__":
    unittest.main()
