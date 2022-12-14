# Axially Swept Light-Sheet Microscopy

[![Tests](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/push_checks.yaml/badge.svg)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/push_checks.yaml)
[![codecov](https://codecov.io/gh/TheDeanLab/ASLM/branch/develop/graph/badge.svg?token=270RFSZGG5)](https://codecov.io/gh/TheDeanLab/ASLM)

### Documentation
Please refer to and contribute to the documentation, which can be found on GitHub Pages: [https://thedeanlab.github.io/ASLM/](https://thedeanlab.github.io/ASLM/).

### Project Philosophy
* Minimal number of dependencies. Prioritize standard library imports for maximum stability.
* Abstraction layer to drive different camera types, etc.
* Brutally obvious, well-documented, clean code so that it can be understood up with by future users years from now.
* Maximize productivity for biological users.
* Performant and responsive. 
* Model-View-Controller architecture.  

### GPU Dependencies for TensorFlow (1.15), PyTorch (1.10.2), CuPy, ...
Excellent directions can be found for CuPy. https://docs.cupy.dev/en/stable/install.html
 * [NVIDIA CUDA Version 11.2](https://developer.nvidia.com/cuda-11.2.0-download-archive?target_os=Windows&target_arch=x86_64&target_version=10&target_type=exelocal)
 * [cuDNN SDK 8.4.1](https://developer.nvidia.com/rdp/cudnn-download)
 * NVIDIA Graphics Driver >450.80.02
 * TensorRT 7
 * Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017 and 2019 
 
### Installation with Conda
~~~
conda create -n ASLM python=3.9.7
conda activate ASLM
python -m pip install --upgrade pip
mkdir ~/Git/
cd ~/Git/
git clone https://github.com/AdvancedImagingUTSW/ASLM.git
cd ASLM
pip install -e .
~~~

To run, enter `aslm` in the `ASLM` Anaconda environment.

### Trouble Shooting
If running the software on campus at UTSW you may need to update some of your proxy settings to allow pip/conda to install the proper packages.
* This can be done by going to Environment Variables for Windows, or another OS equivalent.
* Create the following variables at the system level: 
    Variable = HTTP_PROXY; Value = http://proxy.swmed.edu:3128
    Variable = HTTPS_PROXY; Value = http://proxy.swmed.edu:3128 (please see that they are both http, this is purposeful and not a typo)
* If you continue to have issues then change the value of Variable HTTPS_PROXY to https://proxy.swmed.edu:3128
* If you still have issues then you will need to create/update both configuration files for conda and pip to include proxy settings, if they are not in the paths below you will need to create them. This assumes a Windows perspective. Mac/Linux users will have different paths, they can be found online.
    Conda's Config file = C:\Users\UserProfile\.condarc
    Pip's Config file = C:\Users\UserProfile\pip\pip.ini
* You can also try to set the proxy from within the Anaconda Prompt:
	set https_proxy=http://username:password@proxy.example.com:8080
	set http_proxy=http://username:password@proxy.example.com:8080


### Command Line Input Arguments (optional)
* --synthetic_hardware or -sh: Use simulated hardware.

~~~
python main.py --synthetic_hardware -sh
~~~

### Authors
* Kevin Dean
* Zach Marin
* Xiaoding 'Annie' Wang
* Dax Collison
* Sampath Rapuri
* Samir Mamtani
* Renil Gupta
* Andrew Jamieson

