# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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
from queue import Queue
import threading
from copy import deepcopy
import time

# Third Party Imports
import numpy as np
from scipy.optimize import curve_fit

# Local imports
from navigate.model.features.feature_container import load_features
import navigate.model.analysis.image_contrast as img_contrast
from navigate.model.features.image_writer import ImageWriter


def poly2(x, a, b, c):
    """Second order polynomial function

    Parameters
    ----------
    x : float
        x value
    a : float
        a value
    b : float
        b value
    c : float
        c value

    Returns
    -------
    float
        y value
    """
    return a * x**2 + b * x + c


def gauss(x, a, b, c, d):
    """Gaussian function

    Parameters
    ----------
    x : float
        x value
    a : float
        a value
    b : float
        b value
    c : float
        c value
    d : float
        d value

    Returns
    -------
    float
        y value
    """
    y = (x - b) / c
    y = np.exp(-(y**2))
    return a * y + d


def r_squared(y, y_fit):
    """Calculate the R^2 value

    Parameters
    ----------
    y : list
        y values
    y_fit : list
        y_fit values

    Returns
    -------
    float
        R^2 value
    """
    y_bar = np.mean(y)
    SS_res = np.sum((y - y_fit) ** 2)
    SS_tot = np.sum((y - y_bar) ** 2)

    return 1 - SS_res / SS_tot


def fourier_annulus(im, radius_1=0, radius_2=64):
    """Calculate the mean of the fourier transform of an annulus

    Parameters
    ----------
    im : array
        Image array
    radius_1 : int, optional
        Inner radius of the annulus, by default 0
    radius_2 : int, optional
        Outer radius of the annulus, by default 64

    Returns
    -------
    float
        Mean of the fourier transform of the annulus
    array
        Fourier transform of the annulus
    """

    x_, y_ = np.meshgrid(range(im.shape[1]), range(im.shape[0]))

    x_ = x_.astype(float) - x_.mean()
    y_ = y_.astype(float) - y_.mean()

    mask = x_**2 + y_**2 > radius_1**2
    mask *= x_**2 + y_**2 <= radius_2**2

    IM = np.fft.fftshift(np.fft.fft2(im))
    IM_abs = np.abs(IM)

    IM_mask = IM_abs * mask

    return np.mean(IM_mask), IM_mask


