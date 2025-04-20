Proxy Configuration
===================

Overview
--------
If the software is run at an institution with a proxy, you may need to update your proxy settings to allow ``pip`` and ``conda`` to install the proper packages.

Solution and Verification
-------------------------

* Setting up your proxy can be done by going to Environment Variables for Windows, or another OS equivalent.
* Create the following new System Variables (please see that they are both http, this is purposeful and not a typo):

    * Variable = HTTP_PROXY; Value = http://proxy.your_university.edu:1234
    * Variable = HTTPS_PROXY; Value = http://proxy.your_university.edu:1234

* If you continue to have issues then change the value of Variable HTTPS_PROXY to https://proxy.your_university.edu:1234

* If you still have issues then you will need to create/update both configuration files for conda and pip to include proxy settings, if they are not in the paths below you will need to create them. This assumes a Windows perspective. Mac/Linux users will have different paths, they can be found online.

    * The ``conda`` configuration file can be found at C:\\Users\\UserProfile\\.condarc
    * The ``pip`` configuration file can be found at C:\\Users\\UserProfile\\pip\\pip.ini

* You can also try to set the proxy from within the Anaconda Prompt:
*  ``set https_proxy=http://username:password@proxy.example.com:8080``
*  ``set http_proxy=http://username:password@proxy.example.com:8080``