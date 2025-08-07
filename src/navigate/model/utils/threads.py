# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Standard Library Imports
import threading
import logging
# Local Imports
from navigate.model.utils.exceptions import UserVisibleException

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class ThreadWithWarning(threading.Thread):
    """A custom thread class that raises a warning to the user if any error is raised."""

    def __init__(self, *args, **kwargs):
        """Initialize the ThreadWithWarning."""
        if "warning_queue" in kwargs:
            self._warning_queue = kwargs["warning_queue"]
            del kwargs["warning_queue"]
        self._logger = logger
        if "logger" in kwargs:
            self._logger = kwargs["logger"]
            del kwargs["logger"]
        super().__init__(*args, **kwargs)

    def run(self):
        """Run the thread and handle warnings."""
        try:
            super().run()
        except Exception as e:
            self._logger.error(f"Error in thread {self.name}: {e}")
            if hasattr(self, "_warning_queue") and isinstance(e, UserVisibleException):
                self._warning_queue.put(("warning", str(e)))
            raise e

