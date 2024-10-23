# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

import importlib
from threading import Lock

from typing_extensions import Optional


def combine_funcs(*funclist):
    """this function will combine a list of functions to a new function

    Parameters
    ----------
    funclist: list
        a list of functions

    Returns
    -------
    new_func: function
        a new function
    """

    def new_func():
        for func in funclist:
            if callable(func):
                func()

    return new_func


def build_ref_name(separator, *args):
    """this function will build a reference name

    Parameters
    ----------
    separator: str
        the separator between each argument
    args: list
        a list of arguments

    Returns
    -------
    ref_name: str
        the reference name
    """
    alist = list(map(lambda a: str(a), args))
    return separator.join(alist)


def copy_proxy_object(content):
    """This function will serialize proxy dict and list

    Parameters
    ----------
    content: dict/list
        the proxy object

    Returns
    -------
    result: dict/list
    """
    from multiprocessing import managers

    def func(content):
        if type(content) == managers.DictProxy:
            result = {}
            for k in content.keys():
                result[k] = func(content[k])
        elif type(content) == managers.ListProxy:
            result = []
            for v in content:
                result.append(func(v))
        else:
            result = content
        return result

    return func(content)


def load_module_from_file(module_name: str, file_path: str) -> Optional[any]:
    """This function will load python file from file path as a module

    Parameters
    ----------
    module_name: str
        the module name
    file_path: os.path/str
        the python file path

    Returns
    -------
    module: Optional[Any]
        The module. None if the module is not found.
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ModuleNotFoundError:
        return None
    return module


class VariableWithLock:
    def __init__(self, VariableType):
        self.lock = Lock()
        self.value = VariableType()

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()
