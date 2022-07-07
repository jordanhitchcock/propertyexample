from typing import List

from leases import GrossLease
from utils import memoized_series
from seriesgroup import SeriesGroup



class OfficeProperty(SeriesGroup):
    
    def __init__(self, name, sf: int, leases: List[GrossLease], cam_psf: float, insurance_psf: float,
                    utilities_psf: float, ret_psf: float, management_pct: float) -> None:
        super().__init__(name)
        self.sf = sf
        self.cam_psf = cam_psf
        self.insurance_psf = insurance_psf
        self.utilities_psf = utilities_psf
        self.ret_psf = ret_psf
        self.management_pct = management_pct
        self.add_series([SeriesGroup.with_series('leases', leases)], index=0)
    
    @memoized_series
    def egi(self, period):
        return sum([lease.effective_rent(period) for lease in self.leases])

    @memoized_series
    def cam(self, period):
        return self.sf * self.cam_psf
    
    @memoized_series
    def insurance(self, period):
        return self.sf * self.insurance_psf
    
    @memoized_series
    def utilities(self, period):
        occupied_sf = sum([lease.sf for lease in self.leases])
        return self.utilities_psf * occupied_sf
    
    @memoized_series
    def ret(self, period):
        return self.sf * self.ret_psf
    
    @memoized_series
    def management_fee(self, period):
        return self.egi(period) * self.management_pct
    
    @memoized_series
    def opex(self, period):
        expenses = self.cam(period) + self.insurance(period) + self.utilities(period) + \
            self.ret(period) + self.management_fee(period)
        return expenses
    
    @memoized_series
    def noi(self, period):
        return self.egi(period) - self.opex(period)



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
    
    in_place_leases = [GrossLease(**lease) for lease in occupied_suites]
    
    leasing_assumptions = [requests.get('https://leasingassumptions.herokuapp.com/marketleaserates', 
                                    params={'address': property_data['address'], 'floor': suite['floor']}).json() 
                       for suite in vacant_suites]
    
    speculative_leases = [GrossLease(name=suite['name'], sf=suite['sf'], **assumptions) 
                      for suite, assumptions in zip(vacant_suites, leasing_assumptions)]
    
    office = OfficeProperty(name=property_data['name'], 
                                sf=sum([l['sf'] for l in [*occupied_suites, *vacant_suites]]),
                                leases=SeriesGroup.with_series('leases', [*in_place_leases, *speculative_leases]),
                                **expenses)
    
    return office
