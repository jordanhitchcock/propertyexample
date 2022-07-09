from typing import List
from .utils import AbstractSeries, flatten_dict, get_all_attrs


class SeriesGroupIterator:
    
    def __init__(self, series_group) -> None:
        self._series = iter(series_group.get_series().values())
    
    def __next__(self):
        try:
            return next(self._series)
        except StopIteration:
            raise StopIteration


class SeriesGroup(AbstractSeries):
    
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name
    
    def __call__(self, *args, **kwargs):
        series = self.get_series()
        series_values = {name: s(*args, **kwargs) for name, s in series.items()}
        return flatten_dict(series_values)
    
    def __iter__(self):
        return SeriesGroupIterator(self)
    
    def get_series(self):
        attrs = {name: getattr(self, name) for name in get_all_attrs(self)}
        series = {name: attr for name, attr in attrs.items() if isinstance(attr, AbstractSeries) or (isinstance(getattr(type(self), name, None), AbstractSeries))}
        return series
    
    @classmethod
    def with_series(cls, name, series: List):
        new_group = cls(name)
        for s in series:
            setattr(new_group, s.name, s)
        return new_group
