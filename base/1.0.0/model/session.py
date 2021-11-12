"""
    Best place to store variables that can be shared between different classes.
    It defines an object that inherits from QObject, mainly to be able to emit signals.
    It overwrites the :meth:`~UUTrack.Model._session.__setattr__` for functionality,
    as well as the :meth:`~UUTrack.Model._session.__str__` for handy serialization.
    Storing of data is done via dictionaries.
        >>> session = Session()
        >>> session.Param1 = {'Value': 1}
        >>> print(session)
        Param1:
          Value: 1
        >>> session.Param1 = {'Value2': 2}
        >>> print(session)
        Param1:
          Value: 1
          Value2: 2
    Note that assigning a second value to Param1 does not overwrite the value, but appends it.
    Also note that the output of printing the session is a Yaml-ready text (2 space indentation, etc.).
    :copyright: 2017
    .. sectionauthor:: Aquiles Carattino <aquiles@aquicarattino.com>
"""

from __future__ import (absolute_import, division, print_function)

from builtins import (bytes, int, list, object, range, str,
    ascii, chr, hex, input, next, oct, open, pow, round, super,
    filter, map, zip)

import yaml
# PyYAML is a YAML parser and emitter for Python
# https://pyyaml.org/wiki/PyYAMLDocumentation

class _session():
    """
    Stores variables and other classes that are common to several UI or instances of the code.
    """

    def __init__(self, ConfigurationClass, SavingClass, verbose):
        """
        The class is prepared to load values from a Yaml file
        :param file: Path to the file where the config file
        is or a dictionary with the data to load.
        """
        super(_session, self).__init__()
        super().__setattr__('params', dict())
        data = ConfigurationClass
        self.verbose = verbose

        # Expects a dictionary to iterate through.
        for d in data:
            if self.verbose:
                print("Setting Attribute: ", d, "Value:", data[d])
            self.__setattr__(d, data[d])
            #TODO: Update View


    '''def __setattr__(self, key, value):
        if type(value) != type({}):
            raise Exception('Everything passed to a session has to be a dictionary')
        if key not in self.params:
            self.params[key] = dict()
            self.__setattr__(key, value)
        else:
            for k in value:
                if k in self.params[key]:
                    val = value[k]
                    self.params[key][k] = value[k]  # Update value
                    self.emit(SIGNAL('Updated'))
                else:
                    self.params[key][k] = value[k]
                    self.emit(SIGNAL('New'))

            super(_session, self).__setattr__(k, value[k])

    def __getattr__(self, item):
        if item not in self.params:
            return None
        else:
            return self.params[item]

    def __str__(self):
        """ Overrides the print(class).
        :return: a Yaml-ready string.
        """

        s = ''
        for key in self.params:
            s += '%s:\n' % key
            for kkey in self.params[key]:
                s += '  %s: %s\n' % (kkey, self.params[key][kkey])
        return s

    def serialize(self):
        """
        Function kept for compatibility. Now it only outputs the same information than print(class).
        :return: string Yaml-ready.
        """
        return self.__str__()

    def getParams(self):
        """Special class for setting up the ParamTree from PyQtGraph. It saves the iterating over all the variables directly
        on the GUI.
        :return: a list with the parameters and their types.
        """
        p = []
        for k in self.params:
            c = []
            for m in self.params[k]:
                if type(self.params[k][m]) == type([]):
                    s = {'name': m.replace('_', ' '), 'type': type(self.params[k][m]).__name__,
                         'values': self.params[k][m]}
                elif type(self.params[k][m]).__name__ == 'NoneType':
                    s = {'name': m.replace('_', ' '), 'type': "str", 'values': self.params[k][m]}
                elif type(self.params[k][m]).__name__ == 'long':
                    s = {'name': m.replace('_', ' '), 'type': "float", 'values': self.params[k][m]}
                else:
                    s = {'name': m.replace('_', ' '), 'type': type(self.params[k][m]).__name__,
                         'value': self.params[k][m], 'decimals': 6}
                c.append(s)

            a = {'name': k.replace('_', ' '), 'type': 'group', 'children': c}
            p.append(a)
        return p

    def copy(self):
        """Copies this class. Important not to overwrite the memory of a previously created session.
        :return: a session exactly the same as this one.
        """
        return _session(self.params)


if __name__ == '__main__':
    s = _session(file='../Config/Camera_defaults_example.yml')
    print('NEW')
    s.Camera = {'new': 'New'}
    print('OLD')
    s.Camera = {'model': 'Old'}
    # print(s.Monitor)
    # for k in s.params:
    #     print(k)
    #     for m in s.params[k]:
    #         print('   %s:  %s'%(m,s.params[k][m]))
    # print(s)

    print('SERIALIZE')
    ss = s.serialize()
    print(ss)

    session2 = _session(ss)
    print('=========SESSION2=============')
    print(session2)
    '''