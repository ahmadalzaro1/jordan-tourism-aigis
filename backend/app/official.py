"""Pinned official observations; no national-to-governorate allocation."""
import json
from functools import lru_cache
from app.paths import DATA_DIR
from app.config import get_settings

def official_mode():
    return get_settings().data_mode == 'official'

@lru_cache()
def official_data():
    return json.loads((DATA_DIR/'official/tourism.json').read_text())

def overview(year):
    data=official_data()
    annual=next((r for r in data['national_annual'] if r['year']==year),None)
    accommodation=next((r for r in data['accommodation_annual'] if r['year']==year),None)
    occupancy=next((r for r in data['occupancy_regions'] if r['year']==year and r['region']=='Grand Total'),None)
    return dict(data_mode='official',year=year,national=annual,monthly=[r for r in data['national_monthly'] if r['year']==year],accommodation=accommodation,occupancy=occupancy,sites=[r for r in data['site_annual'] if r['year']==year],site_monthly=[r for r in data['site_monthly'] if r['year']==year],hotel_regions=[r for r in data['hotel_regions'] if r['year']==year and r['region']!='Total'],occupancy_regions=[r for r in data['occupancy_regions'] if r['year']==year and r['region']!='Grand Total'],sources=data['sources'],source_issues=[r for r in data['source_issues'] if r['year']==year],definitions=data['definitions'])
