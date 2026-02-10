# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

"""Runtime guard that logs off-main-thread Tk access."""

from collections import Counter
from functools import wraps
import logging
import threading
import traceback

_patch_lock = threading.Lock()


def install_tk_thread_guard(root, logger: logging.Logger = None) -> bool:
    """Install a best-effort logger for off-main-thread Tk calls.

    Parameters
    ----------
    root : tkinter.Tk
        Tk root instance.
    logger : logging.Logger, optional
        Logger used for warnings. Defaults to this module logger.

    Returns
    -------
    bool
        True if patch installed in this call, False if already installed.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    tkapp_cls = type(root.tk)
    methods_to_wrap = (
        "call",
        "eval",
        "evalfile",
        "setvar",
        "getvar",
        "globalsetvar",
        "globalgetvar",
    )

    with _patch_lock:
        if getattr(tkapp_cls, "_navigate_tk_guard_installed", False):
            return False

        main_thread_ident = threading.get_ident()
        violation_counts = Counter()

        for method_name in methods_to_wrap:
            original = getattr(tkapp_cls, method_name, None)
            if original is None or not callable(original):
                continue

            @wraps(original)
            def wrapped(self, *args, __orig=original, __name=method_name, **kwargs):
                if threading.get_ident() != main_thread_ident:
                    key = (__name, args[0] if args else "")
                    violation_counts[key] += 1
                    count = violation_counts[key]
                    # Log first few violations, then sample periodically.
                    if count <= 5 or count % 100 == 0:
                        stack = ""
                        if count <= 3:
                            stack = "".join(traceback.format_stack(limit=8)[:-1])
                        logger.warning(
                            "Tk off-main-thread access detected: %s(%r) from thread '%s' [count=%d]%s%s",
                            __name,
                            args[0] if args else None,
                            threading.current_thread().name,
                            count,
                            "\nCall stack (most recent call last):\n" if stack else "",
                            stack,
                        )
                return __orig(self, *args, **kwargs)

            setattr(tkapp_cls, method_name, wrapped)

        setattr(tkapp_cls, "_navigate_tk_guard_installed", True)
        setattr(tkapp_cls, "_navigate_tk_guard_main_thread_ident", main_thread_ident)
        logger.info("Installed Tk thread guard for off-main-thread access logging.")
        return True
