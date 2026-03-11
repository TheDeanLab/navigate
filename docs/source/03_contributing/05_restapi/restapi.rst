========
REST API
========

**navigate** can communicate with external image-analysis software through a REST API. This integration pattern is useful when external tools require dependencies that conflict with the core **navigate** environment.

Data is exchanged through HTTP requests and responses. This is usually more efficient than writing data to disk and reloading it in another application, although it is typically slower than direct in-memory access.

For an example integration with ilastik, see :ref:`the ilastik case study <case_study_ilastik>`. The corresponding plugin is available in the `navigate ilastik Server repository <https://github.com/TheDeanLab/navigate-ilastik-server>`_.
