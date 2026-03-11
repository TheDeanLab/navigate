===================
Proxy Configuration
===================

Overview
--------

If you are installing **navigate** behind an institutional proxy, you may need to configure proxy settings so ``pip`` and ``conda`` can download packages.

Solution and Verification
-------------------------

1. Open system environment variable settings (Windows) or your OS equivalent.
2. Create these variables:

   - ``HTTP_PROXY=http://proxy.your_university.edu:1234``
   - ``HTTPS_PROXY=http://proxy.your_university.edu:1234``

3. If installation still fails, try:

   - ``HTTPS_PROXY=https://proxy.your_university.edu:1234``

4. If problems persist, configure proxy settings directly in package-manager config files.

   - Conda config file (Windows): :file:`C:\\Users\\<UserProfile>\\.condarc`
   - pip config file (Windows): :file:`C:\\Users\\<UserProfile>\\pip\\pip.ini`

5. You can also set proxy variables in an Anaconda Prompt:

.. code-block:: bat

   set https_proxy=http://username:password@proxy.example.com:8080
   set http_proxy=http://username:password@proxy.example.com:8080
