
==================
Deformable Mirrors
==================

Deformable mirrors enable correction for aberrations in the image that arise from
sample or system-specific distortions in the optical wavefront.

------------

Imagine Optic
-------------

We currently have support for a
`Mirao 52E <https://www.imagine-optic.com/products/deformable-mirror-mirao-52e/>`_.
The ``flat_path`` provides a path to a system correction ``.wcs`` file, an Imagine
Optic proprietary file that stores actuator voltages and corresponding Zernike
coefficients.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          mirror:
              hardware:
                type: ImagineOpticsMirror
                flat_path: D:\WaveKitX64\MirrorFiles\BeadsCoverslip_20231212.wcs
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
            type: SyntheticMirror
            flat_path: D:\WaveKitX64\MirrorFiles\BeadsCoverslip_20231212.wcs
            n_modes: 32


|
