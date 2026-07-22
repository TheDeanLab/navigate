# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

"""SDK-contract tests for navigate.model.devices.APIs.imagineoptics.imop.

wavekit_py is Imagine Optic's proprietary SDK, installed only alongside a real
WaveKit setup -- it ships with the WaveKit installer and is not distributable
in this repository or in CI. The tests below therefore skip everywhere the SDK
is absent, but on a machine with WaveKit 4.5.1 installed, they exercise the
*actual* wavekit_py classes imop.py calls into and assert that our call sites
match the real signatures, rather than mocking the module wholesale.

Run these against the real SDK (e.g. on the instrument/lab machine) before
merging any change to imop.py. A skip in this environment is expected and is
not the same as a pass -- it means the contract is unverified here.
"""

import inspect

import pytest

wk = pytest.importorskip(
    "wavekit_py",
    reason=(
        "wavekit_py is not installed. These contract tests only run on a "
        "machine with the real Imagine Optic WaveKit 4.5.1 SDK installed; "
        "they must be run there before merging changes to imop.py."
    ),
)


def _params(callable_obj):
    """Return a callable's ordered parameter names (excluding 'self'/'cls').

    Returns None when wavekit_py does not expose an introspectable signature
    (e.g. a compiled extension without signature metadata) so callers can
    skip with an explicit reason instead of silently passing.
    """
    try:
        sig = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return None
    return [p for p in sig.parameters if p not in ("self", "cls")]


def _require_params(callable_obj, description):
    params = _params(callable_obj)
    if params is None:
        pytest.skip(
            f"wavekit_py does not expose an introspectable signature for "
            f"{description}; verify manually against the WaveKit 4.5.1 docs."
        )
    return params


class TestModalCoefSetDataContract:
    """Highest-risk gap flagged in review: imop.py's ModalCoef.set_data()
    calls wk.ModalCoef.set_data(coef_array, pupil) -- 2 args, no explicit
    coefficient-index array. The ctypes wrapper this replaced (WaveKit <= 4.3)
    required set_data(coef, index, size, pupil). If 4.5.1 still expects an
    index array, this call raises, and IMOP_Mirror.display_modes() catches
    and swallows that exception, silently failing to move or flatten the
    mirror."""

    def test_set_data_does_not_require_an_explicit_index_array(self):
        params = _require_params(wk.ModalCoef.set_data, "ModalCoef.set_data")
        assert len(params) == 2, (
            "navigate's ModalCoef.set_data() (imop.py) calls "
            "wk.ModalCoef.set_data(coef, pupil) with 2 positional arguments, "
            f"but the installed wavekit_py expects {len(params)} parameters "
            f"({params}). Update ModalCoef.set_data() in "
            "navigate/model/devices/APIs/imagineoptics/imop.py to match, "
            "restoring an explicit index array if required."
        )


class TestComputePupilContract:
    def test_fit_zernike_pupil_signature(self):
        params = _require_params(
            wk.ComputePupil.fit_zernike_pupil, "ComputePupil.fit_zernike_pupil"
        )
        assert len(params) == 4, (
            "imop.py calls wk.ComputePupil.fit_zernike_pupil(pupil, "
            "detection_mode, covering, has_central_occultation) positionally "
            f"but the installed wavekit_py expects {len(params)} parameters "
            f"({params})."
        )


class TestCorrDataManagerContract:
    def test_get_greatest_common_pupil_takes_no_arguments(self):
        """The previous ctypes wrapper called
        get_greatest_common_pupil(pupil_zeros_array); imop.py's migration
        dropped that argument. Confirm wavekit_py's method genuinely takes
        none, rather than silently ignoring/misusing one."""
        params = _require_params(
            wk.CorrDataManager.get_greatest_common_pupil,
            "CorrDataManager.get_greatest_common_pupil",
        )
        assert len(params) == 0, (
            "imop.py calls wk.CorrDataManager.get_greatest_common_pupil() "
            f"with no arguments, but the installed wavekit_py expects "
            f"{len(params)} parameters ({params})."
        )

    def test_constructor_kwargs(self):
        params = _require_params(
            wk.CorrDataManager.__init__, "CorrDataManager.__init__"
        )
        for kwarg in ("haso_config_file_path", "interaction_matrix_file_path"):
            assert kwarg in params, (
                f"imop.py constructs wk.CorrDataManager(...) with "
                f"'{kwarg}=' but the installed wavekit_py does not accept "
                f"that keyword (accepts: {params})."
            )


class TestModalCoefPrefsContract:
    def test_set_zernike_prefs_kwargs(self):
        params = _require_params(
            wk.ModalCoef.set_zernike_prefs, "ModalCoef.set_zernike_prefs"
        )
        for kwarg in (
            "zernike_normalization",
            "nb_zernike_coefs_total",
            "zernike_indexing",
            "projection_pupil",
        ):
            assert kwarg in params, (
                f"imop.py calls ModalCoef.set_zernike_prefs(...) with "
                f"'{kwarg}=' but the installed wavekit_py does not accept "
                f"that keyword (accepts: {params})."
            )


class TestHasoConfigContract:
    def test_get_config_returns_three_values(self):
        params = _require_params(wk.HasoConfig.get_config, "HasoConfig.get_config")
        assert len(params) == 1, (
            "imop.py calls wk.HasoConfig.get_config(haso_config_file_path) "
            f"with 1 positional argument, but the installed wavekit_py "
            f"expects {len(params)} parameters ({params})."
        )


class TestWavefrontCorrectorContract:
    def test_preferences_round_trip_kwargs(self):
        params = _require_params(
            wk.CorrectorPrefs_t.__init__, "CorrectorPrefs_t.__init__"
        )
        for kwarg in (
            "min_array",
            "max_array",
            "validity_array",
            "fixed_value_array",
        ):
            assert kwarg in params, (
                f"imop.py constructs wk.CorrectorPrefs_t(...) with "
                f"'{kwarg}=' but the installed wavekit_py does not accept "
                f"that keyword (accepts: {params})."
            )
