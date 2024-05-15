
.. _camera_configuration:
=======
Cameras
=======

The software supports camera-based acquisition. It can run both normal and rolling
shutter modes of contemporary scientific CMOS cameras.

Hamamatsu
---------

ORCA-Flash4.0 V3
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-   :ref:`Install Directions <dcam>`.
-   `ORCA-Flash 4.0 v3 Manual <https://www.hamamatsu
    .com/us/en/product/cameras/cmos-cameras/C13440-20CU.html>`_.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: HamamatsuOrca
                serial_number: 111
                camera_connection:
              defect_correct_mode: 2.0
              delay: 1.0
              flip_x: False
              flip_y: False
              count: 5

|

------------------


ORCA-Fusion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**navigate** works with both the back-thinned and front-illuminated versions of the
ORCA-Fusion.

-   :ref:`Install Directions <dcam>`.
-   `ORCA-Fusion Manual <https://www.hamamatsu
    .com/jp/en/product/cameras/cmos-cameras/C15440-20UP.html>`_.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: HamamatsuOrcaFusion
                serial_number: 111
                camera_connection:
              defect_correct_mode: 2.0
              delay: 1.0
              flip_x: False
              flip_y: False
              count: 5

|

------------------


ORCA-Lightning
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-   :ref:`Install Directions <dcam>`.
-   `ORCA-Lightning Manual <https://www.hamamatsu
    .com/us/en/product/cameras/cmos-cameras/C14120-20P.html>`_.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: HamamatsuOrcaLightning
                serial_number: 111
                camera_connection:
              defect_correct_mode: 2.0
              delay: 1.0
              flip_x: False
              flip_y: False
              count: 5

|

------------------


ORCA-Fire
~~~~~~~~~~~~~~~~~~~~~~~~~~~


-   :ref:`Install Directions <dcam>`.
-   `ORCA-Fire Manual <https://www.hamamatsu.com/us/en/product/cameras/cmos-cameras/C16240-20UP.html>`_.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: HamamatsuOrcaFire
                serial_number: 111
                camera_connection:
              defect_correct_mode: 2.0
              delay: 1.0
              flip_x: False
              flip_y: False
              count: 5
|

------------------

Photometrics
------------

-   :ref:`Install Directions <pvcam>`.


Iris 15
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: Photometrics
                serial_number: 111
                camera_connection: PMPCIECam00
              defect_correct_mode: 2.0
              delay: 1.0
              flip_x: False
              flip_y: False
              count: 5

|

------------------


Synthetic Camera
----------------

The synthetic camera simulates noise images from an sCMOS camera. If no camera is present,
the synthetic camera class must be used.

.. collapse:: Configuration File

    .. code-block:: yaml

       microscopes:
        microscope_name:
            camera:
              hardware:
                type: synthetic
                serial_number: 111
                camera_connection:
              defect_correct_mode: 2.0
              delay: 1.0
              flip_x: False
              flip_y: False
              count: 5

|
