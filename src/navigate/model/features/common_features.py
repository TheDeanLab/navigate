# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard library imports
import time
from functools import reduce
from threading import Lock
import copy

# Third party imports

# Local application imports
from .image_writer import ImageWriter
from navigate.tools.common_functions import VariableWithLock


class ChangeResolution:
    """
    ChangeResolution class for modifying the resolution mode of a microscope.

    This class provides functionality to change the resolution mode of a microscope by
    reconfiguring the microscope settings and updating the active microscope.

    Notes:
    ------
    - This class is used to change the resolution mode of a microscope by updating the
    microscope settings and configuring the active microscope accordingly.

    - The `resolution_mode` parameter specifies the desired resolution mode, and the
    `zoom_value` parameter specifies the zoom value to be set. These parameters can
    be adjusted to modify the microscope's configuration.

    - The `ChangeResolution` class is typically used to adapt the microscope's settings
    for different imaging requirements during microscopy experiments.

    - The resolution change process involves reconfiguring the microscope, updating the
    active microscope instance, and resuming data acquisition.

    - The `config_table` attribute is used to define the configuration for the
    resolution change process, including signal acquisition and cleanup steps.
    """

    def __init__(self, model, resolution_mode="high", zoom_value="N/A"):
        """Initialize the ChangeResolution class.


        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for resolution mode changes.
        resolution_mode : str, optional
            The desired resolution mode to set for the microscope. Default is "high".
        zoom_value : str, optional
            The zoom value to set for the microscope. Default is "N/A".
        """
        #: MicroscopeModel: The microscope model associated with the resolution change.
        self.model = model

        #: dict: A dictionary defining the configuration for the resolution change
        self.config_table = {
            "signal": {"main": self.signal_func, "cleanup": self.cleanup},
            "node": {"device_related": True},
        }

        #: str: The desired resolution mode to set for the microscope.
        self.resolution_mode = resolution_mode

        #: str: The zoom value to set for the microscope.
        self.zoom_value = zoom_value

    def signal_func(self):
        """Perform actions to change the resolution mode and update the active
         microscope.

        This method carries out actions to change the resolution mode of the microscope
         by reconfiguring the microscope settings, updating the active microscope, and
         resuming data acquisition.

        Returns:
        -------
        bool
            A boolean value indicating the success of the resolution change process.
        """
        # pause data thread
        self.model.pause_data_thread()
        # end active microscope
        self.model.active_microscope.end_acquisition()
        # prepare new microscope
        self.model.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ] = self.resolution_mode
        self.model.configuration["experiment"]["MicroscopeState"][
            "zoom"
        ] = self.zoom_value
        self.model.change_resolution(self.resolution_mode)
        self.model.logger.debug(f"current resolution is {self.resolution_mode}")
        self.model.logger.debug(
            f"current active microscope is {self.model.active_microscope_name}"
        )
        # prepare active microscope
        waveform_dict = self.model.active_microscope.prepare_acquisition()
        self.model.event_queue.put(("waveform", waveform_dict))
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        """Perform cleanup actions if needed.

        This method is responsible for performing cleanup actions if required after the
        resolution change process.
        """
        self.model.resume_data_thread()


class Snap:
    """Snap class for capturing data frames using a microscope.

    This class provides functionality to capture data frames using a microscope
    and log information about the camera and frame IDs.

    Notes:
    ------
    - This class is used to capture data frames using a microscope and log
    relevant information, such as the active camera and frame IDs.

    - The `Snap` class is typically used for capturing individual frames during
    microscopy experiments.

    - The data capture process involves capturing frames and logging
    camera-related information.

    - The `config_table` attribute is used to define the configuration for the
    data capture process, specifically the main data capture function.
    """

    def __init__(self, model):
        """Initialize the Snap class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for data capture.
        """
        #: MicroscopeModel: The microscope model associated with the data capture.
        self.model = model

        #: dict: A dictionary defining the configuration for the data capture process.
        self.config_table = {"data": {"main": self.data_func}}

    def data_func(self, frame_ids):
        """Capture data frames and log camera information.

        This method captures data frames using the microscope and logs information
        about the active camera and the provided frame IDs.

        Parameters:
        ----------
        frame_ids : list
            A list of frame IDs for which data frames should be captured.

        Returns:
        -------
        bool
            A boolean value indicating the success of the data capture process.
        """
        self.model.logger.info(
            f"the camera is:{self.model.active_microscope_name}, {frame_ids}"
        )
        return True


