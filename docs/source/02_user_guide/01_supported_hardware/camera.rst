.. _camera_configuration:

=======
Cameras
=======

The software supports camera-based acquisition. It can run both normal and rolling
shutter modes of contemporary scientific CMOS cameras.

-------------------

Daheng
------

MER2-1220-32U3C
~~~~~~~~~~~~~~~~~~~~~~~~~~~

More information on the Daheng MER2-1220-32U3C camera can be found
`here <https://en.daheng-imaging.com/show-106-1997-1.html>`_.

.. warning::

    This camera class has not been internally tested by our team. Users are advised to exercise caution when using it.

.. note::

    This camera requires Daheng Imaging's proprietary Python SDK and must be installed manually. Download the SDK `here <https://www.daheng-imaging.com/>`_. Locate 'gxipy' under: Development/Samples/Python/gxipy and then install it using pip. Also, this camera class uses the Line0 trigger input by default for external triggering.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: daheng.Daheng
                serial_number: "123456"
              defect_correct_mode: 2.0
              delay: 1.0  #ms
              settle_down: 0.1 #ms
              flip_x: False
              flip_y: False

|


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
              settle_down: 0.1 #ms
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
              settle_down: 0.1 #ms
              flip_x: False
              flip_y: False


|

------------------


ORCA-Lightning
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-   :ref:`Install Directions <dcam>`.
-   `ORCA-Lightning Manual <https://camera.hamamatsu.com/content/dam/hamamatsu-photonics/sites/static/sys/en/manual/C14120-20P_IM_En.pdf>`_.


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
              settle_down: 0.1 #ms
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
              settle_down: 0.1 #ms
              flip_x: False
              flip_y: False

|

------------------

Photometrics
------------

-   :ref:`Install Directions <pvcam>`.


.. note::

    **navigate** has been tested with the following versions of the Photometric's drivers:
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
              settle_down: 0.1 #ms
              flip_x: False
              flip_y: False
|

-----------------

Ximea
--------------------------------


MU196MR-ON
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            camera:
              hardware:
                type: ximea.MU196XR
                serial_number: 111
              defect_correct_mode: 2.0
              delay: 1.0  #ms
              settle_down: 0.1 #ms
              flip_x: False
              flip_y: False
              gain: 1
              pixel_size_in_microns: 1.4
              readout_port: 0
              readout_speed: 1.0
              settle_down: 0.0
              speed_table_index: 0
              supported_readout_directions: ['Top-to-Bottom']
              supported_sensor_modes: ['Normal']
              supported_trigger_sources: ['External']
              trigger_active: 1.0
              trigger_mode: 1.0
              trigger_polarity: 2.0
              trigger_source: 2.0
              x_pixels: 5112
              x_pixels_min: 192
              x_pixels_step: 24
              y_pixels: 3840
              y_pixels_min: 2
              y_pixels_step: 2
|

------------------

.. _synthetic_camera:

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
              settle_down: 0.1 #ms
              flip_x: False
              flip_y: False

|
