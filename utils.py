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


def get_hierarchy_attr(cls, filter=None):
    """
    Get all attributes for the current class and any parents, based on method resolution order (MRO).
    Filter should be a function that takes a `attr_name: str, attr_value: obj` and returns a bool.
    """
    bases = cls.__mro__
    if bases:
        bases = list(bases)
        bases.reverse()

    attributes = []

    if filter:
        for base in bases:
            for name, attr in vars(base).items():
                if (name not in attributes) and filter(name, attr):
                    attributes.append(name)
    else:
        for base in bases:
            for name, attr in vars(base).items():
                if (name not in attributes):
                    attributes.append(name)
    return attributes
