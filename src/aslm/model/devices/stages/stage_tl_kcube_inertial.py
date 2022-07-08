from aslm.model.devices.stages.stage_base import StageBase

import importlib
import logging
import time

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class TLKIMStage(StageBase):
    def __init__(self, configuration, verbose):
        super().__init__(configuration, verbose, axes=['f'])  # only initialize the focus axis

        # Mapping from self.axes to corresponding KIM channels
        self.kim_axes = [1]

        self.kim_controller = importlib.import_module('aslm.model.devices.APIs.thorlabs.kcube_inertial')

        # Initialize
        self.kim_controller.TLI_BuildDeviceList()

        # Cheat for now by opening just the first stage of this type.
        # TODO: Pass this from the configuration file
        self.serialnum = self.kim_controller.TLI_GetDeviceListExt().split(',')[0]
        print(f"KIM S/N: {self.serialnum}")
        self.kim_controller.KIM_Open(self.serialnum)

    def __del__(self):
        self.stop()
        self.kim_controller.KIM_Close(self.serialnum)

    def report_position(self):
        """
        # Reports the position of the stage for all axes, and creates the hardware
        # position dictionary.
        """
        for i, ax in zip(self.kim_axes, self.axes):
            pos = self.kim_controller.KIM_GetCurrentPosition(self.serialnum, i)
            setattr(self, f"{ax}_pos", pos)

        # Update internal dictionaries
        self.update_position_dictionaries()

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

        self.kim_controller.KIM_MoveAbsolute(self.serialnum, axis_num, int(axis_abs))
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

        for ax, n in zip(self.axes, self.kim_axes):
            success = self.move_axis_absolute(ax, n, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"] - getattr(self, f"int_{ax}_pos_offset",
                                                                    0)  # TODO: should we default to 0?
                while (stage_pos != target_pos) and (i < n_tries):
                    stage_pos = self.kim_controller.KIM_GetCurrentPosition(self.serialnum, n)
                    i += 1
                    time.sleep(0.01)
                if stage_pos != target_pos:
                    success = False

        return success

    def stop(self):
        for i in self.kim_axes:
            self.kim_controller.KIM_MoveStop(self.serialnum, i)

    def get_abs_position(self, axis, move_dictionary):
        r"""
        Hack in a lack of bounds checking. TODO: Don't do this.
        """
        try:
            # Get all necessary attributes. If we can't we'll move to the error case.
            axis_abs = move_dictionary[f"{axis}_abs"] - getattr(self, f"int_{axis}_pos_offset",
                                                                0)  # TODO: should we default to 0?
            # axis_min, axis_max = getattr(self, f"{axis}_min"), getattr(self, f"{axis}_max")
            axis_min, axis_max = -1e6, 1e6

            # Check that our position is within the axis bounds, fail if it's not.
            if (axis_min > axis_abs) or (axis_max < axis_abs):
                log_string = f"Absolute movement stopped: {axis} limit would be reached!" \
                             "{axis_abs} is not in the range {axis_min} to {axis_max}."
                logger.info(log_string)
                print(log_string)
                # Return a ridiculous value to make it clear we've failed.
                # This is to avoid returning a duck type.
                return -1e50
            return axis_abs
        except (KeyError, AttributeError):
            return -1e50
