User Guide
==========

Installation
------------
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
    (ASLM) MyComputer ~ $ aslm -sh