class WaitToContinue:
    """WaitToContinue class for synchronizing signal and data acquisition.

    This feature is used to synchronize signal and data acquisition processes, allowing
    the faster one to wait until the other one ends.

    Notes:
    ------
    - This class is used to synchronize signal and data acquisition processes in a
    controlled manner. It ensures that the faster process waits for the slower one to
    complete, improving synchronization during microscopy experiments.

    - The synchronization process involves using locks to control when the signal and
    data acquisition processes are allowed to proceed.

    - The `config_table` attribute defines the configuration for each stage of the
    synchronization process, including initialization, main execution, and cleanup
    steps.

    - The `first_enter_node` attribute tracks which process (signal or data) enters the
    node first to determine synchronization order.

    - The `WaitToContinue` class helps maintain order and synchronization between signal
    and data acquisition nodes in microscopy experiments.
    """

    def __init__(self, model):
        """Initialize the WaitToContinue class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for synchronization.
        """
        #: MicroscopeModel: The microscope model associated with the synchronization.
        self.model = model

        #: Lock: A lock for the signal acquisition process.
        self.pause_signal_lock = Lock()

        #: Lock: A lock for the data acquisition process.
        self.pause_data_lock = Lock()

        #: VariableWithLock: A variable to track which process enters the node first.
        self.first_enter_node = VariableWithLock(str)

        #: dict: A dictionary defining the configuration for the synchronization
        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "cleanup": self.cleanup,
            },
            "data": {
                "init": self.pre_data_func,
                "main": self.data_func,
                "cleanup": self.cleanup,
            },
        }

    def pre_signal_func(self):
        """Prepare for the signal acquisition stage and synchronize with data
        acquisition.

        This method prepares for the signal acquisition stage and synchronizes with
        the data acquisition process, ensuring that the slower process proceeds first.
        """
        with self.first_enter_node as first_enter_node:
            if first_enter_node.value == "":
                self.model.logger.debug("*** wait to continue enters signal " "first!")
                first_enter_node.value = "signal"
                if not self.pause_signal_lock.locked():
                    self.pause_signal_lock.acquire()
                if self.pause_data_lock.locked():
                    self.pause_data_lock.release()

    def signal_func(self):
        """Synchronize signal acquisition and release locks.

        This method synchronizes the signal acquisition process with data acquisition
        and releases any locks held.

        Returns:
        -------
        bool
           A boolean value indicating the success of the synchronization process.
        """
        self.model.logger.debug(f"--wait to continue: {self.model.frame_id}")
        if self.pause_signal_lock.locked():
            self.pause_signal_lock.acquire()
        elif self.pause_data_lock.locked():
            self.pause_data_lock.release()
        self.first_enter_node.value = ""
        self.model.logger.debug(f"--wait to continue is done!: {self.model.frame_id}")
        return True

    def pre_data_func(self):
        """Prepare for the data acquisition stage and synchronize with signal
        acquisition.

        This method prepares for the data acquisition stage and synchronizes with the
        signal acquisition process, ensuring that the slower process proceeds first.
        """
        with self.first_enter_node as first_enter_node:
            if first_enter_node.value == "":
                self.model.logger.debug(
                    "*** wait to continue enters data " "node first!"
                )
                first_enter_node.value = "data"
                if not self.pause_data_lock.locked():
                    self.pause_data_lock.acquire()
                if self.pause_signal_lock.locked():
                    self.pause_signal_lock.release()

    def data_func(self, frame_ids):
        """Synchronize data acquisition and release locks.

        This method synchronizes the data acquisition process with signal acquisition
        and releases any locks held.

        Parameters:
        ----------
        frame_ids : list
            A list of frame IDs for which data acquisition should be performed.

        Returns:
        -------
        bool
            A boolean value indicating the success of the synchronization process.
        """
        self.model.logger.debug(f"**wait to continue? {frame_ids}")
        if self.pause_data_lock.locked():
            self.pause_data_lock.acquire()
        elif self.pause_signal_lock.locked():
            self.pause_signal_lock.release()
        self.first_enter_node.value = ""
        self.model.logger.debug(f"**wait to continue is done! {frame_ids}")
        return True

    def cleanup(self):
        """Release any remaining locks during cleanup.

        This method releases any locks that may still be held during cleanup.
        """
        if self.pause_signal_lock.locked():
            self.pause_signal_lock.release()
        if self.pause_data_lock.locked():
            self.pause_data_lock.release()


