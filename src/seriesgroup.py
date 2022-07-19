from __future__ import annotations
from typing import Any, Callable, Dict, List

from .utils import AbstractSeries, flatten_dict, get_all_attrs_w_filter


def is_child_series(name, attr):
    if name == 'parent':
        return False
    return isinstance(attr, AbstractSeries)


class SeriesGroup(AbstractSeries):
    
    def __init__(self, name: str, parent: SeriesGroup=None) -> None:
        super().__init__()
        self.name = name
        self.parent = parent
    
    @classmethod
    def with_children(cls, name: str, children: Dict[str, SeriesGroup]) -> SeriesGroup:
        new_sg = cls(name)
        for name, sg in children.items():
            setattr(new_sg, name, sg)
        return new_sg
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        """If setting a SeriesGroup as an attribute, set the attribute's `parent` property to self"""
        if isinstance(__value, SeriesGroup):
            super(SeriesGroup, __value).__setattr__('parent', self)
        return super().__setattr__(__name, __value)
    
    def __delattr__(self, __name: str) -> None:
        """If removing a SeriesGroup attribute, set the `parent` property to None"""
        attr = getattr(self, __name)
        if isinstance(attr, SeriesGroup):
            attr.parent = None
        return super().__delattr__(__name)
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        series_values = {series.name: series(*args, **kwds) for series in self._series()}
        return flatten_dict(series_values)
    
    def _series(self) -> List[SeriesGroup]:
        """Get all AbstractBase attributes for self and class"""
        return get_all_attrs_w_filter(self, is_child_series)
    
    def root(self) -> SeriesGroup:
        """Return tree root node"""
        return self.parent.root() if self.parent is not None else self
    
    def series(self, function: Callable | None = None) -> List[SeriesGroup]:
        """
        Return series in the tree where the test function returns `True` or all tree series if function is None
        The test function should take a single AbstractSeries parameter and return a bool
        """
        return self.root().child_series(function=function)
    
    def child_series(self, function: Callable | None = None) -> List[SeriesGroup]:
        """
        Return children series where the test function returns `True` or all children series if function is None
        The test function should take a single AbstractSeries parameter and return a bool
        """
        series = []
        
        children = self._series()
        
        for child in children:
            # If there's a test condition, add child if it passes the test regardless of whether its a SG or memoized_series
            # If SG, propogate call to children as well
            if function is not None:
                if function(child):
                    series.append(child)
                
                if isinstance(child, SeriesGroup):
                    series.extend(child.child_series(function=function))
            
            # If no test condition, then then propogate call if SG otherwise add to series
            else:
                if isinstance(child, SeriesGroup):
                    series.extend(child.child_series(function=function))
                else:
                    series.append(child)
        
        return series
