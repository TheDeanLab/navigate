import importlib
import logging
import time

from aslm.model.devices.stages.stage_base import StageBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def build_MCLStage_connection(serialnum):
    mcl_controller = importlib.import_module("aslm.model.devices.APIs.mcl.madlib")

    # Initialize
    mcl_controller.MCL_GrabAllHandles()

    handle = mcl_controller.MCL_GetHandleBySerial(int(serialnum))

    stage_connection = {"handle": handle, "controller": mcl_controller}

    return stage_connection


class MCLStage(StageBase):
    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(
            microscope_name, device_connection, configuration, device_id
        )  # only initialize the focus axis

        # Mapping from self.axes to corresponding MCL channels
        self.mcl_controller = device_connection["controller"]
        self.handle = device_connection["handle"]

    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
        for ax in self.axes:
            try:
                pos = self.mcl_controller.MCL_SingleReadN(ax, self.handle)
                setattr(self, f"{ax}_pos", pos)
            except self.mcl_controller.MadlibError as e:
                logger.debug(f"MCL - {e}")
                pass

        # Update internal dictionaries
        # self.update_position_dictionaries()

        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """

        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        self.mcl_controller.MCL_SingleWriteN(axis_abs, axis, self.handle)
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        for ax in self.axes:
            success = self.move_axis_absolute(ax, None, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"] - getattr(
                    self, f"int_{ax}_pos_offset", 0
                )  # TODO: should we default to 0?
                while (abs(stage_pos - target_pos) < 0.01) and (i < n_tries):
                    stage_pos = self.mcl_controller.MCL_SingleReadN(ax, self.handle)
                    i += 1
                    time.sleep(0.01)
                if abs(stage_pos - target_pos) > 0.01:
                    success = False

        return success

    def get_abs_position(self, axis, move_dictionary):
        r"""
        Hack in a lack of bounds checking. TODO: Don't do this.
        """
        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(
                self, f"int_{axis}_pos_offset", 0
            )  # TODO: should we default to 0?

            # axis_min, axis_max = getattr(self, f"{axis}_min"), getattr(self, f"{axis}_max")
            axis_min, axis_max = -1e6, 1e6

            # Check that our position is within the axis bounds, fail if it's not.
            if (axis_min > axis_abs) or (axis_max < axis_abs):
                log_string = (
                    f"Absolute movement stopped: {axis} limit would be reached!"
                    f"{axis_abs} is not in the range {axis_min} to {axis_max}."
                )
                logger.info(log_string)
                print(log_string)
                # Return a ridiculous value to make it clear we've failed.
                # This is to avoid returning a duck type.
                return -1e50
            return axis_abs
        except (KeyError, AttributeError):
            return -1e50
