# Standard Library Imports
import time
import unittest

# Third Party Imports
import pytest

# Local Imports
from navigate.model.devices.stages.tl_kcube_steppermotor import TLKSTStage
from navigate.model.devices.stages.tl_kcube_steppermotor import (
    build_TLKSTStage_connection,
)


@pytest.mark.hardware
class TestStageClass(unittest.TestCase):
    def setUp(self):
        # Create configuration for microscope stage
        self.serial_number = 26001318
        self.dv_units = 20000000
        self.real_units = 9.957067  # mm
        self.dv_per_mm = self.dv_units / self.real_units
        self.mm_per_dv = self.real_units / self.dv_units
        self.microscope_name = "test"
        self.config = {
            "configuration": {
                "microscopes": {
                    f"{self.microscope_name}": {
                        "stage": {
                            "hardware": {
                                "serial_number": str(self.serial_number),
                                "axes": "f",
                                "axes_mapping": [1],
                                "device_units_per_mm": self.dv_per_mm,
                                "f_min": 0,
                                "f_max": 25,
                            },
                            "f_min": 0,
                            "f_max": 25,
                        }
                    }
                }
            }
        }

        # Create the stage controller class
        self.stage = TLKSTStage(
            microscope_name=self.microscope_name,
            device_connection=None,
            configuration=self.config,
        )

    def tearDown(self):
        self.kcube_connection.KST_Close(str(self.serial_number))

    def test_homing(self):
        """Test the homing function"""
        self.stage.run_homing()

    def test_move_axis_absolute(self):
        distance = 0.100

        # Get the current position
        self.stage.report_position()
        start = self.stage.f_pos
        print(f"starting stage position = {start}")

        # Move the target distance
        target = start + distance
        self.stage.move_axis_absolute("f", target, True)

        # Read the position and report
        self.stage.report_position()
        end = self.stage.f_pos

        print(
            f"The final position in device units:{end/self.dv_per_mm}, "
            f"in real units:{end}mm,\n",
            f"Distance moved = {(end-start)}mm",
        )

    def test_move_absolute(self):
        distance = 0.200

        # Get the current position
        self.stage.report_position()
        start = self.stage.f_pos
        print(f"starting stage position = {start}")

        # Move the target distance
        target = start + distance
        self.stage.move_to_position(target, True)

        # Read the position and report
        self.stage.report_position()
        end = self.stage.f_pos

        print(
            f"The final position in device units:{end}, in real units:{end}mm,\n",
            f"Distance moved = {(end-start)}mm",
        )

    def test_move_to_position(self):
        distance = 0.100

        # Get the current position
        self.stage.report_position()
        start = self.stage.f_pos
        print(f"starting stage position = {start:.4f}")

        # move target distance, wait till done
        self.stage.move_to_position(start + distance, True)

        # get the final position
        self.stage.report_position()
        end = self.stage.f_pos
        print(f"End stage position = {end:.4f}", f"distance moved = {end-start:.6f}")


@pytest.mark.hardware
class TestKSTDeviceController(unittest.TestCase):
    def setUp(self):

        # test build connection function
        self.serial_number = 26001318

        # perform calibration
        dv_units = 20000000
        real_units = 9.957067  # mm
        self.dv_per_mm = dv_units / real_units

        # Open connection to stage
        self.kcube_connection = build_TLKSTStage_connection(self.serial_number)
        time.sleep(2)

        # Move the stage to middle of travel
        self.kcube_connection.KST_MoveToPosition(
            str(self.serial_number), int(12.5 * self.dv_per_mm)
        )

        time.sleep(5)

        current_pos = self.kcube_connection.KST_GetCurrentPosition(
            str(self.serial_number)
        )
        print(f"Stage currently at:{current_pos} dvUnits")

    def tearDown(self):
        self.kcube_connection.KST_Close(str(self.serial_number))

    def test_move(self):
        """Test how long commands take to execute move some distance"""
        distance = 12.5
        start = self.kcube_connection.KST_GetCurrentPosition(str(self.serial_number))
        final_position = start + distance

        self.kcube_connection.KST_MoveToPosition(
            str(self.serial_number), int(final_position * self.dv_per_mm)
        )
        time.sleep(5)

        tstart = time.time()
        self.kcube_connection.KST_MoveToPosition(str(self.serial_number), start)

        pos = None
        while pos != start:
            pos = self.kcube_connection.KST_GetCurrentPosition(str(self.serial_number))
            tend = time.time()

        print(f"it takes {tend - tstart:.3f}s to move {distance:.3}mm")

    def test_jog(self):
        """Test MoveJog"""
        # get the initial position
        start = self.kcube_connection.KST_GetCurrentPosition(str(self.serial_number))

        # Test a short jog
        self.kcube_connection.KST_MoveJog(str(self.serial_number), 1)
        time.sleep(2)
        self.kcube_connection.KST_MoveStop(str(self.serial_number))

        time.sleep(2)
        # read stage and make sure it moved
        jog_pos = self.kcube_connection.KST_GetCurrentPosition(str(self.serial_number))
        print(f"JogMove moved from {start} to {jog_pos}, starting jog back...")

        self.kcube_connection.KST_MoveJog(str(self.serial_number), 2)
        time.sleep(2)
        self.kcube_connection.KST_MoveStop(str(self.serial_number))

        time.sleep(2)
        end = self.kcube_connection.KST_GetCurrentPosition(str(self.serial_number))
        print(f"JogMove back moved from {jog_pos} to {end}")

    def test_polling(self):
        """Start polling, then run the jog test"""
        print("testing polling")
        # start polling
        self.kcube_connection.KST_StartPolling(str(self.serial_number), 100)

        # Run Jog during active polling
        self.test_jog()

        # End polling
        self.kcube_connection.KST_StopPolling(str(self.serial_number))
        # pos = self.kcube_connection.KST_GetCurrentPosition(str(self.serial_number))

        # print(f"final position: {pos}")
