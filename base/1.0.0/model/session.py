"""
    Best place to store variables that can be shared between different classes.
    It defines an object that inherits from QObject, mainly to be able to emit signals.
    It overwrites the :meth:`~UUTrack.Model.Session.__setattr__` for functionality,
    as well as the :meth:`~UUTrack.Model.Session.__str__` for handy serialization.
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

class Session:
    """
    Stores variables and other classes that are common to several UI or instances of the code.
    """

    def __init__(self, file_path=None, verbose=False):
        """
        The class is prepared to load values from a Yaml file
        :param file: Path to the file where the config file is or a dictionary with the data to load.
        """

        super(Session, self).__init__()
        super().__setattr__('params', dict())

        """
        Load a Yaml file and stores the values in the object.
        :param file: Path to the file where the config file is.
        """
        if file_path == None:
            print("No file provided to load_yaml_config()")
            sys.exit(1)
        else:
            # If the file exists, load it
            if type(file_path) == type('path'):
                with open(file_path) as f:
                    try:
                        config_data = yaml.load(f, Loader=yaml.FullLoader)
                    except yaml.YAMLError as yaml_error:
                        print(yaml_error)

            if verbose:
                for data_iterator in config_data:
                    print("Loaded:", data_iterator)

        # Set the attributes with the custom __setattr__
        for data_iterator in config_data:
            self.__setattr__(data_iterator, config_data[data_iterator], verbose)
            if verbose:
                print("Set:", data_iterator)

    def __setattr__(self, key, value, verbose=False):
        """
        Custom setter for the attributes.
        :param key: Name of the attribute.
        :param value: Value of the attribute.
        """
        if type(value) != type({}):
            raise Exception('Everything passed to a session must be a dictionary')

        if key not in self.params:
            self.params[key] = dict()
            self.__setattr__(key, value)
            if verbose:
                print("Added:", key)
                print("Value:", value)

        else:
            for k in value:
                if k in self.params[key]:
                    val = value[k]

                    # Update value
                    self.params[key][k] = value[k]
                    if verbose:
                        print("Updated:", key)
                        print("Value:", val)
                    #TODO: Update GUI?
                    #self.emit(SIGNAL('Updated'))

                else:
                    self.params[key][k] = value[k]
                    if verbose:
                        print("Updated:", key)
                        print("Value:", value)
                    #TODO: Update GUI?
                    #self.emit(SIGNAL('New'))

            super(Session, self).__setattr__(k, value[k])


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

    def get_parameters(self):
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
        return Session(self.params)


if __name__ == '__main__':
    """ Testing Section """
    s = Session(file='../config/configuration.yml')
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

    session2 = Session(ss)
    print('=========SESSION2=============')
    print(session2)