class LoopByCount:
    """LoopByCount class for controlling signal and data acquisition loops.

    This class provides functionality to control signal and data acquisition loops by
    specifying the number of steps or frames to execute.

    Notes:
    ------
    - This class is used to control signal and data acquisition loops by specifying the
    number of steps or frames to execute. It allows for flexible control of the
    acquisition process.

    - The `steps` parameter can be an integer specifying the number of steps/frames
    directly or a string representing a configuration reference to determine the loop
    count dynamically.

    - The loop control process involves tracking the remaining steps/frames and deciding
     whether to continue the loop or exit based on the remaining count.

    - The `LoopByCount` class is useful for controlling the number of acquisitions
    during microscopy experiments, either by specifying a fixed count or by
    dynamically determining it from configuration references.
    """

    def __init__(self, model, steps=1):
        """Initialize the LoopByCount class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for loop control.
        steps : int or str, optional
            The number of steps or a configuration reference to determine the loop
            count. Default is 1.
        """
        #: MicroscopeModel: The microscope model associated with the loop control.
        self.model = model

        #: bool: A boolean value indicating whether to step by frame or by step.
        self.step_by_frame = True

        #: int: The remaining number of steps or frames.
        self.steps = steps
        if type(steps) is str:
            self.step_by_frame = False
            try:
                parameters = steps.split(".")
                config_ref = reduce((lambda pre, n: f"{pre}['{n}']"), parameters, "")
                exec(f"self.steps = int(self.model.configuration{config_ref})")
            except:  # noqa
                self.steps = 1

        #: int: The remaining number of steps.
        self.signals = self.steps

        #: int: The remaining number of frames.
        self.data_frames = self.steps

        #: dict: A dictionary defining the configuration for the loop control process.
        self.config_table = {
            "signal": {"main": self.signal_func},
            "data": {"main": self.data_func},
        }

    def signal_func(self):
        """Control the signal acquisition loop and update the remaining steps.

        This method controls the signal acquisition loop by decrementing the remaining
        steps. It determines whether to continue the loop or exit based on the
        remaining count.

        Returns:
        -------
        bool
            A boolean value indicating whether to continue the loop.
        """
        self.signals -= 1
        if self.signals <= 0:
            self.signals = self.steps
            return False
        return True

    def data_func(self, frame_ids):
        """Control the data acquisition loop and update the remaining frames or steps.

        This method controls the data acquisition loop by decrementing the remaining
        frames or steps. It determines whether to continue the loop or exit based on
        the remaining count.

        Parameters:
        ----------
        frame_ids : list
            A list of frame IDs for which data acquisition should be performed.

        Returns:
        -------
        bool
            A boolean value indicating whether to continue the loop.
        """
        if self.step_by_frame:
            self.data_frames -= len(frame_ids)
        else:
            self.data_frames -= 1
        if self.data_frames <= 0:
            self.data_frames = self.steps
            return False
        return True


class PrepareNextChannel:
    """PrepareNextChannel class for preparing microscopes for the next imaging channel.

    This class provides functionality to prepare multiple microscopes, including virtual
    microscopes and the primary microscope, for the next imaging channel during
    microscopy experiments.

    Notes:
    ------
    - This class is used to prepare multiple microscopes for the next imaging
    channel, ensuring that both virtual microscopes and the primary microscope are
    ready for the next step in microscopy experiments.

    - The `PrepareNextChannel` class is typically used to manage the preparation of
    microscopes before transitioning to a new imaging channel.

    - The channel preparation process involves calling the `prepare_next_channel()`
    method for each virtual microscope and the active microscope.

    - The `config_table` attribute is used to define the configuration for the
    channel preparation process, specifically the main preparation function.
    """

    def __init__(self, model):
        """Initialize the PrepareNextChannel class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for channel preparation.
        """
        #: MicroscopeModel: Microscope model associated with the channel preparation.
        self.model = model

        #: dict: A dictionary defining the configuration for the channel preparation
        self.config_table = {"signal": {"main": self.signal_func}}

    def signal_func(self):
        """Prepare virtual and active microscopes for the next imaging channel.

        This method prepares virtual microscopes, if any, followed by the active
        microscope for the next imaging channel.

        Returns:
        -------
        bool
            A boolean value indicating the success of the channel preparation process.
        """
        # prepare virtual microscopes before the primary microscope
        for microscope_name in self.model.virtual_microscopes:
            self.model.virtual_microscopes[microscope_name].prepare_next_channel()

        self.model.active_microscope.prepare_next_channel()

        return True


