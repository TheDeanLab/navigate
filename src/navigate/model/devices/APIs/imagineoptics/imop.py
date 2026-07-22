import os
import json
import time

import numpy as np
import pandas as pd

try:
    import wavekit_py as wk
except ImportError as err:
    raise ImportError(
        "wavekit_py is not installed in this Python environment. "
        "With this environment active, run the WaveKit installer: "
        'python "C:\\Program Files\\Imagine Optic\\WaveSuite_4.5.1\\WaveKit'
        '\\Python\\install_wavekit_python.py"'
    ) from err


from .enums import (
    E_MODAL_T,
    E_PUPIL_DETECTION_T,
    E_ZERNIKE_NORM_T,
    E_PUPIL_COVERING_T,
    E_ZERNIKE_INDEXING_T,
)

# Base directory used only to resolve short `name=` references in load_wcs()/
# save_wcs() into `<basepath>/MirrorFiles/<name>.wcs`. All hardware-specific
# config/calibration file paths are supplied explicitly by the caller (see
# navigate.model.devices.mirror.imop.ImagineOpticsMirror.get_connect_params).
basepath = "C:/Users/Spectral/Desktop/muDM"


mode_names = [
    "Vert. Tilt",
    "Horz. Tilt",
    "Defocus",
    "Vert. Asm.",
    "Oblq. Asm.",
    "Vert. Coma",
    "Horz. Coma",
    "3rd Spherical",
    "Vert. Tre.",
    "Horz. Tre.",
    "Vert. 5th Asm.",
    "Oblq. 5th Asm.",
    "Vert. 5th Coma",
    "Horz. 5th Coma",
    "5th Spherical",
    "Vert. Tetra.",
    "Oblq. Tetra.",
    "Vert. 7th Tre.",
    "Horz. 7th Tre.",
    "Vert. 7th Asm.",
    "Oblq. 7th Asm.",
    "Vert. 7th Coma",
    "Horz. 7th Coma",
    "7th Spherical",
    "Vert. Penta.",
    "Horz. Penta.",
    "Vert. 9th Tetra.",
    "Oblq. 9th Tetra.",
    "Vert. 9th Tre.",
    "Horz. 9th Tre.",
    "Vert. 9th Asm.",
    "Oblq. 9th Asm.",
]


