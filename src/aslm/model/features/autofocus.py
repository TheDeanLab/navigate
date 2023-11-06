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


# Standard Library Imports
from queue import Queue
import threading

# Third Party Imports
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress

# Local imports
from aslm.model.features.feature_container import load_features
from aslm.model.analysis.image_contrast import fast_normalized_dct_shannon_entropy


def power_tent(x, x_offset, y_offset, amplitude, sigma, alpha):
    """Power tent function.

    Used for fitting the response curve of the autofocus routine.

    Parameters
    ----------
    x : float
        x value
    x_offset : float
        x offset
    y_offset : float
        y offset
    amplitude : float
        amplitude
    sigma : float
        sigma
    alpha : float
        alpha

    Returns
    -------
    function : float
        Power tent function
    """
    function = y_offset + amplitude * (1 - np.abs(sigma * (x - x_offset)) ** alpha)
    return function


class Autofocus:
    """Autofocus Data Process

    This function is called by the data thread. It will get the data from the
    autofocus_frame_queue and calculate the entropy of the image. The entropy
    is then compared to the maximum entropy and the position is saved if it is
    higher. The autofocus_pos_queue is then filled with the next position to
    move to. If the autofocus_pos_queue is empty, the autofocus is finished.

    Attributes
    ----------
    autofocus_frame_queue : Queue
        Queue containing the frames to be processed.
    autofocus_pos_queue : Queue
        Queue containing the positions to move to.
    max_entropy : float
        Maximum entropy of the image.
    f_frame_id : int
        Frame ID of the frame with the maximum entropy.
    frame_num : int
        Number of frames to be processed.
    init_pos : float
        Initial position of the stage.
    f_pos : float
        Position of the stage with the maximum entropy.
    focus_pos : float
        Position of the stage with the maximum entropy.
    target_frame_id : int
        Frame ID of the frame to be processed.
    get_frames_num : int
        Number of frames to be processed.
    plot_data : list
        List containing the entropy of the image for each frame.
    total_frame_num : int
        Total number of frames to be processed.
    fine_step_size : float
        Step size of the fine autofocus.
    fine_pos_offset : float
        Offset of the fine autofocus.
    coarse_step_size : float
        Step size of the coarse autofocus.
    coarse_steps : int
        Number of steps of the coarse autofocus.
    signal_id : int
        ID of the frame to be processed.
    target_channel : int
        Channel of the image to be processed.

    Methods
    -------
    run()
        Run the autofocus data process.
    """

    def __init__(self, model, device="stage", device_ref="f"):
        self.model = model
        self.max_entropy = None
        self.f_frame_id = None
        self.frame_num = None

        self.init_pos = None
        self.f_pos = None
        self.focus_pos = None

        self.target_frame_id = None
        self.get_frames_num = None
        self.plot_data = None
        self.total_frame_num = None

        self.fine_step_size = None
        self.fine_pos_offset = None

        self.coarse_step_size = None
        self.coarse_steps = None

        self.signal_id = None

        # Queue
        self.autofocus_frame_queue = Queue()
        self.autofocus_pos_queue = Queue()

        # target channel
        self.target_channel = 1

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
        self.device = device
        self.device_ref = device_ref

    def run(self):
        """Run the Autofocusing Routine



        Returns
        -------
        dict
            Autofocus parameters.
        """
        frame_num = self.get_autofocus_frame_num()
        if frame_num < 1:
            return

        # Opens correct shutter and puts all signals to false
        self.model.prepare_acquisition()
        self.model.active_microscope.prepare_next_channel()

        # load Autofocus
        self.model.signal_container, self.model.data_container = load_features(
            self.model,
            [
                [
                    {
                        "name": Autofocus,
                        "args": (
                            self.device,
                            self.device_ref,
                        ),
                    }
                ]
            ],
        )

        self.model.signal_thread = threading.Thread(
            target=self.model.run_acquisition,
            name="Autofocus Signal",
        )

        self.model.data_thread = threading.Thread(
            target=self.model.run_data_process,
            args=(frame_num + 1,),
            name="Autofocus Data",
        )

        # Start Threads
        self.model.signal_thread.start()
        self.model.data_thread.start()

    def get_autofocus_frame_num(self):
        """Calculate how many frames are needed to get the best focus position.



        Returns
        -------
        int
            Number of frames to be processed.
        """
        settings = self.model.configuration["experiment"]["AutoFocusParameters"][
            self.model.active_microscope_name
        ][self.device][self.device_ref]
        frames = 0
        if settings["coarse_selected"]:
            coarse_range = float(settings["coarse_range"])
            coarse_step_size = float(settings["coarse_step_size"])
            frames = int(coarse_range // coarse_step_size) + 1
        if settings["fine_selected"]:
            fine_range = float(settings["fine_range"])
            fine_step_size = float(settings["fine_step_size"])
            frames += int(fine_range // fine_step_size) + 1
        return frames

    @staticmethod
    def get_steps(ranges, step_size):
        """Calculate number of steps for autofocusing routine.

        Parameters
        ----------
        ranges : float
            Distance to be traveled during the autofocusing routine
        step_size : float
            Step size for autofocusing routine

        Returns
        -------
        steps : float
            Number of steps for the stack
        pos_offset : float
            Need to figure out.
        """
        steps = ranges // step_size + 1
        pos_offset = (steps // 2) * step_size + step_size
        return steps, pos_offset

    def pre_func_signal(self):
        """Prepare the autofocus routine."""
        settings = self.model.configuration["experiment"]["AutoFocusParameters"][
            self.model.active_microscope_name
        ][self.device][self.device_ref]
        if self.device == "stage":
            self.focus_pos = self.model.configuration["experiment"]["StageParameters"][
                self.device_ref
            ]
        else:
            self.focus_pos = 0
        self.total_frame_num = self.get_autofocus_frame_num()  # Total frame num
        self.coarse_steps, self.init_pos = 0, 0

        if settings["fine_selected"]:
            self.fine_step_size = float(settings["fine_step_size"])
            fine_steps, self.fine_pos_offset = self.get_steps(
                float(settings["fine_range"]), self.fine_step_size
            )
            self.init_pos = self.focus_pos - self.fine_pos_offset

        if settings["coarse_selected"]:
            self.coarse_step_size = float(settings["coarse_step_size"])
            self.coarse_steps, coarse_pos_offset = self.get_steps(
                float(settings["coarse_range"]), self.coarse_step_size
            )
            self.init_pos = self.focus_pos - coarse_pos_offset
        self.signal_id = 0

    def in_func_signal(self):
        """Run the autofocus routine."""

        if self.signal_id < self.coarse_steps:
            self.init_pos += self.coarse_step_size
            if self.device == "stage":
                self.model.move_stage(
                    {f"{self.device_ref}_abs": self.init_pos}, wait_until_done=True
                )
                self.model.logger.debug(
                    f"*** Autofocus move stage: ({self.device_ref}, {self.init_pos})"
                )
            elif self.device == "remote_focus":
                self.model.active_microscope.move_remote_focus(self.init_pos)
                self.model.logger.debug(
                    f"*** Autofocus move remote focus: {self.init_pos}"
                )
            self.autofocus_frame_queue.put(
                (self.model.frame_id, self.coarse_steps - self.signal_id, self.init_pos)
            )

        elif self.signal_id < self.total_frame_num:
            if self.signal_id and self.signal_id == self.coarse_steps:
                self.init_pos = self.autofocus_pos_queue.get(
                    timeout=self.coarse_steps * 10
                )
                self.init_pos -= self.fine_pos_offset
            self.init_pos += self.fine_step_size
            if self.device == "stage":
                self.model.move_stage(
                    {f"{self.device_ref}_abs": self.init_pos}, wait_until_done=True
                )
                self.model.logger.debug(
                    f"*** Autofocus move stage: ({self.device_ref}, {self.init_pos})"
                )
            elif self.device == "remote_focus":
                self.model.active_microscope.move_remote_focus(self.init_pos)
                self.model.logger.debug(
                    f"*** Autofocus move remote focus: {self.init_pos}"
                )
            self.autofocus_frame_queue.put(
                (
                    self.model.frame_id,
                    self.total_frame_num - self.signal_id,
                    self.init_pos,
                )
            )

        else:
            self.init_pos = self.autofocus_pos_queue.get(timeout=self.coarse_steps * 10)
            if self.device == "stage":
                self.model.move_stage(
                    {f"{self.device_ref}_abs": self.init_pos}, wait_until_done=True
                )
                self.model.logger.debug(
                    f"*** Autofocus move stage: ({self.device_ref}, {self.init_pos})"
                )
            elif self.device == "remote_focus":
                self.model.active_microscope.move_remote_focus(self.init_pos)
                self.model.logger.debug(
                    f"*** Autofocus move remote focus: {self.init_pos}"
                )

        self.signal_id += 1
        return self.init_pos if self.signal_id > self.total_frame_num else None

    def end_func_signal(self):
        """End the autofocus routine."""

        return self.signal_id > self.total_frame_num

    def pre_func_data(self):
        """Prepare the autofocus routine."""
        # Initialize the autofocus data
        self.max_entropy = 0
        self.f_frame_id = -1

        # Need to calculate DCTS value, but the image frame isn't ready
        self.frame_num = 10  # any value but not 1
        self.f_pos = 0
        self.target_frame_id = 0  # frame id in the buffer with best focus
        self.get_frames_num = 0
        self.plot_data = []
        self.total_frame_num = self.get_autofocus_frame_num()

    def in_func_data(self, frame_ids=[]):
        """Run the autofocus routine.

        Parameters
        ----------
        frame_ids : list
            List of frame ids to be processed


        """

        self.get_frames_num += len(frame_ids)
        while True:
            try:
                if self.f_frame_id < 0:
                    (
                        self.f_frame_id,
                        self.frame_num,
                        self.f_pos,
                    ) = self.autofocus_frame_queue.get_nowait()
                if self.f_frame_id not in frame_ids:
                    break
            except Exception:
                break

            entropy = fast_normalized_dct_shannon_entropy(
                input_array=self.model.data_buffer[self.f_frame_id],
                psf_support_diameter_xy=3,
            )

            self.model.logger.debug(
                f"Appending plot data for frame {self.f_frame_id} focus: {self.f_pos}, "
                f"entropy: {entropy[0]}"
            )
            self.plot_data.append([self.f_pos, entropy[0]])
            # Need to initialize entropy above for the first iteration of the autofocus
            # routine. Need to initialize entropy_vector above for the first iteration
            # of the autofocus routine. Then need to append each measurement to the
            # entropy_vector.  First column will be the focus position, second column
            # would be the DCT entropy value.

            # Find Maximum Focus Position
            if entropy > self.max_entropy:
                self.max_entropy = entropy
                self.focus_pos = self.f_pos
                self.target_frame_id = self.f_frame_id

            self.f_frame_id = -1

            if self.frame_num == 1:
                self.frame_num = 10  # any value but not 1
                self.model.logger.info(
                    f"***********max shannon entropy: {self.max_entropy}, "
                    f"{self.focus_pos}"
                )
                # find out the focus
                self.autofocus_pos_queue.put(self.focus_pos)
                # return [self.target_frame_id]

        if self.get_frames_num > self.total_frame_num:
            return frame_ids

    def end_func_data(self):
        """End the autofocus routine."""
        if self.get_frames_num <= self.total_frame_num:
            return False

        # Send the data for plotting via the event queue
        self.model.event_queue.put(("autofocus", [self.plot_data, False, True]))

        # Evaluate data by fitting it to an inverse power tent.
        if self.model.configuration["experiment"]["AutoFocusParameters"][
            self.model.active_microscope_name
        ][self.device][self.device_ref]["robust_fit"]:
            fit_data, fit_focus_position, r_squared = self.robust_autofocus()

            # If the fit is good, use the fit focus position, else use the max entropy
            if r_squared > 0.9:
                self.focus_pos = fit_focus_position
                self.model.event_queue.put(("autofocus", [fit_data, True, False]))
                self.model.logger.info(
                    f"Robust Focus Estimate: {self.focus_pos}, " f"R^2: {r_squared}"
                )
            else:
                print("Robust Focus Estimate Failed. R^2: %s" % r_squared)
                self.model.logger.info(
                    f"Robust Focus Estimate Failed. R^2: {r_squared}"
                )

        # Update the configuration with the new focus position
        if self.device == "stage":
            self.model.configuration["experiment"]["StageParameters"][
                self.device_ref
            ] = self.focus_pos

            # Tell the controller to update the view
            stage_position = dict(
                map(
                    lambda axis: (
                        f"{axis}_abs",
                        self.model.configuration["experiment"]["StageParameters"][axis],
                    ),
                    ["x", "y", "z", "f", "theta"],
                )
            )
            self.model.event_queue.put(("update_stage", stage_position))
        elif self.device == "remote_focus":
            # update offset of the waveform_constants configuration dict
            zoom = self.model.configuration["experiment"]["MicroscopeState"]["zoom"]
            remote_focus_constants = self.model.configuration["waveform_constants"][
                "remote_focus_constants"
            ][self.model.active_microscope_name][zoom]
            for laser in remote_focus_constants.keys():
                remote_focus_constants[laser]["offset"] = (
                    float(remote_focus_constants[laser]["offset"]) + self.focus_pos
                )

        # Log the new focus position
        # self.model.logger.info("***********final focus: %s" % self.focus_pos)
        # self.model.logger.info(
        #     f"***** final stage position: {self.model.get_stage_position()}"
        # )
        return self.get_frames_num > self.total_frame_num

    def robust_autofocus(self):
        """Robust autofocus routine.

        TODO: Current values for amplitude, sigma, and alpha are hard-coded. Fitting
        is unfortunately unstable.



        Returns
        -------
        self.focus_pos : float
            Focus position
        """

        # Convert plot data to numpy array
        x_data = np.asarray(self.plot_data)[:, 0]
        y_data = np.asarray(self.plot_data)[:, 1]

        # Provide starting conditions for the fit.
        x_offset = np.argmax(y_data)
        y_offset = np.min(y_data)
        amplitude = 1
        sigma = 1
        alpha = 0.01

        # Fit the data
        start_vals = [x_offset, y_offset, amplitude, sigma, alpha]
        tent, _ = curve_fit(power_tent, x_data, y_data, p0=start_vals)
        y_fit = power_tent(x_data, *tent)
        focus_value = np.argmax(y_fit)
        focus_position = x_data[focus_value]

        # Calculate the R-Squared value
        _, _, r_value, _, _ = linregress(y_data, y_fit)
        r_squared = r_value**2

        fit_data = []
        for i in range(len(x_data)):
            fit_data.append([x_data[i], y_fit[i]])

        return fit_data, focus_position, r_squared
