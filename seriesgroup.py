from typing import List
from utils import AbstractSeries, flatten_dict, get_hierarchy_attr


class SeriesGroupIterator:

    def __init__(self, series) -> None:
        self._series = series
        self._names_iter = iter(series.sub_series)
        self._sub_series_lenth = len(series.sub_series)

    def __next__(self):
        if len(self._series.sub_series) != self._sub_series_lenth:
            raise RuntimeError('Number of sub-series changed during iteration')
        try:
            name = next(self._names_iter)
            return getattr(self._series, name)
        except StopIteration:
            raise StopIteration


class SeriesGroup(AbstractSeries):

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.sub_series = get_hierarchy_attr(type(self), lambda name, value: isinstance(value, AbstractSeries))

    def __call__(self, *args, **kwds):
        series_values = {name: getattr(self, name)(*args, **kwds) for name in self.sub_series}
        return flatten_dict(series_values)

    def __iter__(self):
        return SeriesGroupIterator(self)

    def add_series(self, series: List, index: int = -1):
        for s in series:
            setattr(self, s.name, s)
            self.sub_series.insert(index, s.name)

    @classmethod
    def with_series(cls, name, series: List):
        new_series = cls(name)
        new_series.add_series(series)
        return new_series