class IMOP_Mirror:
    """
    High-level controller for the muDM deformable mirror.
    """

    def __init__(
        self,
        wfc_config_file_path,
        haso_config_file_path,
        positions_file_path,
        interaction_matrix_file_path,
        n_modes=32,
    ):
        """
        Connect to the mirror and HASO, build the command matrix, and fit
        the Zernike pupil, all from the given config/calibration files.

        Args:
            wfc_config_file_path: Path to the wavefront-corrector (.dat) config file.
            haso_config_file_path: Path to the HASO sensor (.dat) config file.
            positions_file_path: Path to the .wcs file defining the flat actuator
                positions.
            interaction_matrix_file_path: Path to the .aoc interaction matrix used
                to build the command matrix.
            n_modes: Number of Zernike modes to keep in the command matrix and
                modal decomposition.
        """

        self.wfc_config_file_path = wfc_config_file_path
        self.haso_config_file_path = haso_config_file_path
        self.positions_file_path = positions_file_path
        self.interaction_matrix_file_path = interaction_matrix_file_path
        self.n_modes = n_modes

        try:
            n_actuators = wk.WavefrontCorrectorSet(
                config_file_path=wfc_config_file_path
            ).get_actuators_count()
        except Exception as err:
            raise RuntimeError(
                f"Could not read wavefront-corrector config '{wfc_config_file_path}'. "
                "Check the path exists and is a valid WaveKit .dat config file."
            ) from err

        mirror = WavefrontCorrector(
            wfc_config_file_path=wfc_config_file_path,
            haso_config_file_path=haso_config_file_path,
            positions_file_path=positions_file_path,
            interaction_matrix_file_path=interaction_matrix_file_path,
            n_actuators=n_actuators,
            connect=True,
        )

        corrdata_manager = CorrDataManager()
        corrdata_manager.new_from_backup_file(
            haso_config_file_path=haso_config_file_path,
            interaction_matrix_file_path=interaction_matrix_file_path,
        )

        corrdata_manager.set_command_matrix_prefs(nb_kept_modes=n_modes)
        corrdata_manager.compute_command_matrix()

        mirror.set_temporization(20)

        config = CoreEngine().get_config(haso_config_file_path=haso_config_file_path)

        pupil = Pupil()
        pupil.new_from_dimensions(
            dimensions=config.nb_subpupils, steps=config.ulens_step, value=0
        )

        pupil_buffer = corrdata_manager.get_greatest_common_pupil()

        pupil.set_data(pupil_buffer)

        zernike_pupil = wk.ComputePupil.fit_zernike_pupil(
            pupil.pointer,
            E_PUPIL_DETECTION_T.E_PUPIL_AUTOMATIC,
            E_PUPIL_COVERING_T.E_PUPIL_CIRCUMSCRIBED,
            False,
        )
        self.pupil_center = zernike_pupil.center
        self.pupil_radius = zernike_pupil.radius

        self.position_flat = np.asarray(
            mirror.get_positions_from_file(positions_file_path), dtype=np.float32
        )

        modal_coef = ModalCoef(modal_type=E_MODAL_T.E_MODALCOEF_ZERNIKE)
        modal_coef.set_zernike_prefs(
            n_modes,
            self.pupil_center,
            self.pupil_radius,
        )

        self.mirror = mirror
        self.corrdata_manager = corrdata_manager
        self.pupil = pupil
        self.modal_coef = modal_coef
        self.haso_slopes = HasoSlopes()
        self.config = config

        self.last_delta_commands = np.zeros(self.mirror.n_actuators, dtype=np.float32)

    def flat(self):
        """Command the mirror back to its flat shape (all Zernike coefficients zero)."""
        self.display_modes(np.zeros(self.n_modes, dtype=np.float32))

    def zero_flatness(self):
        """Redefine flat as all-zero actuator positions, then move there."""
        self.set_flat(np.zeros(self.mirror.n_actuators, dtype=np.float32))
        self.flat()

    def set_flat(self, pos=None, pos_path=None):
        """
        Redefine the reference "flat" actuator positions used by display_modes(),
        without moving the mirror.

        Args:
            pos: Actuator-length array of positions to use as the new flat reference.
            pos_path: Alternatively, a .wcs file path to load the positions from.
        """
        if pos_path:
            pos = self.mirror.get_positions_from_file(pos_path)

        self.position_flat = np.asarray(pos, dtype=np.float32)

    def move_absolute_zero(self):
        """Move all actuators directly to position zero."""
        self.mirror.move_absolute(np.zeros(self.mirror.n_actuators, dtype=np.float32))

    def display_modes(self, coefs, wait=False):
        """
        Command the mirror to reproduce the given Zernike modal coefficients.

        Converts the requested Zernike coefficients into HASO slopes, then
        into per-actuator delta commands via the command matrix, and moves
        the mirror to 'position_flat + delta_commands'.

        Args:
            coefs: Zernike coefficient vector, length 'n_modes'.
            wait: If True, block (up to 1s) until the measured modal
                coefficients match the request.
        """
        if type(coefs) is not np.ndarray:
            coefs = np.array(coefs)

        if coefs.dtype is not np.float32:
            coefs = coefs.astype(np.float32)

        try:
            self.modal_coef.set_data(coefs, self.pupil)

        except Exception as modal_coef_exception:
            print(f"modal_coef.set_data failed: {modal_coef_exception}")
            return

        try:
            self.haso_slopes.new_from_modal_coef(
                self.modal_coef, self.haso_config_file_path
            )

        except Exception as haso_exception:
            print(f"haso_slopes.new_from_modal_coef failed: {haso_exception}")
            return

        try:
            delta_commands = (
                self.corrdata_manager.compute_delta_command_from_delta_slopes(
                    self.haso_slopes
                )
            )

        except Exception as delta_commands_exception:
            print(
                "corrdata_manager.compute_delta_command_from_delta_slopes "
                f"failed: {delta_commands_exception}"
            )
            return

        self.last_delta_commands = delta_commands

        new_positions = self.position_flat + delta_commands

        try:
            self.mirror.move_absolute(new_positions)

        except Exception as move_exception:
            print(f"mirror.move_absolute failed: {move_exception}")
            return

        if wait:
            timeout = 1000
            t = 0
            while (self.get_modal_coefs()[0] != coefs).any():
                t += 1
                if t == timeout:
                    print("Ran out of time....")
                    break
                time.sleep(0.001)

    def update_delta_commands(self):
        """Recompute 'last_delta_commands' from the mirror's actual current
        positions minus flat."""
        self.last_delta_commands = np.asarray(
            self.mirror.get_current_positions(), dtype=np.float32
        ) - np.asarray(self.position_flat, dtype=np.float32)

    def get_modal_coefs(self):
        """Return the (coefficients, mode indices) last set via display_modes()."""
        return self.modal_coef.get_data()

    def load_wcs(self, path=None, name=None, mode_file=False):
        """
        Load actuator positions from a .wcs file and move the mirror there.

        Args:
            path: Full path to the .wcs file to load.
            name: Alternatively, a name to resolve to `<mirror_file_path>/<name>.wcs`.
            mode_file: If True, also load the sibling `<name>.json` mode-coefficient
                file and return it as a list of floats (empty list if not found).

        Returns:
            List of mode coefficients if 'mode_file' is True and the json file
            exists, an empty list if it doesn't, or None otherwise.
        """
        if path:
            wcs_load_path = path
        elif name:
            wcs_load_path = os.path.join(basepath, "MirrorFiles", name + ".wcs")

        else:
            print("IMOP_Mirror:: Need to provide either name or path")
            return

        new_positions = self.mirror.get_positions_from_file(wcs_load_path)
        self.mirror.move_absolute(new_positions)
        self.update_delta_commands()

        if mode_file:
            mode_load_path = wcs_load_path.split(".")[0] + ".json"

            try:
                with open(mode_load_path, "r") as f:
                    coefs = json.load(f)
            except FileNotFoundError as err:
                print(f"{err.strerror}::{mode_load_path} > modal coef not updated...")
                return []

            coefs = [float(c) for c in coefs.values()]

            return coefs

    def save_wcs(self, path=None, name=None, mode_file=False):
        """
        Save the mirror's current actuator positions to a .wcs file.
        """
        if path:
            wcs_save_path = path
        elif name:
            wcs_save_path = os.path.join(basepath, "MirrorFiles", name + ".wcs")

        else:
            print("IMOP_Mirror:: Need to provide either name or path")
            return

        self.mirror.save_positions_to_file(file_path=wcs_save_path)

        if mode_file:
            mode_save_path = wcs_save_path.split(".")[0] + ".json"
            coefs, coef_inds = self.get_modal_coefs()

            mode_dict = {}
            for c in coef_inds:
                mode_dict[mode_names[c - 1]] = f"{coefs[c-1]:.4f}"

            with open(mode_save_path, "w") as f:
                json.dump(mode_dict, f)

    def get_wavefront_pix(self):
        """
        Lay out 'last_delta_commands' on a square pixel grid for visualization.

        Actuators are placed at the 'n_actuators' grid points nearest the
        center (by Euclidean distance), matching the physical layout
        assumption used elsewhere in this module; all other pixels are NaN.

        Returns:
            2D float32 array (side x side, side = ceil(sqrt(n_actuators)) + 2)
            with actuator delta-command values at their grid positions and
            NaN everywhere else.
        """

        n = self.mirror.n_actuators

        side = int(np.ceil(np.sqrt(n))) + 2

        x, y = np.meshgrid(np.arange(side), np.arange(side))

        x = x - x.mean()
        y = y - y.mean()

        r2 = x**2 + y**2

        nearest = np.argsort(r2.ravel(), kind="stable")[:n]
        pupil = np.zeros(r2.shape, dtype=bool)
        pupil.flat[nearest] = True

        wavefront = np.full(pupil.shape, np.nan, dtype=np.float32)

        wavefront[pupil] = self.last_delta_commands

        return wavefront


