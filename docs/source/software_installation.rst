Software Installation
*********************

Download Git
------------
If you do not have `Git already installed <https://git-scm.com/downloads>`_, you will need to do so before downloading the repo.
We also recommend installing `GitHub Desktop <https://desktop.github.com/>`_ for a more user-friendly experience.


Setup your Python Environment
-----------------------------
Head over to the `miniconda website <https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links>`_
and install the appropriate version based on your operating system.

.. tip::

    It is also handy to have the `conda cheatsheet <https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf>`_ open when first using miniconda to get accustomed to the commands available.



* Windows: Search your computer for the anaconda prompt window. Given how frequently you will use this, we recommend pinning it to your taskbar.
* Linux/Mac: Search your computer for Terminal.

**Create a python environment called Navigate with Python version 3.9.7**::

    (base) MyComputer ~ $ conda create -n navigate python=3.9.7

.. note::
    If you are inside of a firewall, e.g., on the UTSW campus, you will likely run into a proxy error.
    See the Troubleshooting section below for information on how to add the proxy address to your environment variables to circumvent this problem.


**Activate the Navigate environment**::

    (base) MyComputer ~ $ conda activate navigate

The active environment is shown in parentheses on the far-left.  Originally, we were in the miniconda base environment.
After activatin the Navigate environment, it should now show (NAVIGATE).

**Update the pip python package manager**::

    (Navigate) MyComputer ~ $ python -m pip install --upgrade pip


**Create a directory where the repository will be cloned**
    We recommend a path/location that is easy to find and access such as the your Desktop or Documents.
    Once the folder is created, we will want to change that to our working directory (e.g., cd)

* Windows::

    (Navigate) C:\Users\Dean-Lab cd Desktop
    (Navigate) C:\Users\Dean-Lab\Desktop mkdir Code
    (Navigate) C:\users\Dean-Lab\Desktop cd Code

* Linux/Mac::

    (Navigate) MyComputer ~ $ mkdir ~/Desktop/Code
    (Navigate) MyComputer ~ $ cd ~/Desktop/Code

**Clone the GitHub repository**::

    (Navigate) MyComputer MyFolderName $ git clone https://github.com/TheDeanLab/navigate.git

**Install the Navigate repository**

The last step requires you to change into the Navigate directory and the install the repo as a package locally on your machine.::

    (Navigate) MyComputer MyFolderName $ cd navigate
    (Navigate) MyComputer Navigate $ pip install -e .


**Run the Navigate software**::
    (Navigate) MyComputer Navigate $ navigate

.. note::

    If you are running the software on a computer that does not have the appropriate hardware you will need to add the flag -sh after navigate:

        navigate -sh


After completeting these steps you will only need to do the below to start the software upon opening the prompt:

.. code-block::

    (base) MyComputer ~ $ conda activate navigate
    (Navigate) MyComputer ~ $ navigate

.. note::

    If you are running Windows, you can create a desktop shortcut to Navigate by right-clicking the Desktop, navigating to New and then Shortcut and entering ``%windir%\system32\cmd.exe "/c" C:\path\to\miniconda\Scripts\activate.bat navigate && navigate`` into the location text box.

Troubleshooting
---------------

If running the software on campus at UTSW you may need to update some of your proxy settings to allow pip/conda to install the proper packages.
    * This can be done by going to Environment Variables for Windows, or another OS equivalent.
    * Create the following new System Variables:
        *  Variable = HTTP_PROXY; Value = http://proxy.swmed.edu:3128
        *  Variable = HTTPS_PROXY; Value = http://proxy.swmed.edu:3128 (please see that they are both http, this is purposeful and not a typo)
    * If you continue to have issues then change the value of Variable HTTPS_PROXY to https://proxy.swmed.edu:3128
    * If you still have issues then you will need to create/update both configuration files for conda and pip to include proxy settings, if they are not in the paths below you will need to create them. This assumes a Windows perspective. Mac/Linux users will have different paths, they can be found online.
        *  Conda's Config file = C:\Users\UserProfile\.condarc
        *  Pip's Config file = C:\Users\UserProfile\pip\pip.ini
    * You can also try to set the proxy from within the Anaconda Prompt:
	  *  set https_proxy=http://username:password@proxy.example.com:8080
	  *  set http_proxy=http://username:password@proxy.example.com:8080
