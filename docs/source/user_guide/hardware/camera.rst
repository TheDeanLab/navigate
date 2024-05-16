
.. _camera_configuration:
=======
Cameras
=======

The software supports camera-based acquisition. It can run both normal and rolling
shutter modes of contemporary scientific CMOS cameras.

Hamamatsu
---------

.. note::

    **navigate** has been tested with the following versions of the Hamamatsu's
    drivers:

    - DCAM API: 20.7.641, 21.7.4321, 22.9.6509, 22.11.4321, 23.12.6736
    - Camera Firmware: 2.21B, 2.53.A, 3.20.A, 4.30.B,
    - Active Silicon CoaXpress: 1.10, 1.13, 1.21.


-----------------

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
              delay: 1.0  #ms
              flip_x: False
              flip_y: False


|

------------------


ORCA-Fusion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
              delay: 1.0  #ms
              flip_x: False
              flip_y: False


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
              delay: 1.0  #ms
              flip_x: False
              flip_y: False


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
              delay: 1.0  #ms
              flip_x: False
              flip_y: False

|

------------------

Photometrics
------------

-   :ref:`Install Directions <pvcam>`.


.. note::

    **navigate** has been tested with the following versions of the Photometric's
    drivers:

    - PVCAM: 3.9.13

-----------------

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
              delay: 1.0  #ms
              flip_x: False
              flip_y: False


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
              delay: 1.0  #ms
              flip_x: False
              flip_y: False

|
