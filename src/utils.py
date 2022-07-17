from collections.abc import MutableMapping
from functools import cache
from types import MethodType


class AbstractSeries:
    pass


class memoized_series(AbstractSeries):
    
    def __init__(self, func) -> None:
        super().__init__()
        self.func = func
    
    def __set_name__(self, owner, name) -> None:
        self.name = name
        self.func.name = name
    
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


def get_all_attrs_w_filter(obj, filter):
    """Get all attribute names from instance to top level base class in method resolution order."""
    attrs = {}

    # instance attributes
    if hasattr(obj, '__dict__'):
        for name, value in obj.__dict__.items():
            if filter(name, value):
                attrs[name] = getattr(obj, name)
    if hasattr(obj, '__slots__'):
        for name in obj.__slots__:
            attr = getattr(obj, name)
            if filter(name, attr):
                attrs[name] = attr
    
    # type attributes
    bases = type(obj).__mro__
    
    for base in bases:
        for name, attr in base.__dict__.items():
            if filter(name, attr) and (name not in attrs):
                attrs[name] = getattr(obj, name)
    
    return attrs
