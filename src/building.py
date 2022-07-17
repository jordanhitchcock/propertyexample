from typing import Dict

from .leases import GrossLease
from .utils import memoized_series
from .seriesgroup import SeriesGroup



class OfficeBuilding(SeriesGroup):
    
    def __init__(self, name, sf: int, leases: Dict[str, SeriesGroup], cam_psf: float, insurance_psf: float,
                    utilities_psf: float, ret_psf: float, management_pct: float) -> None:
        super().__init__(name)
        self.sf = sf
        self.cam_psf = cam_psf
        self.insurance_psf = insurance_psf
        self.utilities_psf = utilities_psf
        self.ret_psf = ret_psf
        self.management_pct = management_pct
        self.leases = SeriesGroup.with_children('leases', leases)
    
    @memoized_series
    def total_effective_rent(self, period):
        return sum([effective_rent(period) for effective_rent in self.series(lambda s: s.name == 'effective_rent')])

    @memoized_series
    def cam(self, period):
        return self.sf * self.cam_psf
    
    @memoized_series
    def insurance(self, period):
        return self.sf * self.insurance_psf
    
    @memoized_series
    def utilities(self, period):
        occupied_sf = sum([lease.sf for lease in self.leases.child_series(lambda s: isinstance(s, SeriesGroup))])
        return self.utilities_psf * occupied_sf
    
    @memoized_series
    def ret(self, period):
        return self.sf * self.ret_psf
    
    @memoized_series
    def management_fee(self, period):
        return self.total_effective_rent(period) * self.management_pct
    
    @memoized_series
    def opex(self, period):
        expenses = self.cam(period) + self.insurance(period) + self.utilities(period) + \
            self.ret(period) + self.management_fee(period)
        return expenses
    
    @memoized_series
    def noi(self, period):
        return self.total_effective_rent(period) - self.opex(period)



import requests
import sqlite3


def build_office(building_name):
    
    with sqlite3.connect('properties_database.db') as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        property_data = dict(cur.execute('select * from properties where name like (?)', (building_name,)).fetchone())

        expenses = dict(cur.execute('select cam_psf, insurance_psf, utilities_psf, ret_psf, \
                                    management_pct from expenses where property_id = (?)', (property_data['id'],))
                                .fetchone())
        occupied_suites = [dict(suite) for suite in cur.execute('select sf, tenant_name as name, start, term, rent_psf, \
                                                                free_periods, escalation_pct, escalation_freq from spaces \
                                                                left join leases on spaces.id = leases.suite_id \
                                                                where property_id = (?) and tenant_name is not null', 
                                                                (property_data['id'],))]
        vacant_suites = [dict(suite) for suite in cur.execute('select suite as name, sf, floor from spaces \
                                                            left join leases on spaces.id = leases.suite_id \
                                                            where spaces.property_id = (?) and tenant_name is null', 
                                                            (property_data['id'],))]
    
    in_place_leases = {lease['name']: GrossLease(**lease) for lease in occupied_suites}
    
    leasing_assumptions = [requests.get('https://leasingassumptions.herokuapp.com/marketleaserates', 
                                        params={'address': property_data['address'], 'floor': suite['floor']}).json() 
                        for suite in vacant_suites]

    speculative_leases = {suite['name']: GrossLease(name=suite['name'], sf=suite['sf'], **assumptions) 
                        for suite, assumptions in zip(vacant_suites, leasing_assumptions)}
    
    office = OfficeBuilding(name=property_data['name'], 
                            sf=sum([l['sf'] for l in [*occupied_suites, *vacant_suites]]),
                            leases=dict(in_place_leases, **speculative_leases),
                            **expenses)
    
    return office