class TonyWilson:
    """Tony Wilson iterative AO routine"""

    def __init__(self, model):
        """Initialize the Tony Wilson iterative AO routine

        Parameters
        ----------
        model : Model
            Model object
        """
        #: int: Number of modes
        self.n_modes = None

        #: int: Number of iterations
        self.n_iter = None

        #: int: Number of steps
        self.n_steps = None

        #: float: Coefficient amplitude
        self.coef_amp = None

        #: bool: True if all iterations are done, False otherwise
        self.done_all = False

        #: bool: True if the current iteration is done, False otherwise
        self.done_itr = False

        #: list: detailed report to save as JSON after
        self.report = []

        # TODO: I don't think these are used...
        self.laser = None
        self.laser_power = 0
        self.start_time = 0

        #: navigate.model.Model: Model object
        self.model = model

        #: navigate.model.devices.mirrors.mirror_imop.ImagineOpticsMirror: Mirror object
        self.mirror_controller = self.model.active_microscope.mirror.mirror_controller

        #: int: Number of modes
        self.n_modes = self.mirror_controller.n_modes

        #: bool: whether to save report at the end of run
        self.save_report = self.model.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ].get("save_report", False)

        #: list: List of coefficients to change
        self.change_coef = []
        modes_armed_dict = self.model.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["TonyWilson"]["modes_armed"]

        #: list: List of mode names
        self.mode_names = modes_armed_dict.keys()
        for i, k in enumerate(self.mode_names):
            if modes_armed_dict[k]:
                self.change_coef += [i]
        self.n_coefs = len(self.change_coef)

        self.start_from = self.model.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["TonyWilson"]["from"]

        self.metric = self.model.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["TonyWilson"]["metric"]

        self.fit_func = self.model.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["TonyWilson"]["fitfunc"]

        # if start_from == "flat":
        #     self.best_coefs = np.zeros(self.n_modes, dtype=np.float32)
        # elif start_from == "current":
        #     curr_expt_coefs = list(
        #         self.model.configuration["experiment"]["MirrorParameters"][
        #             "modes"
        #         ].values()
        #     )
        #     self.best_coefs = np.asarray(curr_expt_coefs, dtype=np.float32)

        # self.best_coefs_overall = deepcopy(self.best_coefs)
        # self.best_metric = 0.0
        # self.coef_sweep = None
        # self.best_peaks = []

        # Queue
        self.tw_frame_queue = Queue()
        self.tw_data_queue = Queue()

        # Image Writer
        self.image_writer = ImageWriter(model, sub_dir="AO_Frames")

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

    def run(self, *args):
        """Run the Tony Wilson iterative AO routine

        Parameters
        ----------
        args[0] : dict
            Current microscope state.
        args[1] : dict
            Autofocus parameters

        """
        frame_num = self.get_tw_frame_num()
        if frame_num < 1:
            return

        # Opens correct shutter and puts all signals to false
        self.model.prepare_acquisition()
        self.model.active_microscope.prepare_next_channel()

        # load signal and data containers
        self.model.signal_container, self.model.data_container = load_features(
            self.model, [[{"name": TonyWilson}]]
        )

        self.model.signal_thread = threading.Thread(
            target=self.model.run_acquisition, name="TonyWilson Signal"
        )

        self.model.data_thread = threading.Thread(
            target=self.model.run_data_process,
            # args=(frame_num,),
            kwargs={"data_func": self.image_writer.save_image},
            name="TonyWilson Data",
        )

        print("\n**** STARTING TONY WILSON ****\n")

        # Start Threads
        self.model.signal_thread.start()
        self.model.data_thread.start()

    def get_tw_frame_num(self):
        """Calculate how many frames are needed: iterations x steps x num_coefs"""
        settings = self.model.configuration["experiment"]["AdaptiveOpticsParameters"][
            "TonyWilson"
        ]
        frames = settings["iterations"] * settings["steps"] * self.n_coefs
        return frames

    # don't need this?
    def get_steps(self, ranges, step_size):
        """Calculate the number of steps and the position offset

        Parameters
        ----------
        ranges : int
            Range of the scan
        step_size : int
            Step size

        Returns
        -------
        int
            Number of steps
        int
            Position offset
        """
        steps = ranges // step_size + 1
        pos_offset = (steps // 2) * step_size + step_size
        return steps, pos_offset

    def pre_func_signal(self):
        """Prepare the signal"""
        # initialize the mirror and coef lists, etc

        # Timing
        self.start_time = time.time()

        tw_settings = self.model.configuration["experiment"][
            "AdaptiveOpticsParameters"
        ]["TonyWilson"]

        self.done_all = False

        self.n_iter = tw_settings["iterations"]
        self.n_steps = tw_settings["steps"]
        self.coef_amp = tw_settings["amplitude"]

        self.coef_sweep = np.linspace(
            -self.coef_amp, self.coef_amp, self.n_steps
        ).astype(np.float32)

        self.signal_id = 0
        self.target_signal_id = 0
        self.total_frame_num = self.get_tw_frame_num()

        print(f"Total frame num: {self.total_frame_num}")

        if self.start_from == "flat":
            self.best_coefs = np.zeros(self.n_modes, dtype=np.float32)
        elif self.start_from == "current":
            curr_expt_coefs = list(
                self.model.configuration["experiment"]["MirrorParameters"][
                    "modes"
                ].values()
            )
            self.best_coefs = np.asarray(curr_expt_coefs, dtype=np.float32)

        self.best_coefs_overall = deepcopy(self.best_coefs)
        self.best_metric = 0.0
        self.best_peaks = []

    def in_func_signal(self):
        """Run the signal.

        Returns
        -------
        bool
            True if the signal is done, False otherwise
        """
        out_str = "in_func_signal\n"

        out_str += f"\tSignal:\t{self.signal_id}\n"

        step = self.signal_id % self.n_steps
        coef = int(self.signal_id / self.n_steps) % self.n_coefs
        itr = int(self.signal_id / self.n_steps / self.n_coefs) % self.n_iter

        out_str += f"\tStep:\t{step}\n"
        out_str += f"\tC_n:\t{coef}\n"
        out_str += f"\tItr:\t{itr}\n"

        coef_arr = np.zeros(self.n_modes, dtype=np.float32)
        c = self.change_coef[coef]
        coef_arr[c] = self.coef_sweep[step]

        applied_coefs = coef_arr + self.best_coefs

        out_str += f"\tApply:\t[{' '.join([f'{c:.2f}' for c in applied_coefs])}]\n"

        # Update the mirror...
        self.mirror_controller.flat()
        try:
            self.mirror_controller.display_modes(applied_coefs)
        except Exception as e:
            print(e)
            return

        time.sleep(self.model.active_microscope.current_exposure_time / 1000)

        try:
            curr_mirror_coefs = self.mirror_controller.get_modal_coefs()[0]
            out_str += (
                f"\tCoefs:\t[{' '.join([f'{c:.2f}' for c in curr_mirror_coefs])}]\n"
            )
        except Exception as e:
            print(e)
            return

        self.model.logger.debug(
            f"*** TonyWilson > in_func_signal :: iter:{itr}\tcoef:{coef}\tstep:{step}"
        )
        coef_str = " ".join([f"{c:.2f}" for c in (coef_arr + self.best_coefs)])
        self.model.logger.debug(
            f"*** TonyWilson > in_func_signal :: display_modes:[{coef_str}]"
        )

        if (applied_coefs == curr_mirror_coefs).all() or (applied_coefs == 0).all():
            self.signal_id += 1

            out_str += "\tSending tw_frame_queue...\n"
            self.tw_frame_queue.put(
                (
                    self.model.frame_id,
                    self.total_frame_num - self.signal_id,
                    itr,
                    coef,
                    step,
                )
            )
        else:
            out_str += "\tMirror update failed...\n"

        print(out_str)

        return self.signal_id >= self.total_frame_num

    def end_func_signal(self):
        """End the signal

        Returns
        -------
        bool
            True if the signal is done, False otherwise
        """
        print("end_func_signal() called!!!")

        if self.model.stop_acquisition:
            return True

        return self.signal_id >= self.total_frame_num or self.done_all

    def pre_func_data(self):
        """Prepare the data"""
        self.f_frame_id = (
            -1
        )  # to indicate if there is one frame need to calculate shannon value,
        # but the image frame isn't ready
        self.frame_num = 10  # any value but not 1
        self.target_frame_id = 0  # frame id in the buffer with best focus
        self.get_frames_num = 0
        self.plot_data = []
        self.trace_list = {}
        self.total_frame_num = self.get_tw_frame_num()
        self.x = self.coef_sweep
        self.y = []
        self.x_fit = np.linspace(-self.coef_amp, self.coef_amp, 1024)
        self.y_fit = []
        self.mirror_img = None

        self.frames_done = 0

    def process_data(self, coef, mode="poly"):
        """Process the data

        Parameters
        ----------
        coef : int
            Coefficient index
        mode : str, optional
            Fitting mode, by default "poly"
        """
        self.y = self.plot_data

        if mode == "poly":
            c = np.min(self.y)  # offset guess
            b = (np.max(self.y) - c) / self.coef_amp  # slope guess
            a = -b / 2

            p, _ = curve_fit(
                poly2,
                self.x,
                self.y,
                p0=[a, b, c],
                bounds=([-np.inf, -np.inf, -np.inf], [0.0, np.inf, np.inf]),
            )
            self.y_fit = poly2(self.x_fit, p[0], p[1], p[2])
            r_2 = r_squared(self.y, poly2(self.x, p[0], p[1], p[2]))

        elif mode == "gauss":
            d = np.min(self.y)
            a = np.max(self.y) - d
            b = self.x[np.argmax(self.y)]
            c = (self.x[-1] - self.x[0]) / 2

            p, _ = curve_fit(
                gauss,
                self.x,
                self.y,
                p0=[a, b, c, d],
                bounds=([0, -np.inf, 0, 0], [np.inf, np.inf, np.inf, np.inf]),
            )
            self.y_fit = gauss(self.x_fit, p[0], p[1], p[2], p[3])
            r_2 = r_squared(self.y, gauss(self.x, p[0], p[1], p[2], p[3]))

        self.best_coefs[self.change_coef[coef - 1]] += (
            self.x_fit[self.y_fit.argmax()] * r_2
        )  # weight by R^2 goodness of fit
        self.mirror_img = self.mirror_controller.get_wavefront_pix()

        new_metric = self.plot_data[int(self.n_steps / 2)]
        self.best_peaks.append(new_metric)
        if new_metric > self.best_metric:
            self.best_metric = new_metric
            self.best_coefs_overall = deepcopy(self.best_coefs)

        self.plot_data = []

    def in_func_data(self, frame_ids=[]):
        """Run the data

        Parameters
        ----------
        frame_ids : list, optional
            List of frame ids, by default []

        Returns
        -------
        list
            List of frame ids
        """
        self.get_frames_num += len(frame_ids)

        out_str = "in_func_data\n"

        out_str += f"\tFrames:\t{frame_ids}\n"

        out_str += f"\tGet Frames Num:\t{self.get_frames_num}\n"

        while True:
            try:
                if self.f_frame_id < 0:
                    (
                        self.f_frame_id,
                        self.frame_num,
                        itr,
                        coef,
                        step,
                    ) = self.tw_frame_queue.get_nowait()
                if self.f_frame_id not in frame_ids:
                    out_str += (
                        f"\tFrame ID {self.f_frame_id} was not in the frame queue...\n"
                    )
                    break
            except Exception:
                out_str += "\tStill waiting tw_frame_queue...\n"
                break

            # get the image metric
            img = self.model.data_buffer[self.f_frame_id]

            """ IMAGE METRICS """
            if self.metric == "Pixel Max":
                new_data = img.max()
            elif self.metric == "Pixel Average":
                new_data = img.mean()
            elif self.metric == "DCT Shannon Entropy":
                new_data = img_contrast.fast_normalized_dct_shannon_entropy(img, 3)[0]

            if len(self.plot_data) == self.n_steps:
                self.process_data(coef, mode=self.fit_func)
                self.trace_list[self.mode_names[self.change_coef[coef]]] = {
                    "x": self.x,
                    "y": self.y,
                    "x_fit": self.x_fit[::32],
                    "y_fit": self.y_fit[::32],
                }
                out_str += "\tFITTING DATA...\n"

            self.plot_data.append(new_data)
            out_str += f"\tTrace:\t{np.flip(self.plot_data)}\n"

            self.frames_done += 1
            out_str += f"\tDone:\t{self.frames_done}\n"

            self.f_frame_id = -1

            self.model.logger.debug(
                f"*** TonyWilson > in_func_data :: plot_data: {np.flip(self.plot_data)}"
            )

            out_str += f"\tFrame Num:\t{self.frame_num}\n"
            if self.frame_num == 1:
                self.frame_num = 10  # any value but not 1
                return [self.target_frame_id]

            if coef == self.n_coefs - 1:
                if step == self.n_steps - 1:

                    self.coef_sweep *= 0.95
                    self.done_itr = True
                    out_str += f"\tDone iteration {itr}!\n"

                    if itr == self.n_iter - 1:
                        self.done_all = True
                        out_str += "\tDone all!!!\n"

        out_str += "\tSending tw_data_queue...\n"
        self.tw_data_queue.put((self.frames_done,))

        print(out_str)

        if self.frames_done >= self.total_frame_num:
            print(">>> in_func_data ended!!!")
            return frame_ids

    def build_report(self):

        return deepcopy(
            {
                "mirror_update": {
                    "mirror_img": self.mirror_img,
                    "coefs": self.best_coefs,
                },
                "tonywilson": {
                    "peaks": self.best_peaks,
                    "trace": self.trace_list,
                    "done": self.done_all,
                    "metric": self.metric,
                    "iter": self.n_iter,
                    "steps": self.n_steps,
                    "amp": self.coef_amp,
                    "modes": self.change_coef,
                },
            }
        )

    def end_func_data(self):
        """End the data

        Returns
        -------
        bool
            True if the data is done, False otherwise
        """
        print("end_func_data() called!!!")

        if self.done_all:
            self.best_coefs = self.best_coefs_overall
            # self.model.stop_acquisition = True
            # self.model.end_acquisition()
            # print("Ending acquisition...")
            try:
                stop_time = time.time()
                print(f"Total runtime:\t{(stop_time - self.start_time):.3f} sec")
            except Exception as e:
                print(e)

        try:
            if self.done_itr:
                current_report = self.build_report()
                self.report.append(current_report)

                self.model.event_queue.put(
                    ("mirror_update", current_report["mirror_update"])
                )
                self.model.event_queue.put(("tonywilson", current_report["tonywilson"]))
        except Exception as e:
            print(e)

        self.done_itr = False

        self.mirror_controller.display_modes(self.best_coefs_overall)

        if self.done_all and self.save_report:
            self.model.event_queue.put(("ao_save_report", self.report))

        return self.frames_done >= self.total_frame_num or self.done_all
