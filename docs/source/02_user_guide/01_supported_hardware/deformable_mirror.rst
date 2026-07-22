.. _deformable_mirror_configuration:

==================
Deformable Mirrors
==================

Deformable mirrors enable correction for aberrations in the image that arise from
sample or system-specific distortions in the optical wavefront.

------------

Imagine Optic
-------------

Mirao 52E
~~~~~~~~~

We currently have support for a
`Mirao 52E <https://www.imagine-optic.com/products/deformable-mirror-mirao-52e/>`_,
driven through Imagine Optic's ``wavekit_py`` SDK (tested against WaveKit 4.5.1).
The ``flat_path`` provides a path to a system correction ``.wcs`` file, an Imagine
Optic proprietary file that stores actuator voltages and corresponding Zernike
coefficients.

The remaining paths point to the WaveKit config/calibration files generated when
the mirror and HASO sensor were set up and calibrated (via Imagine Optic's
WaveSuite software), and are specific to each physical mirror/HASO pair:

* ``wfc_config_file_path``: the wavefront-corrector ``.dat`` config file.
* ``haso_config_file_path``: the HASO sensor ``.dat`` config file.
* ``positions_file_path``: a default ``.wcs`` actuator-positions file.
* ``interaction_matrix_file_path``: the ``.aoc`` interaction matrix used to
  build the command matrix.

All four paths must be supplied explicitly in the microscope configuration --
there are no built-in defaults, since these files are specific to each mirror.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          mirror:
              hardware:
                type: ImagineOpticsMirror
                flat_path: D:\WaveKitX64\MirrorFiles\BeadsCoverslip_20231212.wcs
                wfc_config_file_path: D:\WaveKitX64\MirrorFiles\WaveFrontCorrector_Mirao52-e_0259.dat
                haso_config_file_path: D:\WaveKitX64\MirrorFiles\HASO4_first_7458.dat
                positions_file_path: D:\WaveKitX64\MirrorFiles\OPMv3_SysCorr_517nm_20230324.wcs
                interaction_matrix_file_path: D:\WaveKitX64\MirrorFiles\VAST_Sept_2023_b.aoc
              n_modes: 32


|

-------------

Synthetic Mirror
----------------
It is not necessary to have a deformable mirror to run the software. If no deformable
mirror is present, but one wants to evaluate the deformable mirror correction features,
one must configure the software to use a synthetic deformable mirror.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          mirror:
            hardware:
              type: SyntheticMirror
              flat_path: D:\WaveKitX64\MirrorFiles\BeadsCoverslip_20231212.wcs
            n_modes: 32


|
