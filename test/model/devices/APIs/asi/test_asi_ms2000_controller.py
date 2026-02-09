# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.

from unittest.mock import MagicMock, patch

from navigate.model.devices.APIs.asi.asi_MS2000_controller import MS2000Controller


def _build_controller():
    controller = MS2000Controller("COM1", 115200)
    controller.serial = MagicMock()
    controller.serial.is_open = True
    controller.report_to_console = MagicMock()
    return controller


def test_connect_to_serial_sets_buffer_size_on_windows():
    controller = _build_controller()
    with patch(
        "navigate.model.devices.APIs.asi.asi_MS2000_controller.platform.system",
        return_value="Windows",
    ):
        controller.connect_to_serial()
    controller.serial.set_buffer_size.assert_called_once_with(12800, 12800)


def test_connect_to_serial_skips_buffer_size_on_linux():
    controller = _build_controller()
    with patch(
        "navigate.model.devices.APIs.asi.asi_MS2000_controller.platform.system",
        return_value="Linux",
    ):
        controller.connect_to_serial()
    controller.serial.set_buffer_size.assert_not_called()
