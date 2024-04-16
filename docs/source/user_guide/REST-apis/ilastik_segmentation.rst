=============================
Analyzing Images via REST-API
=============================

**navigate** has the ability to communicate with other image analysis software through REST-API interfaces.
In general, the REST-API is used to communicate with software that has different or conflicting
dependencies with the **navigate** codebase. Data is transferred via HTTP requests and responses,
which is faster and more efficient than locally saving the data and then loading it into another
piece of software, but slower than direct access of the data in memory.

Here is an example using `ilastik <https://www.nature.com/articles/s41592-019-0582-9>`_ to segment
images and mark positions for higher resolution in a multiscale
microscope. ilastik is a powerful image analysis software that enables users to train
a support vector machine learning classifier to segment images using a combination of
intensity, texture, and shape features. More information about ilastik can be found
`here <https://www.ilastik.org/>`_.

Install navigate-ilastik server
###########################################

Install ilastik first and then follow the steps below:

.. code-block::

    conda activate your-ilastik-environment
    python -m pip install --upgrade pip
    mkdir ~/Git/
    cd ~/Git/
    git clone https://github.com/TheDeanLab/navigate-ilastik-server
    cd navigate-ilastik-server
    pip install -e .

Visit `navigate-ilastik-server <https://github.com/TheDeanLab/navigate-ilastik-server>`_ for more information.

Run navigate-ilastik-server
#####################################

In the conda environment command window, go to the folder "navigate-ilastik-server", run the command:

.. code-block::

    flask --app navigate_server run

If ilastik server runs on a different machine, run the command:

.. code-block::

    flask --app navigate_server run --host 0.0.0.0

If want to specify a specific port, add parameter ``--port port-number``.

Set REST-API configuration
######################################

Specify url address of the ilastik server in the configuration file (.navigate/config/rest_api_config.yml).
If the ilastik server runs on the same machine as navigate, set the configuration as follow:

.. code-block::

    ilastik:
    url: 'http://127.0.0.1:5000/ilastik'


If the ilastik server runs on a different machine, set the configuration as follow:

.. code-block::

    ilastik:
    url: 'http://remote-url:5000/ilastik'

.. note::

    As shown here, the default port is 5000. If another port is used, provide it here.

Load and set ilastik project
############################

#. Select and click menu :menuselection:`Features --> ilastik Settings`.

    .. image:: images/ilastik_1.png
     :width: 400px
     :align: center

#. Load one ilastik segmentation project file from the pop-up window

    .. image:: images/ilastik_2.png
     :width: 400px
     :align: center

    .. image:: images/ilastik_3.png
     :width: 400px
     :align: center

#. Select target labels and the way to use the segmentation (display or mark positions), then click :guilabel:`Confirm`.

    .. image:: images/ilastik_5.png
     :width: 400px
     :align: center

Use ilastik feature
#######################

#. Choose :guilabel:`Customize` acquisition mode, and select the menu :menuselection:`Features --> ilastik Segmentation`.

    .. image:: images/ilastik_6.png
     :width: 400px
     :align: center

#. Click :guilabel:`Acquire` to run acquisition.

If you choose to show segmentation only, click :guilabel:`Confirm` in the popup window directly.

   .. image:: images/ilastik_7.png
     :width: 400px
     :align: center

   .. image:: images/ilastik_9.png
     :width: 400px
     :align: center


If you choose to :guilabel:`Mark Position`, please click :guilabel:`ilastik` in the pop-up window and set the target microscope name and zoom value.

    .. image:: images/ilastik_10.png
     :width: 400px
     :align: center

    .. image:: images/ilastik_8.png
     :width: 400px
     :align: center

The positions will be populated to the multi-position table.

    .. image:: images/ilastik_11.png
     :width: 400px
     :align: center

The positions looks like the following if saves it in a CSV file.

    .. image:: images/ilastik_12.png
     :width: 400px
     :align: center

    .. image:: images/ilastik_13.png
     :width: 400px
     :align: center