class CoreEngine:
    """Reads static HASO sensor configuration/calibration metadata from a
    config file."""

    def get_config(self, haso_config_file_path):
        """
        Get HASO config information from HASO config file path.
        """
        config_t, specs_t, wavelength_t = wk.HasoConfig.get_config(
            haso_config_file_path
        )

        def _opt_list(value):
            if isinstance(value, str):
                return [item for item in value.split(";") if item]
            else:
                return value

        config = {
            "serial_number": getattr(config_t, "serial_number", None),
            "revision": getattr(config_t, "revision", None),
            "model": getattr(config_t, "model", None),
            "nb_subpupils": specs_t.nb_subapertures,
            "ulens_step": specs_t.ulens_step,
            "alignment_position_pixels": getattr(specs_t, "align_pos", None),
            "tolerence_radius": getattr(specs_t, "radius_tolerance", None),
            "default_start_subpupil": getattr(specs_t, "start_subpup", None),
            "lower_calibration_wavelen": getattr(wavelength_t, "lower_calib_wl", None),
            "upper_calibration_wavelen": getattr(wavelength_t, "upper_calib_wl", None),
            "black_pupil_position": getattr(specs_t, "black_subpup", None),
            "tilt_limit_mrad": getattr(specs_t, "tilt_limit", None),
            "radius": getattr(specs_t, "radius", None),
            "microlens_focal": getattr(specs_t, "micro_lens_focal", None),
            "internal_options_list": _opt_list(
                getattr(specs_t, "internal_options", None)
            ),
            "software_info_list": _opt_list(getattr(specs_t, "software_info", None)),
            "SdkInfoList": _opt_list(getattr(specs_t, "sdk_info", None)),
        }

        return pd.Series(config)