class MoveToNextPositionInMultiPositionTable:
    """MoveToNextPositionInMultiPositionTable class for advancing in a multi-position
    table.

    This class provides functionality to move to the next position in a multi-position
    table and control the data thread accordingly.

    Notes:
    ------
    - This class is used to advance to the next position in a multi-position table,
    controlling the data thread based on stage distance thresholds.

    - The `MoveToNextPositionInMultiPositionTable` class is typically used to automate
     position changes during microscopy experiments, ensuring proper data thread
     management.

    - The position control process involves moving to the next position in the table,
    pausing the data thread if necessary, and resuming it after the movement.

    - The `config_table` attribute defines the configuration for the position control
    process, including signal acquisition and cleanup steps.
    """

    def __init__(self, model):
        """Initialize the MoveToNextPositionInMultiPositionTable class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for position control.
        """
        #: MicroscopeModel: The microscope model associated with position control.
        self.model = model

        #: dict: A dictionary defining the configuration for the position control
        self.config_table = {
            "signal": {
                "main": self.signal_func,
                "cleanup": self.cleanup,
            },
            "node": {"device_related": True},
        }

        #: int: The current index of the position being acquired in the multi-position
        self.pre_z = None

        #: int: The current index of the position being acquired in the multi-position
        self.current_idx = 0

        #: dict: A dictionary defining the configuration for the position control
        self.multiposition_table = self.model.configuration["experiment"][
            "MultiPositions"
        ]

        #: int: The total number of positions in the multi-position table.
        self.position_count = self.model.configuration["experiment"]["MicroscopeState"][
            "multiposition_count"
        ]

        #: int: The stage distance threshold for pausing the data thread.
        self.stage_distance_threshold = 1000

    def signal_func(self):
        """Move to the next position in the multi-position table and control the data
        thread.

        This method advances to the next position in the multi-position table,
        controls the data thread based on stage distance thresholds, and updates
        position-related information.

        Returns:
        -------
        bool
            A boolean value indicating whether to continue the position control process.
        """
        self.model.logger.debug(
            f"multi-position current idx: {self.current_idx}, {self.position_count}"
        )
        if self.current_idx >= self.position_count:
            return False
        pos_dict = self.multiposition_table[self.current_idx]
        # pause data thread if necessary
        if self.current_idx == 0:
            temp = self.model.get_stage_position()
            pre_stage_pos = dict(
                map(
                    lambda k: (k, temp[f"{k}_pos"]),
                    ["x", "y", "z", "f", "theta"],
                )
            )
        else:
            pre_stage_pos = self.multiposition_table[self.current_idx - 1]
        delta_x = abs(pos_dict["x"] - pre_stage_pos["x"])
        delta_y = abs(pos_dict["y"] - pre_stage_pos["y"])
        delta_z = abs(pos_dict["z"] - pre_stage_pos["z"])
        delta_f = abs(pos_dict["f"] - pre_stage_pos["f"])
        should_pause_data_thread = any(
            distance > self.stage_distance_threshold
            for distance in [delta_x, delta_y, delta_z, delta_f]
        )
        if should_pause_data_thread:
            self.model.pause_data_thread()

        self.current_idx += 1
        abs_pos_dict = dict(map(lambda k: (f"{k}_abs", pos_dict[k]), pos_dict.keys()))
        self.model.logger.debug(f"MoveToNextPositionInMultiPosition: " f"{pos_dict}")
        self.model.move_stage(abs_pos_dict, wait_until_done=True)

        self.model.logger.debug("MoveToNextPositionInMultiPosition: move done")
        # resume data thread
        if should_pause_data_thread:
            self.model.resume_data_thread()
        self.model.active_microscope.central_focus = None
        if self.pre_z != pos_dict["z"]:
            self.pre_z = pos_dict["z"]
            return True

    def cleanup(self):
        """Cleanup method to resume the data thread.

        This method is responsible for resuming the data thread after position control.
        """
        self.model.resume_data_thread()


class StackPause:
    """StackPause class for pausing stack acquisition.

    This class provides functionality to pause stack acquisition for a specified
    number of timepoints or based on a defined pause time. It manages the data thread
    accordingly.

    Notes:
    ------
    - This class is used to pause stack acquisition for a specified number of timepoints
    or based on a defined pause time during microscopy experiments.

    - The `StackPause` class allows for flexible control of stack acquisition pauses,
    ensuring synchronization with data acquisition.

    - The stack pause control process involves managing the data thread, calculating
    pause times, and handling stack acquisition pauses.

    - The `config_table` attribute defines the configuration for the stack pause control
    process, specifically the main pause function.
    """

    def __init__(self, model, pause_num="experiment.MicroscopeState.timepoints"):
        """Initialize the StackPause class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for stack acquisition control.

        pause_num : int or str, optional
            The number of timepoints to pause stack acquisition or a configuration
            reference to determine the pause count dynamically. Default is
            "experiment.MicroscopeState.timepoints".
        """
        self.model = model
        self.pause_num = pause_num
        if type(pause_num) is str:
            try:
                parameters = pause_num.split(".")
                config_ref = reduce((lambda pre, n: f"{pre}['{n}']"), parameters, "")
                exec(f"self.pause_num = int(self.model.configuration{config_ref})")
            except:  # noqa
                self.pause_num = 1
        self.config_table = {"signal": {"main": self.signal_func}}

    def signal_func(self):
        """Pause stack acquisition based on timepoints or pause time and manage the
        data thread.

        This method pauses stack acquisition based on the remaining timepoints or
        defined pause time. It manages the data thread accordingly during the pause.
        """
        self.pause_num -= 1
        if self.pause_num <= 0:
            return
        pause_time = float(
            self.model.configuration["experiment"]["MicroscopeState"]["stack_pause"]
        )
        if pause_time <= 0:
            return
        current_channel = f"channel_{self.model.active_microscope.current_channel}"
        current_exposure_time = (
            float(
                self.model.configuration["experiment"]["MicroscopeState"]["channels"][
                    current_channel
                ]["camera_exposure_time"]
            )
            / 1000.0
        )
        if pause_time < 5 * current_exposure_time:
            time.sleep(pause_time)
        else:
            self.model.pause_data_thread()
            pause_time -= 2 * current_exposure_time
            while pause_time > 0:
                pt = min(pause_time, 0.1)
                time.sleep(pt)
                if self.model.stop_acquisition:
                    self.model.resume_data_thread()
                    return
                pause_time -= 0.1
            self.model.resume_data_thread()


