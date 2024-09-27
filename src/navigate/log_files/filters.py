# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

# Standard Library Imports
import logging

# Third Party Library Imports

# Local Library Imports


class PerformanceFilter(logging.Filter):
    """
    A custom logging filter to exclude performance messages.

    This filter is designed to be used with the Python logging module. It includes
    log records whose messages do not start with "Performance" or "Spec."
    """

    def filter(self, record):
        """Filter out performance messages

        Parameters
        ----------
        record : logging.LogRecord
            The log record to filter

        Returns
        -------
        bool
            True if the record should be logged, False otherwise
        """
        # Checking if log message should be sent to performance.log
        # based on if it starts with Performance or Spec
        if record.getMessage().startswith("Performance"):
            return True
        if record.getMessage().startswith("Spec"):
            return True

        return False


class NonPerfFilter(logging.Filter):
    """
    A custom logging filter to exclude non-performance messages.

    This filter is designed to be used with the Python logging module. It excludes
    log records whose messages do not start with "Performance" or "Spec."
    """

    def filter(self, record):
        """Filter out non-performance messages

        Parameters
        ----------
        record : logging.LogRecord
            The log record to filter

        Returns
        -------
        bool
            True if the record should be logged, False otherwise
        """
        # Making sure performance data only goes to performance.log

        if record.getMessage().startswith("Performance"):
            return False
        if record.getMessage().startswith("Spec"):
            return False
        return True

class DebugFilter(logging.Filter):
    """
    A custom logging filter to include only DEBUG level messages.
    """
    def filter(self, record):
        return record.levelno == logging.DEBUG