class HasoSlopes:
    """Wraps a wavekit_py HasoSlopes object -- the wavefront slopes
    synthesized from a set of Zernike modal coefficients."""

    def __init__(self):
        self._haso_slopes = None

    @property
    def pointer(self):
        return self._haso_slopes

    def new_from_modal_coef(self, modal_coef, haso_config_file_path):
        """
        Synthesize HASO slopes corresponding to the given Zernike modal coefficients.

        Args:
            modal_coef: A ModalCoef wrapper whose coefficients define the
                target wavefront.
            haso_config_file_path: Path to the HASO sensor config file used
                for the synthesis.
        """
        self._haso_slopes = wk.HasoSlopes(
            modalcoef=modal_coef.pointer, config_file_path=haso_config_file_path
        )


class Pupil:
    """Wraps a wavekit_py Pupil object -- a binary mask over the subaperture
    grid marking which subapertures are active."""

    def __init__(self):
        self._pupil = None

    @property
    def pointer(self):
        return self._pupil

    def new_from_dimensions(self, dimensions, steps, value):
        """
        Create a uniform pupil mask of the given size, filled with a constant value.

        Args:
            dimensions: Subaperture grid size (object with .X/.Y), e.g.
                from CoreEngine's config.
            steps: Subaperture step size (object with .X/.Y).
            value: Boolean fill value for every mask element.
        """
        dim = wk.dimensions(size=dimensions, steps=steps)
        self._pupil = wk.Pupil(dimensions=dim, value=bool(value))

    def new_from_zernike_pupil(self, dimensions, steps, radius, center):
        """
        Create a circular pupil mask from an explicit center and radius.

        Args:
            dimensions: Subaperture grid size (object with .X/.Y).
            steps: Subaperture step size (object with .X/.Y).
            radius: Radius of the circular pupil, in subaperture units.
            center: Center of the circular pupil.
        """
        dim = wk.dimensions(size=dimensions, steps=steps)
        self._pupil = wk.Pupil(dimensions=dim, center=center, radius=radius)

    def get_data(self):
        """Return the pupil mask as a 2D boolean array."""
        return self._pupil.get_data()

    def set_data(self, data):
        """Overwrite the pupil mask from a 2D array-like, coerced to boolean."""
        self._pupil.set_data(np.asarray(data).astype(bool))