class ZStackAcquisition:
    """ZStackAcquisition class for controlling z-stack acquisition in microscopy.

    This class provides functionality to control z-stack acquisition, including managing
    z and focus positions, acquiring image data, and handling multi-channel
    acquisitions.

    Notes:
    ------
    - This class is used to control z-stack acquisition during microscopy experiments,
    allowing for position cycling, multi-channel acquisitions, and image saving.

    - The z-stack acquisition process involves initializing parameters, controlling
    position and focus movements, handling data acquisition, and managing data threads.

    - The `config_table` attribute defines the configuration for the z-stack acquisition
    process, including signal acquisition, data handling, and node type.
    """

    def __init__(
        self, model, get_origin=False, saving_flag=False, saving_dir="z-stack"
    ):
        """Initialize the ZStackAcquisition class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for z-stack acquisition control.
        get_origin : bool, optional
            Flag to determine whether to get the z and focus origin positions.
            Default is False.
        saving_flag : bool, optional
            Flag to enable image saving during z-stack acquisition. Default is False.
        saving_dir : str, optional
            The sub-directory for saving z-stack images. Default is "z-stack".

        """
        #: MicroscopeModel: The microscope model associated with z-stack acquisition.
        self.model = model

        #: bool: Flag to determine whether to get the z and focus origin positions.
        self.get_origin = get_origin

        #: int: The number of z steps in the z-stack.
        self.number_z_steps = 0

        #: float: The start z position for the z-stack.
        self.start_z_position = 0

        #: float: The start focus position for the z-stack.
        self.start_focus = 0

        #: float: The z step size for the z-stack.
        self.z_step_size = 0

        #: float: The z stack distance for the z-stack.
        self.focus_step_size = 0

        #: dict: A dictionary defining the multi-position table for z-stack acquisition.
        self.positions = {}

        #: int: The current index of the position being acquired in the multi-position
        self.current_position_idx = 0

        #: int: The z position of the channel being acquired in the z-stack
        self.current_z_position = 0

        #: int: The f position of the channel being acquired in the z-stack
        self.current_focus_position = 0

        #: bool: Flag to determine whether to move to a new position
        self.need_to_move_new_position = True

        #: bool: Flag to determine whether to move the z position
        self.need_to_move_z_position = True

        #: int: The number of times the z position has been moved
        self.z_position_moved_time = 0

        #: dict: A dictionary defining the defocus values between channels
        self.defocus = None

        #: str: The stack cycling mode for z-stack acquisition.
        self.stack_cycling_mode = "per_stack"

        #: int: The number of channels in the z-stack.
        self.channels = 1

        #: ImageWriter: An image writer object for saving z-stack images.
        self.image_writer = None
        if saving_flag:
            self.image_writer = ImageWriter(model, sub_dir=saving_dir)

        #: dict: A dictionary defining the configuration for the z-stack acquisition
        self.config_table = {
            "signal": {
                "init": self.pre_signal_func,
                "main": self.signal_func,
                "end": self.signal_end,
            },
            "data": {
                "init": self.pre_data_func,
                "main": self.in_data_func,
                "end": self.end_data_func,
                "cleanup": self.cleanup_data_func,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_signal_func(self):
        """Initialize z-stack acquisition parameters before the signal stage.

        This method initializes z-stack acquisition parameters, including position,
        focus, and data thread management, before the signal stage.
        """
        microscope_state = self.model.configuration["experiment"]["MicroscopeState"]

        self.stack_cycling_mode = microscope_state["stack_cycling_mode"]

        # get available channels
        self.channels = microscope_state["selected_channels"]
        #: int: The current channel being acquired in the z-stack
        self.current_channel_in_list = 0

        self.number_z_steps = int(microscope_state["number_z_steps"])
        self.start_z_position = float(microscope_state["start_position"])
        # end_z_position = float(microscope_state["end_position"])
        self.z_step_size = float(microscope_state["step_size"])
        #: float: The z stack distance for the z-stack.
        self.z_stack_distance = abs(
            self.start_z_position - float(microscope_state["end_position"])
        )

        self.start_focus = float(microscope_state["start_focus"])
        end_focus = float(microscope_state["end_focus"])
        self.focus_step_size = (end_focus - self.start_focus) / self.number_z_steps
        #: float: The focus stack distance for the z-stack.
        self.f_stack_distance = abs(end_focus - self.start_focus)

        # restore z, f
        pos_dict = self.model.get_stage_position()
        self.model.logger.debug(f"**** ZStack get stage position: {pos_dict}")
        #: float: The z position of the channel being acquired in the z-stack
        self.restore_z = pos_dict["z_pos"]
        #: float: The f position of the channel being acquired in the z-stack
        self.restore_f = pos_dict["f_pos"]

        if bool(microscope_state["is_multiposition"]):
            self.positions = self.model.configuration["experiment"]["MultiPositions"]
        else:
            self.positions = [
                {
                    "x": float(pos_dict["x_pos"]),
                    "y": float(pos_dict["y_pos"]),
                    "z": float(
                        microscope_state.get(
                            "stack_z_origin",
                            pos_dict["z_pos"],
                        )
                        if not self.get_origin
                        else pos_dict["z_pos"]
                    ),
                    "theta": float(pos_dict["theta_pos"]),
                    "f": float(
                        microscope_state.get(
                            "stack_focus_origin",
                            pos_dict["f_pos"],
                        )
                        if not self.get_origin
                        else pos_dict["f_pos"]
                    ),
                }
            ]

        # Setup next channel down here, to ensure defocus isn't merged into
        # restore f_pos, positions
        self.model.active_microscope.central_focus = None
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()

        self.model.logger.debug(
            f"*** ZStack pre_signal_func: {self.positions}, {self.start_focus}, "
            f"{self.start_z_position}"
        )
        self.current_position_idx = 0
        self.z_position_moved_time = 0
        self.need_to_move_new_position = True
        self.need_to_move_z_position = True
        #: bool: Flag to determine whether to pause the data thread.
        self.should_pause_data_thread = False
        # TODO: distance > 1000 should not be hardcoded and somehow related to
        #  different kinds of stage devices.
        self.stage_distance_threshold = 1000

        self.defocus = [
            v["defocus"]
            for v in microscope_state["channels"].values()
            if v["is_selected"]
        ]

    def signal_func(self):
        """Control z-stack acquisition, move positions, and manage data threads.

        This method controls the z-stack acquisition process, including moving positions
        and focus, managing data threads, and handling data acquisition during the
        signal stage.

        Returns:
        -------
        bool
            A boolean value indicating whether to continue the z-stack acquisition
            process.
        """
        if self.model.stop_acquisition:
            return False
        data_thread_is_paused = False
        # move stage X, Y, Theta
        if self.need_to_move_new_position:
            self.need_to_move_new_position = False

            # calculate first z, f position
            self.current_z_position = (
                self.start_z_position + self.positions[self.current_position_idx]["z"]
            )
            self.current_focus_position = (
                self.start_focus + self.positions[self.current_position_idx]["f"]
            )
            if self.defocus is not None:
                self.current_focus_position += self.defocus[
                    self.current_channel_in_list
                ]

            # calculate delta_x, delta_y
            # TODO: Here.
            pos_dict = dict(
                map(
                    lambda ax: (
                        f"{ax}_abs",
                        self.positions[self.current_position_idx][ax],
                    ),
                    ["x", "y", "theta"],
                )
            )

            if self.current_position_idx > 0:
                delta_x = (
                    self.positions[self.current_position_idx]["x"]
                    - self.positions[self.current_position_idx - 1]["x"]
                )
                delta_y = (
                    self.positions[self.current_position_idx]["y"]
                    - self.positions[self.current_position_idx - 1]["y"]
                )
                delta_z = (
                    self.positions[self.current_position_idx]["z"]
                    - self.positions[self.current_position_idx - 1]["z"]
                    + self.z_stack_distance
                )
                delta_f = (
                    self.positions[self.current_position_idx]["f"]
                    - self.positions[self.current_position_idx - 1]["f"]
                    + self.f_stack_distance
                )
            else:
                delta_x = 0
                delta_y = 0
                delta_z = 0
                delta_f = 0

            # displacement = [delta_z, delta_f, delta_x, delta_y]
            # Check the distance between current position and previous position,
            # if it is too far, then we can call self.model.pause_data_thread() and
            # self.model.resume_data_thread() after the stage has completed the move
            # to the next position.

            self.should_pause_data_thread = any(
                distance > self.stage_distance_threshold
                for distance in [delta_x, delta_y, delta_z, delta_f]
            )
            if self.should_pause_data_thread:
                self.model.pause_data_thread()
                data_thread_is_paused = True
            pos_dict22 = self.model.get_stage_position()
            self.model.logger.debug(f"**** ZStack get stage position before move: {pos_dict22}")

            self.model.move_stage(pos_dict, wait_until_done=True)
            self.model.logger.debug(f"*** ZStack move stage: {pos_dict}")
            pos_dict2 = self.model.get_stage_position()
            self.model.logger.debug(f"**** ZStack get stage position after move: {pos_dict2}")

        if self.need_to_move_z_position:
            # move z, f
            # self.model.pause_data_thread()

            self.model.logger.debug(
                f"*** Zstack move stage: (z: {self.current_z_position}), "
                f"(f: {self.current_focus_position})"
            )

            if self.should_pause_data_thread and not data_thread_is_paused:
                self.model.pause_data_thread()

            pos_dict222 = self.model.get_stage_position()
            self.model.logger.debug(f"**** ZStack get stage position before move: {pos_dict222}")

            self.model.move_stage(
                {
                    "z_abs": self.current_z_position,
                    "f_abs": self.current_focus_position,
                },
                wait_until_done=True,
            )

            pos_dict3 = self.model.get_stage_position()
            self.model.logger.debug(f"**** ZStack get stage position after move: {pos_dict3}")

        if self.should_pause_data_thread:
            self.model.resume_data_thread()
            self.should_pause_data_thread = False

        return True

    def signal_end(self):
        """Handle the end of the signal stage and position cycling.

        This method handles the end of the signal stage, including position cycling and
        channel updates for multi-channel acquisitions.

        Returns:
        -------
        bool
            A boolean value indicating whether to end the current node.
        """

        # end this node
        if self.model.stop_acquisition:
            return True

        if self.stack_cycling_mode != "per_stack":
            # update channel for each z position in 'per_slice'
            if self.defocus is not None:
                self.current_focus_position -= self.defocus[
                    self.current_channel_in_list
                ]
            self.update_channel()
            self.need_to_move_z_position = self.current_channel_in_list == 0

        # in 'per_slice', move to next z position if all the channels have been acquired
        if self.need_to_move_z_position:
            # next z, f position
            self.current_z_position += self.z_step_size
            self.current_focus_position += self.focus_step_size

            # update z position moved time
            self.z_position_moved_time += 1

        # decide whether to move X,Y,Theta
        if self.z_position_moved_time >= self.number_z_steps:
            self.z_position_moved_time = 0
            # calculate first z, f position
            self.current_z_position = (
                self.start_z_position + self.positions[self.current_position_idx]["z"]
            )
            self.current_focus_position = (
                self.start_focus + self.positions[self.current_position_idx]["f"]
            )
            if (
                self.z_stack_distance > self.stage_distance_threshold
                or self.f_stack_distance > self.stage_distance_threshold
            ):
                self.should_pause_data_thread = True

            # after running through a z-stack, update channel
            if self.stack_cycling_mode == "per_stack":
                self.update_channel()
                # if run through all the channels, move to next position
                if self.current_channel_in_list == 0:
                    self.need_to_move_new_position = True
            else:
                self.need_to_move_new_position = True

            if self.need_to_move_new_position:
                # move to next position
                self.current_position_idx += 1

        if self.current_position_idx >= len(self.positions):
            self.current_position_idx = 0

            pos_dict2222 = self.model.get_stage_position()
            self.model.logger.debug(f"**** ZStack get stage position before move: {pos_dict2222}")
            # restore z
            self.model.move_stage(
                {"z_abs": self.restore_z, "f_abs": self.restore_f},
                wait_until_done=False,
            )  # Update position

            pos_dict4 = self.model.get_stage_position()
            self.model.logger.debug(f"**** ZStack get stage position after move: {pos_dict4}")
            return True

        return False

    def update_channel(self):
        """Update the active channel during multi-channel acquisition.

        This method updates the active channel for multi-channel acquisitions, allowing
        cycling through channels.
        """
        self.current_channel_in_list = (
            self.current_channel_in_list + 1
        ) % self.channels
        # not update DAQ tasks if there is a NI Galvo stage
        self.model.active_microscope.prepare_next_channel()
        if self.defocus is not None:
            self.current_focus_position += self.defocus[self.current_channel_in_list]

    def pre_data_func(self):
        """Initialize data-related parameters before data acquisition.

        This method initializes data-related parameters before data acquisition,
        including the count of received and expected frames.
        """

        self.received_frames = 0
        self.total_frames = self.channels * self.number_z_steps * len(self.positions)

    def in_data_func(self, frame_ids):
        """Handle incoming data frames during data acquisition.

        This method handles incoming data frames during data acquisition, updating the
        count of received frames and saving images if enabled.

        Parameters:
        ----------
        frame_ids : list
            A list of frame IDs received during data acquisition.

        """
        self.model.mark_saving_flags(frame_ids)
        self.received_frames += len(frame_ids)
        if self.image_writer is not None:
            self.image_writer.save_image(frame_ids)

    def end_data_func(self):
        """Check if all expected data frames have been received.

        This method checks whether all expected data frames have been received during
        data acquisition.

        Returns:
        -------
        bool
            A boolean value indicating whether all expected data frames have been
            received.
        """

        return self.received_frames >= self.total_frames

    def cleanup_data_func(self):
        """Perform cleanup actions after data acquisition, if image saving is enabled.

        This method performs cleanup actions after data acquisition, such as cleaning up
         image writing, if image saving is enabled.
        """
        if self.image_writer:
            self.image_writer.cleanup()


class FindTissueSimple2D:
    """FindTissueSimple2D class for detecting tissue and gridding out the imaging
    space in  2D.

    This class is responsible for detecting tissue, thresholding, and gridding out the
    space for 2D imaging. It processes acquired frames to determine regions of
    interest (tissue), calculates offsets, and generates grid positions for imaging.
    """

    def __init__(
        self,
        model,
        overlap=0.1,
        target_resolution="Nanoscale",
        target_zoom="N/A",
    ):
        """Initialize the FindTissueSimple2D class.

        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for tissue detection and gridding.
        overlap : float, optional
            The overlap percentage between grid tiles. Default is 0.1 (10%).
        target_resolution : str, optional
            The target resolution for imaging (e.g., "Nanoscale"). Default is
            "Nanoscale".
        target_zoom : str, optional
            The target zoom level for imaging. Default is "N/A".
        """
        #: MicroscopeModel: The microscope model associated with tissue detection and
        self.model = model

        #: dict: A dictionary defining the configuration for tissue detection and
        self.config_table = {"signal": {}, "data": {"main": self.data_func}}

        #: float: The overlap percentage between grid tiles.
        self.overlap = overlap

        #: str: The target resolution for imaging (e.g., "Nanoscale").
        self.target_resolution = target_resolution

        #: str: The target zoom level for imaging.
        self.target_zoom = target_zoom

    def data_func(self, frame_ids):
        """Process acquired frames for tissue detection, thresholding, and grid
        calculation.

        This method processes acquired frames to detect tissue regions, apply
        thresholding, and calculate grid positions for imaging. It performs the
        following steps:
        - Downsamples the acquired image based on desired magnification change.
        - Applies thresholding using Otsu's method.
        - Calculates the bounding box of the tissue region.
        - Computes offsets for gridding based on acquired and target resolutions.
        - Grids out the 2D imaging space based on the specified overlap percentage.

        Parameters:
        ----------
        frame_ids : list
            A list of frame IDs corresponding to acquired frames.
        """

        from skimage import filters
        from skimage.transform import downscale_local_mean
        import numpy as np
        from navigate.tools.multipos_table_tools import (
            compute_tiles_from_bounding_box,
            calc_num_tiles,
        )

        for idx in frame_ids:
            img = self.model.data_buffer[idx]

            # Get current mag
            microscope_name = self.model.configuration["experiment"]["MicroscopeState"][
                "microscope_name"
            ]
            zoom = self.model.configuration["experiment"]["MicroscopeState"]["zoom"]
            curr_pixel_size = self.model.configuration["configuration"]["microscopes"][
                microscope_name
            ]["zoom"][zoom]["pixel_size"]
            # get target pixel size
            pixel_size = self.model.configuration["configuration"]["microscopes"][
                self.target_resolution
            ]["zoom"][self.target_zoom]["pixel_size"]

            # Downsample according to the desired magnification change. Note, we
            # could downsample by whatever we want.
            ds = int(curr_pixel_size / pixel_size)
            ds_img = downscale_local_mean(img, (ds, ds))

            # Threshold
            thresh_img = ds_img > filters.threshold_otsu(img)

            # Find the bounding box
            # In the real-deal, non-transposed image, x increase corresponds to a
            # decrease in row number y increase responds to an increase in row number
            # This means the smallest x coordinate is actually the largest
            x, y = np.where(thresh_img)
            # + 0.5 accounts for center of FOV
            x_start, x_end = -curr_pixel_size * ds * (
                np.max(x) + 0.5
            ), -curr_pixel_size * ds * (np.min(x) + 0.5)
            y_start, y_end = curr_pixel_size * ds * (
                np.min(y) + 0.5
            ), curr_pixel_size * ds * (np.max(y) + 0.5)
            xd, yd = abs(x_start - x_end), y_end - y_start

            # grab z, theta, f starting positions
            z_start = self.model.configuration["experiment"]["StageParameters"]["z"]
            r_start = self.model.configuration["experiment"]["StageParameters"]["theta"]
            if self.target_resolution == "Nanoscale":
                f_start = 0  # very different range of focus values in high-res
            else:
                f_start = self.model.configuration["experiment"]["StageParameters"]["f"]

            # Update x and y start to initialize from the upper-left corner of the
            # current image, since this is how np.where indexed them. The + 0.5 in
            # x_start/y_start calculation shifts their starts back to the center of the
            # field of view.
            curr_fov_x = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "x_pixels"
                    ]
                )
                * curr_pixel_size
            )
            curr_fov_y = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "y_pixels"
                    ]
                )
                * curr_pixel_size
            )
            x_start += (
                self.model.configuration["experiment"]["StageParameters"]["x"]
                + curr_fov_x / 2
            )
            y_start += (
                self.model.configuration["experiment"]["StageParameters"]["y"]
                - curr_fov_y / 2
            )

            # stage offset
            x_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["x_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["x_offset"]
            )
            y_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["y_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["y_offset"]
            )
            z_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["z_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["z_offset"]
            )
            r_start += float(
                self.model.configuration["configuration"]["microscopes"][
                    self.target_resolution
                ]["stage"]["r_offset"]
            ) - float(
                self.model.configuration["configuration"]["microscopes"][
                    microscope_name
                ]["stage"]["r_offset"]
            )

            # grid out the 2D space
            fov_x = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "x_pixels"
                    ]
                )
                * pixel_size
            )
            fov_y = (
                float(
                    self.model.configuration["experiment"]["CameraParameters"][
                        "y_pixels"
                    ]
                )
                * pixel_size
            )
            x_tiles = calc_num_tiles(xd, self.overlap, fov_x)
            y_tiles = calc_num_tiles(yd, self.overlap, fov_y)

            table_values = compute_tiles_from_bounding_box(
                x_start,
                x_tiles,
                fov_x,
                self.overlap,
                y_start,
                y_tiles,
                fov_y,
                self.overlap,
                z_start,
                1,
                0,
                self.overlap,
                r_start,
                1,
                0,
                self.overlap,
                f_start,
                1,
                0,
                self.overlap,
            )

            self.model.event_queue.put(("multiposition", table_values))
