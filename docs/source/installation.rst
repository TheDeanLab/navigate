Software Installation
============
First we need to setup our python enviornment. Head over to the `miniconda website <https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links>`_
and install the appropriate version based on your operating system.

.. tip::

    It is also handy to have the `conda cheatsheet <https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf>`_ open when first using miniconda to get accustomed to the commands available.

Once you have installed miniconda its time to use it to create our python enviornment.
Search your computer for the anaconda prompt window. If you are on a Linux/Mac you can just use the terminal.
From there you will need to use the below commands:

.. code-block::

    (base) MyComputer ~ $ conda create -n ASLM python=3.9.7

This will create our python enviornment with the correct version.

.. code-block::

    (base) MyComputer ~ $ conda activate ASLM

Now we need to activate our new enviornment.

.. code-block::

    (ASLM) MyComputer ~ $ python -m pip install --upgrade pip

We will now update our package manager. Python has a builtin called pip. Also notice that our enviornment is now reflected on the far left of our terminal as (ASLM). This will confirm you are in the correct environment.

.. code-block::

    (ASLM) MyComputer ~ $ mkdir ~/MyFolderName
    (ASLM) MyComputer ~ $ cd ~/MyFolderName

It is important to stay organized. Create a folder in a path/location that is easy to find and access. We will be saving the repo(the code!) here. After creating the folder we can change to it.

.. code-block::

    (ASLM) MyComputer MyFolderName $ git clone https://github.com/AdvancedImagingUTSW/ASLM.git

After creating the folder and changing to it, we need to download the code. We can use the git command for this task.

.. note::

    If you do not have `Git already downloaded <https://git-scm.com/downloads>`_. You will need to do that before downloading the repo.

.. code-block::

    (ASLM) MyComputer MyFolderName $ cd ASLM
    (ASLM) MyComputer ASLM $ pip install -e .

The last step requires you to change into the ASLM directory and the install the repo as a package locally on your machine.

Finally once this is all finished you can run the software with the below command.

.. code-block::

    (ASLM) MyComputer ASLM $ aslm

.. note::

    If you are running the software on a computer that does not have the appropriate hardware you will need to add the flag -sh after aslm:

        aslm -sh



After completeting these steps you will only need to do the below to start the software upon opening the prompt:

.. code-block::

    (base) MyComputer ~ $ conda activate ASLM
    (ASLM) MyComputer ~ $ aslm

GPU Dependencies
============
A CUDA GPU device is necessary to use TensorFlow (1.15), PyTorch (1.10.2), CuPy, ...
`Excellent directions can be found for CuPy <https://docs.cupy.dev/en/stable/install.html>`_.
    * `NVIDIA CUDA Version 11.2 <https://developer.nvidia.com/cuda-11.2.0-download-archive?target_os=Windows&target_arch=x86_64&target_version=10&target_type=exelocal>`_
    * `cuDNN SDK 8.4.1 <https://developer.nvidia.com/rdp/cudnn-download>`_
    * NVIDIA Graphics Driver >450.80.02
    * TensorRT 7
    * Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017 and 2019

Troubleshooting
============

If running the software on campus at UTSW you may need to update some of your proxy settings to allow pip/conda to install the proper packages.
    * This can be done by going to Environment Variables for Windows, or another OS equivalent.
    * Create the following variables at the system level:
        *  Variable = HTTP_PROXY; Value = http://proxy.swmed.edu:3128
        *  Variable = HTTPS_PROXY; Value = http://proxy.swmed.edu:3128 (please see that they are both http, this is purposeful and not a typo)
    * If you continue to have issues then change the value of Variable HTTPS_PROXY to https://proxy.swmed.edu:3128
    * If you still have issues then you will need to create/update both configuration files for conda and pip to include proxy settings, if they are not in the paths below you will need to create them. This assumes a Windows perspective. Mac/Linux users will have different paths, they can be found online.
        *  Conda's Config file = C:\Users\UserProfile\.condarc
        *  Pip's Config file = C:\Users\UserProfile\pip\pip.ini
    * You can also try to set the proxy from within the Anaconda Prompt:
	  *  set https_proxy=http://username:password@proxy.example.com:8080
	  *  set http_proxy=http://username:password@proxy.example.com:8080
