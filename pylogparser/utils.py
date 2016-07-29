##########################################################################
# pylogparser - Copyright (C) AGrigs, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function


class Singleton(type):
    """ This metaclass implements the singleton design pattern.
    """
    # Global instance parameter reference
    instance = None

    def __call__(cls, *args, **kwargs):
        """ This method is used to create a unique instance.

        Parameters
        ----------
        cls: meta class (mandatory)
            a meta class.
        """
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


def tree(data, padding=None, level=-1, display_content=False, current_level=0):
    """ Prints the tree structure of log data.

    Parameters
    ----------
    data: dict (mandatory)
        the log data structure.
    padding: list of str (optional, default None)
        the tree left paddings.
    level: int (optional, default -1)
        the tree level to be displayed, default all.
    display_content: bool (optional, default False)
        if true display the records values.
    current_level: int (optional, default 0)
        the current level in the dataset.
    """
    # Initialize the padding
    if padding is None:
        padding = [" "]

    # Go through the dataset structure
    for key, value in data.items():
        print("".join(padding) + "+-" + key)
        new_padding = padding + ["|", " "]
        if level != -1 and current_level == level:
            continue
        if isinstance(value, dict):
            tree(value,
                 padding=new_padding,
                 level=level,
                 display_content=display_content,
                 current_level=current_level + 1)
        elif display_content:
            print("".join(new_padding) + "+-" + repr(value))


def with_metaclass(mcls):
    """ Create a base class with a metaclass using a decorator.
    """
    def decorator(cls):
        body = vars(cls).copy()
        body.pop("__dict__", None)
        body.pop("__weakref__", None)
        return mcls(cls.__name__, cls.__bases__, body)
    return decorator