class ModalCoef:
    """Wraps a wavekit_py ModalCoef object -- a set of modal (Zernike or
    Legendre) coefficients describing a wavefront."""

    def __init__(self, modal_type=E_MODAL_T.E_MODALCOEF_ZERNIKE):
        self._modal_coef = wk.ModalCoef(modal_type=modal_type)

    @property
    def pointer(self):
        return self._modal_coef

    def set_zernike_prefs(
        self,
        nb_coefs_total,
        projection_pupil_center,
        projection_pupil_radius,
        normalization=E_ZERNIKE_NORM_T.E_ZERNIKE_NORM_STD,
        zernike_indexing=E_ZERNIKE_INDEXING_T.WYANT,
    ):
        """
        Configure how Zernike coefficients are interpreted: how many terms,
        which normalization/indexing convention, and over which pupil
        (center + radius) they're projected.

        Args:
            nb_coefs_total: Number of Zernike coefficients to track.
            projection_pupil_center: Center of the projection pupil (e.g.
                from wk.ComputePupil.fit_zernike_pupil).
            projection_pupil_radius: Radius of the projection pupil.
            normalization: Zernike normalization convention (standard or RMS).
            zernike_indexing: Zernike term ordering convention (Wyant or Noll).
        """

        projection_pupil = wk.ZernikePupil_t(
            center=projection_pupil_center,
            radius=projection_pupil_radius,
        )

        self._modal_coef.set_zernike_prefs(
            zernike_normalization=normalization,
            nb_zernike_coefs_total=nb_coefs_total,
            zernike_indexing=zernike_indexing,
            projection_pupil=projection_pupil,
        )

    def set_data(self, coef, pupil=None):
        """
        Set polynomial coefficients information and values.
        """
        pupil_obj = pupil.pointer if pupil is not None else None
        self._modal_coef.set_data(np.asarray(coef).astype(np.float32), pupil_obj)

    def get_data(self):
        """
        Get polynomial coefficients information and values.
        """
        coef, index, _mask = self._modal_coef.get_data()
        return coef, index


class CorrDataManager:
    """
    Wraps a wavekit_py CorrDataManager object -- builds the command matrix
    from an interaction matrix and HASO calibration, and uses it to convert
    wavefront slope variations into actuator command deltas.
    """

    def __init__(self):
        self._corr_data = None

    @property
    def pointer(self):
        return self._corr_data

    def new_from_backup_file(self, haso_config_file_path, interaction_matrix_file_path):
        """
        Load HASO calibration and interaction-matrix data to initialize
        the correction-data pipeline.

        Args:
            haso_config_file_path: Path to the HASO sensor config file.
            interaction_matrix_file_path: Path to the .aoc interaction matrix file.
        """
        self._corr_data = wk.CorrDataManager(
            haso_config_file_path=haso_config_file_path,
            interaction_matrix_file_path=interaction_matrix_file_path,
        )

    def set_command_matrix_prefs(self, nb_kept_modes, tilt_filtering=False):
        """
        Configure the command matrix to be computed.

        Args:
            nb_kept_modes: Number of Zernike modes to keep when inverting
                the interaction matrix.
            tilt_filtering: Whether to filter out tip/tilt from the command matrix.
        """
        self._corr_data.set_command_matrix_prefs(nb_kept_modes, tilt_filtering)

    def compute_command_matrix(self):
        """Compute the command matrix using the previously set preferences."""
        self._corr_data.compute_command_matrix()

    def get_greatest_common_pupil(self):
        """
        Compute the greatest common pupil.
        """
        return self._corr_data.get_greatest_common_pupil()

    def compute_delta_command_from_delta_slopes(self, delta_slopes):
        """
        Compute the relative wavefront corrector commands corresponding
        to a delta slopes variation

        Returns:
            Array of size actuators count, containing the relative commands deltas.
        """
        return self._corr_data.compute_delta_command_from_delta_slopes(
            delta_slopes.pointer
        )


