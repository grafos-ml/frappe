#! -*- encoding: utf-8 -*-
"""
Util contrib for the system
"""

__author__ = "joaonrb"

import sys
if sys.version_info >= (3, 0):
    basestring = unicode = str


def initialize(cls):
    """
    Return a tuple with the class, a tuple with args and a dict with keyword args.

    >>> cls, atr, kwatr = initialize("random.random")
    >>> n = cls(*atr, **kwatr)
    >>> print(type(n))
    <type 'float'>
    >>> print(0. <= n <= 1.)
    True

    >>> cls, atr, kwatr = initialize(("random.randint", (0, 10), {}))
    >>> n = cls(*atr, **kwatr)
    >>> print(type(n))
    <type 'int'>
    >>> print(0 <= n <= 10)
    True

    >>> cls, atr, kwatr = initialize(object())
    Traceback (most recent call last):
    ...
    AttributeError: Attribute must be string or tuple with the first element string.

    >>> cls, atr, kwatr = initialize(("random", object()))
    Traceback (most recent call last):
    ...
    AttributeError: The second element in tuple must be list, tuple or dict with python native structs.

    >>> cls, atr, kwatr = initialize(("random", object(), object()))
    Traceback (most recent call last):
    ...
    AttributeError: The second element in tuple must be list or and the third must be dict.

    >>> cls, atr, kwatr = initialize(("random", object(), object(), object()))
    Traceback (most recent call last):
    ...
    AttributeError: Tuple must be size 2 or 3.

    :param cls:
    :return:
    """
    if isinstance(cls, basestring):
        cls_str, args, kwargs = cls, (), {}
    elif isinstance(cls, (tuple, list)) and isinstance(cls[0], basestring):
        if len(cls) == 2:
            if isinstance(cls[1], (tuple, list)):
                cls_str, args, kwargs = cls[0], cls[1], {}
            elif isinstance(cls[1], dict):
                cls_str, args, kwargs = cls[0], (), cls[1]
            else:
                raise AttributeError("The second element in tuple must be list, tuple or dict with python native "
                                     "structs.")
        elif len(cls) == 3:
            if isinstance(cls[1], (tuple, list)) and isinstance(cls[2], dict):
                cls_str, args, kwargs = cls
            else:
                raise AttributeError("The second element in tuple must be list or and the third must be dict.")
        else:
            raise AttributeError("Tuple must be size 2 or 3.")
    else:
        raise AttributeError("Attribute must be string or tuple with the first element string.")
    parts = cls_str.split(".")
    module, cls = ".".join(parts[:-1]), parts[-1]
    return getattr(__import__(module, fromlist=[""]), cls), args, kwargs