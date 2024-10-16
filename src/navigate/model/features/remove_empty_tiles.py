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
#

# Standard Library Imports
from math import ceil
from queue import Queue

# Third Party Imports

# Local Imports
from navigate.model.analysis.boundary_detect import find_tissue_boundary_2d


def detect_tissue(image_data, percentage=0.0):
    """Detect tissue in an image and determine if it exceeds a specified percentage.

    This function takes an image in the form of image data and detects tissue
    within the image. It calculates the percentage of tissue area with respect
    to the total image area using a sliding window approach.

    Parameters:
    -----------
    image_data : ndarray
        A NumPy array representing the image data. The image should be
        preprocessed and ready for tissue detection.

    percentage : float, optional (default: 0.0)
        The minimum required percentage of tissue in the image for it to be
        considered as containing tissue. If the detected tissue percentage is
        greater than or equal to this value, the function returns True; otherwise,
        it returns False.

    Returns:
    --------
    bool
        True if the detected tissue percentage is greater than or equal to the
        specified percentage; False otherwise.

    Notes:
    ------
    - The function applies a sliding window approach to count tissue squares
      within the image.
    - It calculates the tissue percentage by dividing the number of tissue squares
      by the total possible squares in the image.
    - The width of the sliding window is determined by the 'width' variable.

    Example:
    --------
    Given an image data array and a percentage threshold of 0.5:
    ```
    image_data = np.array([[0, 0, 1, 1, 1],
                           [0, 0, 0, 1, 1],
                           [1, 0, 0, 0, 0],
                           [1, 1, 0, 0, 1]])

    result = detect_tissue(image_data, 0.5)
    ```

    The function would return True, as the detected tissue percentage in the
    image (10 out of 20 squares) is greater than or equal to 0.5.
    """

    width = 50
    boundary = find_tissue_boundary_2d(image_data, width)
    tissue_squares = 0
    for row in boundary:
        if row:
            tissue_squares += row[1] - row[0] + 1
    return (
        tissue_squares
        / (ceil(image_data.shape[0] / width) * ceil(image_data.shape[1] / width))
        > percentage
    )


def detect_tissue2(image_data, percentage=0.0):
    """Detect Tissue in an Image (Version 2).

    This function analyzes an image to determine if it contains tissue based on
    a specified percentage threshold. Unlike other tissue detection methods,
    this version (Version 2) always returns `False`, indicating no tissue is detected.

    Parameters:
    -----------
    image_data : numpy.ndarray
        The input image data as a NumPy array.

    percentage : float, optional
        The percentage threshold for tissue detection. Default is 0.0,
        indicating that no tissue detection is performed.

    Returns:
    --------
    bool
        Always returns `False`, indicating no tissue detection.

    Notes:
    ------
    - This function is a placeholder and always returns `False`.
    - For actual tissue detection, consider using other functions or methods.
    """

    return False