class WavefrontCorrector:
    """
    Wraps a wavekit_py WavefrontCorrector -- the live connection to the
    deformable mirror hardware.
    """

    def __init__(
        self,
        wfc_config_file_path,
        haso_config_file_path,
        positions_file_path,
        interaction_matrix_file_path,
        n_actuators=91,
        connect=True,
    ):
        """
        Args:
            wfc_config_file_path: Path to the wavefront-corrector (.dat) config file.
            haso_config_file_path: Path to the HASO sensor (.dat) config file.
            positions_file_path: Default .wcs positions file associated
                with this corrector.
            interaction_matrix_file_path: Default .aoc interaction matrix
                associated with this corrector.
            n_actuators: Number of actuators on the corrector.
            connect: If True, open the hardware connection immediately.
        """

        self.wfc_config_file_path = wfc_config_file_path
        self.haso_config_file_path = haso_config_file_path
        self.positions_file_path = positions_file_path
        self.interaction_matrix_file_path = interaction_matrix_file_path
        self.n_actuators = n_actuators

        try:
            self._wfc = wk.WavefrontCorrector(config_file_path=wfc_config_file_path)
        except Exception as err:
            raise RuntimeError(
                f"Could not load wavefront-corrector config '{wfc_config_file_path}'. "
                "Check the path exists and is a valid WaveKit .dat config file."
            ) from err

        self._is_connected = False

        if connect:
            self.connect()

        self.get_preferences()

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def connect(self):
        """Open the hardware connection, if not already connected."""
        if not self._is_connected:
            try:
                self._wfc.connect(True)
            except Exception as err:
                raise ConnectionError(
                    f"Could not connect to the wavefront corrector (config: "
                    f"'{self.wfc_config_file_path}'). Check that the mirror is "
                    "powered on, connected via USB, its drivers are installed, "
                    "and no other program is already connected to it."
                ) from err
            self._is_connected = True

    def disconnect(self):
        """Close the hardware connection, if currently connected. Safe to
        call multiple times."""
        if getattr(self, "_is_connected", False):
            self._wfc.disconnect()
            self._is_connected = False

    def get_preferences(self):
        """
        Fetch and cache the corrector's current command preferences from hardware.

        Returns:
            Dict with keys "sleep_after_movement", "cmd_min", "cmd_max",
            "validity", and "fixed_values" (also stored on `self.preferences`).
        """
        sleep_after_movement, prefs = self._wfc.get_preferences()

        self.preferences = {
            "sleep_after_movement": sleep_after_movement,
            "cmd_min": prefs.min_array,
            "cmd_max": prefs.max_array,
            "validity": prefs.validity_array,
            "fixed_values": prefs.fixed_value_array,
        }

        return self.preferences

    def set_preferences(self, **kwargs):
        """
        Update one or more cached preferences and push them to hardware.

        Args:
            **kwargs: Any subset of the keys returned by `get_preferences()`
                (e.g. cmd_min=..., cmd_max=...). Unknown keys raise ValueError.

        Raises:
            ValueError: If a kwarg key is not one of the valid preference keys.
        """
        for key in kwargs.keys():
            if key in self.preferences.keys():
                self.preferences[key] = kwargs[key]

            else:
                raise ValueError(
                    f"{key} is not a valid preference. Choose from: "
                    f"{str([key for key in self.preferences.keys()])}"
                )

        prefs = wk.CorrectorPrefs_t(
            min_array=self.preferences["cmd_min"],
            max_array=self.preferences["cmd_max"],
            validity_array=self.preferences["validity"],
            fixed_value_array=self.preferences["fixed_values"],
        )

        self._wfc.set_preferences(self.preferences["sleep_after_movement"], prefs)

    def get_temporization(self):
        """Get current WavefrontCorrector preference"""

        return self._wfc.get_temporization()

    def set_temporization(self, sleep_after_movement):
        """Set current Wavefront preference."""

        self.preferences["sleep_after_movement"] = sleep_after_movement
        self._wfc.set_temporization(sleep_after_movement)

    def get_current_positions(self):
        """
        Get current actuators positions

        Returns:
            Array containing the actuators positions
        """
        return np.asarray(self._wfc.get_current_positions(), dtype=np.float32)

    def get_positions_from_file(self, positions_file_path):
        """
        Get Wavefront corrector positions from positions file
        """
        return np.asarray(
            self._wfc.get_positions_from_file(positions_file_path), dtype=np.float32
        )

    def save_positions_to_file(self, file_path):
        """
        Save current wavefroont corrector positions to file
        """
        self._wfc.save_current_positions_to_file(file_path)

    def move_relative(self, positions):
        """
        Move to requested relative positions, clipping according to current preferences.
        """
        self._wfc.move_to_relative_positions(np.asarray(positions).astype(np.float32))

    def move_absolute(self, positions):
        """
        Move to requested absolute positions, clipping according to current preferences.
        """
        self._wfc.move_to_absolute_positions(np.asarray(positions).astype(np.float32))

    def check_absolute_positions(self, positions):
        """
        Check if requested absolute positions are valid according to
        current preferences.
        """
        return self._wfc.check_absolute_positions(
            np.asarray(positions).astype(np.float32)
        )

    def clear(self):
        """
        Clear the Wavefront corrector positions to zero.
        """
        self.move_absolute(np.zeros(self.n_actuators, dtype=np.float32))
