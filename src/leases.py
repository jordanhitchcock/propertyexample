from typing import List
from .utils import memoized_series
from .seriesgroup import SeriesGroup



class GrossLease(SeriesGroup):
    
    def __init__(self, name: str, start: int, term: int, sf: int, rent_psf: float, free_periods: int, 
                 escalation_pct: float, escalation_freq: int) -> None:
        super().__init__(name)
        self.start = start
        self.term = term
        self.sf = sf
        self.rent_psf = rent_psf
        self.free_periods = free_periods
        self.escalation_pct = escalation_pct
        self.escalation_freq = escalation_freq
    
    @memoized_series
    def potential_rent(self, period):
        if self.start <= period <= (self.start + self.term):
            cum_escalations = (1 + self.escalation_pct) ** (period // self.escalation_freq)
            return self.sf * self.rent_psf * cum_escalations
        return 0
    
    @memoized_series
    def free_rent(self, period):
        return -self.potential_rent(period) if (period < self.free_periods) else 0
    
    @memoized_series
    def effective_rent(self, period):
        return self.potential_rent(period) + self.free_rent(period)


class NetLease(SeriesGroup):
    
    def __init__(self, name: str, start: int, term: int, sf: int, rent_psf: float, free_periods: int, 
                 escalation_pct: float, escalation_freq: int, reimb_pct: float, recoveries: List[str]) -> None:
        super().__init__(name)
        self.start = start
        self.term = term
        self.sf = sf
        self.rent_psf = rent_psf
        self.free_periods = free_periods
        self.escalation_pct = escalation_pct
        self.escalation_freq = escalation_freq
        self.reimb_pct = reimb_pct
        self.recoveries = recoveries
    
    @memoized_series
    def potential_rent(self, period):
        if self.start <= period <= (self.start + self.term):
            cum_escalations = (1 + self.escalation_pct) ** (period // self.escalation_freq)
            return self.sf * self.rent_psf * cum_escalations
        return 0
    
    @memoized_series
    def free_rent(self, period):
        return -self.potential_rent(period) if (period < self.free_periods) else 0
    
    @memoized_series
    def reimbursements(self, period):
        expense_amounts = [series(period) for series in self.series(lambda s: s.name in self.recoveries)]
        return sum(expense_amounts) * self.reimb_pct
    
    @memoized_series
    def effective_rent(self, period):
        return self.potential_rent(period) + self.free_rent(period) + self.reimbursements(period)
