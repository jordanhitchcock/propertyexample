from functools import cache
from types import MethodType
from typing import MutableMapping


class AbstractSeries:
    """Base class for memoize and Component that makes it easier to find ojbjects"""
    pass


class memoized_series(AbstractSeries):

    def __init__(self, func) -> None:
        super().__init__()
        self.func = func

    def __set_name__(self, owner, name) -> None:
        self.name = name

    def __get__(self, instance=None, cls=None):
        """
        Return the encapsulated function wrapped with a cache and bound to the instance.
        If `instance` is `None`, return self.
        """
        if instance is None:
            return self

        bound_func = MethodType(cache(self.func), instance)
        setattr(instance, self.name, bound_func)
        return bound_func


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    return dict(_flatten_dict_gen(d, parent_key, sep))


def get_all_attrs(obj):
    """Get all attribute names from instance to top level base class in method resolution order."""
    attr_names = []
    
    # instance attributes
    if hasattr(obj, '__dict__'):
        attr_names.extend(obj.__dict__.keys())
    if hasattr(obj, '__slots__'):
        attr_names.extend(obj.__slots__)

    # type attributes
    bases = type(obj).__mro__
    
    for base in bases:
        for attr in vars(base):
            if attr not in attr_names:
                attr_names.append(attr)
    
    return attr_names
