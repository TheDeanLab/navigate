====================
REST-APIs
====================

**navigate** has the ability to communicate with other image analysis software through REST-API interfaces.
Here is an example using ilastik to segment images and mark positions for higher resolution in a multiscale 
microscope.

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
"flask --app navigate_server run".

If ilastik server runs on a different machine, run the command: "flask --app navigate_server run --host 0.0.0.0"

If want to specify a specific port, add parameter "--port port-number".

Set rest-api configuration
######################################

Specify url address of the ilastik server in the configuration file (.navigate/config/rest_api_config.yml).
If the ilastik server runs on the same machine as navigate, set the configuration as follow:

.. code-block::

    Ilastik:
    url: 'http://127.0.0.1:5000/ilastik'


If the ilastik server runs on a different machine, set the configuration as follow:

.. code-block::

    Ilastik:
    url: 'http://remote-url:5000/ilastik'


** here uses the default port 5000, if another one please overwrite it.

Load and set ilastik project
############################

#. Select and click menu :menuselection:`Features --> Ilastik Settings`.


    .. image:: images/ilastik_1.png

#. Load one ilastik segmentation project file from the pop-up window

    .. image:: images/ilastik_2.png

    .. image:: images/ilastik_3.png

#. Select target labels and the way to use the segmentation (display or mark positions), then click "Confirm".

    .. image:: images/ilastik_5.png


Use ilastik feature
#######################

#. Choose "Customize" acquisition mode, and select the menu :menuselection:`Features --> Ilastik Segmentation`.

    .. image:: images/ilastik_6.png


#. Click guilabel:`Acquire` to run acquisition.

If you choose to show segmentation only, click guilabel`Confirm` in the popup window directly.

   .. image:: images/ilastik_7.png

   .. image:: images/ilastik_9.png

   

If you choose to "mark positions", please click "Ilastik " in the pop-up window and set the target microscope name and zoom value.

    .. image:: images/ilastik_10.png

    .. image:: images/ilastik_8.png
        

The positions will be populated to the multi-position table.

    .. image:: images/ilastik_11.png

The positions looks like the following if saves it in a cvs file.

    .. image:: images/ilastik_12.png

    .. image:: images/ilastik_13.png