class DetectTissueInStack:
    """Detect Tissue in a Stack of Images.

    This class is used to detect tissue in a stack of images by moving the microscope
    stage through different Z and F positions and analyzing each frame for tissue
    presence.
    """

    def __init__(self, model, planes=1, percentage=0.75, detect_func=None):
        """Initialize the DetectTissueInStack class.

        Parameters:
        -----------
        model : object
            The model object representing the microscope.
        planes : int, optional
            The number of Z planes to capture in the stack. Default is 1.
        percentage : float, optional
            The minimum percentage of tissue required to consider a frame as having
            tissue. Default is 0.75 (75%).
        detect_func : function, optional
            The custom tissue detection function to use. If not specified, the default
            `detect_tissue` function will be used.
        """

        #: navigate.model.Model: The model object representing the microscope.
        self.model = model

        #: int: The number of Z planes to capture in the stack.
        self.planes = int(planes)

        #: float: The minimum percentage of tissue required to consider a frame as
        # having tissue.
        self.percentage = float(percentage)

        # if not specify a detect function, use the default one
        if detect_func is None:
            #: function: The tissue detection function used to analyze image frames.
            self.detect_func = detect_tissue
        else:
            self.detect_func = detect_func

        #: dict: A dictionary specifying the configuration for signal and data
        # functions.
        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "main": self.in_func_signal,
                "end": self.end_func_signal,
            },
            "data": {
                "init": self.pre_func_data,
                "main": self.in_func_data,
                "end": self.end_func_data,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_func_signal(self):
        """Initialization function for signal processing.

        This method is called at the beginning of the signal processing phase
        and initializes the necessary parameters for moving the microscope stage.
        """

        microscope_config = self.model.configuration["experiment"]["MicroscopeState"]
        # get current z and f position
        pos = self.model.get_stage_position()

        #: float: The current Z position of the microscope stage.
        self.current_z_pos = pos["z_pos"] + float(microscope_config["start_position"])

        #: float: The current F position of the microscope stage.
        self.current_f_pos = pos["f_pos"] + float(microscope_config["start_focus"])

        # calculate Z and F stage step sizes
        z_pos_range = float(microscope_config["end_position"]) - float(
            microscope_config["start_position"]
        )
        f_pos_range = float(microscope_config["end_focus"]) - float(
            microscope_config["start_focus"]
        )

        #: int: The number of Z planes to capture in the stack.
        if self.planes == 1:
            self.current_z_pos = self.current_z_pos + z_pos_range / 2
            self.current_f_pos = self.current_f_pos + f_pos_range / 2
        else:
            #: float: The Z stage step size.
            self.z_step = z_pos_range / (self.planes - 1)

            #: float: The F stage step size.
            self.f_step = f_pos_range / (self.planes - 1)

        #: int: The current scan number.
        self.scan_num = 0

    def in_func_signal(self):
        """Signal processing function to move the microscope stage.

        This method is called during the signal processing phase to move the microscope
         stage to the specified Z and F positions. It increments the Z and F
         positions for each scan.
        """

        # move to Z anf F position
        self.model.logger.debug(
            f"move to position (z, f): ({self.current_z_pos}, {self.current_f_pos}), "
            f"{self.scan_num}, {self.model.frame_id}"
        )
        self.model.move_stage(
            {"z_abs": self.current_z_pos, "f_abs": self.current_f_pos},
            wait_until_done=True,
        )
        self.scan_num += 1

    def end_func_signal(self):
        """Signal processing function to end the signal phase.

        This method is called to determine whether the signal phase should end.
        It checks if the specified number of Z planes have been scanned.

        Returns:
        --------
        bool
            True if the signal phase should end, False otherwise.
        """
        self.model.logger.debug(
            f"*** detect tissue signal end function: " f"{self.scan_num}"
        )
        if self.scan_num >= self.planes:
            return True
        self.current_z_pos += self.z_step
        self.current_f_pos += self.f_step
        return False

    def pre_func_data(self):
        """Initialization function for data processing.

        This method is called at the beginning of the data processing phase and
        initializes variables for tracking received frames and tissue detection.

        Returns:
        --------
        None
        """
        #: int: The number of received frames.
        self.received_frames = 0

        #: bool: Flag indicating whether tissue is detected.
        self.has_tissue_flag = False

    def in_func_data(self, frame_ids):
        """Data processing function to analyze image frames for tissue presence.

        This method is called during the data processing phase to analyze image frames
        for tissue presence. It checks if any of the received frames contain
        sufficient tissue.

        Parameters:
        -----------
        frame_ids : list
            A list of frame IDs to analyze.

        Returns:
        --------
        bool
            True if tissue is detected, False otherwise.
        """

        if not self.has_tissue_flag:
            for frame_id in frame_ids:
                # check if the frame has tissue
                r = self.detect_func(self.model.data_buffer[frame_id], self.percentage)
                if r:
                    self.model.logger.debug(
                        f"*** this frame has enough percentage of tissue!{frame_id}"
                    )
                    self.has_tissue_flag = True
                    break
        self.received_frames += len(frame_ids)
        return self.has_tissue_flag

    def end_func_data(self):
        """Data processing function to end the data phase.

        This method is called to determine whether the data phase should end. It checks
         if the specified number of frames have been received.

        Returns:
        --------
        bool
            True if the data phase should end, False otherwise.
        """
        return self.received_frames >= self.planes


class DetectTissueInStackAndReturn(DetectTissueInStack):
    def __init__(self, model, planes=1, percentage=0.75, detect_func=None):
        """Initialize the DetectTissueInStackAndReturn class.

        Parameters:
        -----------
        model : object
            The model object representing the microscope.
        planes : int, optional
            The number of Z planes to capture in the stack. Default is 1.
        percentage : float, optional
            The minimum percentage of tissue required to consider a frame as having
            tissue. Default is 0.75 (75%).
        detect_func : function, optional
            The custom tissue detection function to use. If not specified, the default
            `detect_tissue` function will be used.
        """
        super().__init__(model, planes, percentage, detect_func)

        self.detect_tissue_queue = Queue()
        self.result_sent_flag = False
        self.config_table["signal"]["main-response"] = self.signal_response_func

    def pre_func_data(self):
        """Initialization function for data processing.

        This method is called at the beginning of the data processing phase and
        initializes variables for tracking received frames and tissue detection.

        Returns:
        --------
        None
        """
        super().pre_func_data()
        self.result_sent_flag = False

    def signal_response_func(self):
        """Return the result if there is an tissue"""
        if self.scan_num >= self.planes:
            self.model.logger.debug("detection signal waiting for result!")
            has_tissue = self.detect_tissue_queue.get()
            self.model.logger.debug(f"detection signal get result: {has_tissue}")
            return has_tissue

    def in_func_data(self, frame_ids):
        """Data processing function to analyze image frames for tissue presence.

        This method is called during the data processing phase to analyze image frames
        for tissue presence. It checks if any of the received frames contain
        sufficient tissue.

        Parameters:
        -----------
        frame_ids : list
            A list of frame IDs to analyze.

        Returns:
        --------
        bool
            True if tissue is detected, False otherwise.
        """
        super().in_func_data(frame_ids)

        if self.has_tissue_flag and not self.result_sent_flag:
            self.model.logger.debug(
                f"detection data send result: {self.has_tissue_flag}"
            )
            self.detect_tissue_queue.put(True)
            self.result_sent_flag = True
        return self.has_tissue_flag

    def end_func_data(self):
        """Data processing function to end the data phase.

        This method is called to determine whether the data phase should end. It checks
         if the specified number of frames have been received.

        Returns:
        --------
        bool
            True if the data phase should end, False otherwise.
        """
        if self.received_frames >= self.planes:
            if not self.result_sent_flag:
                self.model.logger.debug(
                    f"detection data send result: {self.has_tissue_flag}"
                )
                self.detect_tissue_queue.put(self.has_tissue_flag)
            return True
        return False


class DetectTissueInStackAndRecord(DetectTissueInStack):
    """Detect Tissue in a Stack of Images and Record Positions.

    This class extends the functionality of detecting tissue in a stack of images
    and also records positions where tissue was detected.
    """

    def __init__(
        self, model, planes=1, percentage=0.75, position_records=[], detect_func=None
    ):
        """Initialize the DetectTissueInStackAndRecord class.

        Parameters:
        -----------
        model : object
            The model object representing the microscope.
        planes : int, optional
            The number of Z planes to capture in the stack. Default is 1.
        percentage : float, optional
            The minimum percentage of tissue required to consider a frame as having
            tissue. Default is 0.75 (75%).
        position_records : list, optional
            A list to record positions where tissue was detected. Default is an empty
            list.
        detect_func : function, optional
            The custom tissue detection function to use. If not specified, the default
            `detect_tissue` function will be used.
        """
        super().__init__(model, planes, percentage, detect_func)

        #: list: A list to record positions where tissue was detected.
        self.position_records = position_records

    def pre_func_data(self):
        """Initialization function for data processing. Extends the base class method.

        This method is called at the beginning of the data processing phase and
        initializes variables for tracking received frames, tissue detection,
        and records the position.
        """

        super().pre_func_data()
        self.position_records.append(True)

    def end_func_data(self):
        """Data processing function to end the data phase. Extends the base class
        method.

        This method is called to determine whether the data phase should end. It checks
        if the specified number of frames have been received and updates the position
        record.

        Returns:
        --------
        bool
            True if the data phase should end, False otherwise.
        """

        self.position_records[-1] = self.has_tissue_flag
        return super().end_func_data()


class RemoveEmptyPositions:
    """Remove Empty Positions from the Model.

    This class is used to remove empty positions from the model based on the specified
    position flags.
    """

    def __init__(self, model, position_flags=[]):
        """Initialize the RemoveEmptyPositions class.

        Parameters:
        -----------
        model : object
            The model object representing the microscope.
        position_flags : list, optional
            A list of position flags to remove. Default is an empty list.
        """

        #: navigate.model.Model: The model object representing the microscope.
        self.model = model

        #: list: A list of position flags to remove.
        self.position_records = position_flags

        #: dict: A dictionary specifying the configuration for signal and data
        # functions.
        self.config_table = {"signal": {"main": self.signal_func}}

    def signal_func(self):
        """Main signal processing function to remove empty positions.

        This method processes the signal to remove empty positions from the model based
        on the specified position flags. It puts a "remove_positions" event into the
        model's event queue to trigger the removal.

        Returns:
        --------
        bool
            True indicating the successful execution of the signal function.
        """

        self.model.event_queue.put(("remove_positions", self.position_records))
        return True
