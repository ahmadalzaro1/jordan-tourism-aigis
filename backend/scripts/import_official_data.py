"""Normalize pinned MoTA publications without changing their geographic meaning."""
import argparse,json,re,hashlib
from urllib.request import Request,urlopen
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'data/official'
MONTHS={name.lower():i+1 for i,name in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}

DISPLAY_NAMES={"Jarash":"Jerash","Ajlun":"Ajloun","Um Qais":"Umm Qais","Um ALjmal":"Umm al-Jimal","um alrsas":"Umm ar-Rasas","Desrt Castle":"Desert castles","AL-Hlabat Castel":"Qasr Hallabat","Wade Rum":"Wadi Rum","AL- Shobaq":"Shobak","Ma''an Spa":"Ma’in Spa","Al Tafelieh":"Tafilah","Alzrqa":"Zarqa","Al-karak":"Karak"}

def number(value):
    return float(value) if pd.notna(value) else None

def download_sources():
    """Retrieve the pinned publications; never accept silently revised bytes."""
    for source in json.loads((DIR/'sources.json').read_text()):
        path=DIR/source['file']
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']:
            continue
        request=Request(source['url'],headers={'User-Agent':'Mozilla/5.0'})
        with urlopen(request,timeout=60) as response:
            content=response.read()
        if hashlib.sha256(content).hexdigest()!=source['sha256']:
            raise ValueError(f"Publication changed: {source['id']}; review the revision before importing")
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)


def require(condition, message):
    if not condition: raise ValueError(message)

def normalize():
    sources=json.loads((DIR/'sources.json').read_text())
    index={s['id']:s for s in sources if 'file' in s}
    for source in index.values():
        path=DIR/source['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError(f"Source hash mismatch: {source['id']}")
    national=[];annual=[];sites=[];site_monthly=[];regions=[];issues=[]
    for id in ['visitors_2019_04','visitors_2021_00','visitors_2023_02','visitors_2025_00']:
        source=index[id];path=DIR/source['file']
        require(hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256'],f'Source hash mismatch: {id}')
        excel=pd.ExcelFile(path)
        sheets=[(name,pd.read_excel(excel,sheet_name=name,header=None)) for name in excel.sheet_names]
        matches=[(name,df) for name,df in sheets if 'Tourist Overnight' in str(df.iloc[1,1])]
        require(len(matches)==1,f'{id}: ambiguous or stale workbook sheet')
        sheet,df=matches[0]
        for col in [2,5]:
            year=int(re.search(r'20\d{2}',str(df.iloc[3,col])).group())
            for i,row in df.iterrows():
                month=MONTHS.get(str(row.iloc[11]).strip().lower())
                if month:
                    values=[number(row.iloc[col+j]) for j in range(3)]
                    require(all(v is not None and v>=0 for v in values),f'{id}: invalid values in {year}-{month}')
                    require(abs(values[0]+values[1]-values[2])<0.01,f'{id}: national components do not reconcile')
                    national.append(dict(year=year,month=month,overnight_visitors=values[0],same_day_visitors=values[1],total_visitors=values[2],source_id=id,sheet=sheet,row=i+1,preliminary='*' in str(df.iloc[3,col])))
                elif str(row.iloc[11]).strip()=='Total':
                    annual.append(dict(year=year,overnight_visitors=number(row.iloc[col]),same_day_visitors=number(row.iloc[col+1]),total_visitors=number(row.iloc[col+2]),source_id=id,sheet=sheet,row=i+1))
    national.sort(key=lambda r:(r['year'],r['month']))
    require(len(national)==96 and len({(r['year'],r['month']) for r in national})==96,'Expected 96 unique national months')
    for r in annual:
        values=[x['total_visitors'] for x in national if x['year']==r['year']]
        require(abs(sum(values)-r['total_visitors'])<0.02,f"National annual mismatch: {r['year']}")
    source=index['sites_2025_00'];df=pd.read_excel(DIR/source['file'],header=None)
    for i,row in df.iloc[7:].iterrows():
        name=str(row.iloc[11]).strip()
        if not name or name=='nan':continue
        for year,col in [(2024,2),(2025,5)]:
            foreign,jordanian,total=[number(row.iloc[col+j]) for j in range(3)]
            if foreign+jordanian!=total:
                issues.append(dict(source_id=source["id"],site=name,year=year,issue="Reported total differs from components",reported_total=total,component_sum=foreign+jordanian,row=i+1))
            sites.append(dict(site=name,name_ar=str(row.iloc[1]).strip(),year=year,foreign_visits=foreign,jordanian_visits=jordanian,total_visits=total,source_id=source['id'],sheet='Sheet1',row=i+1,preliminary=year==2025))
    for id,source in index.items():
        if not id.startswith('sites_2025_') or id=='sites_2025_00':continue
        excel=pd.ExcelFile(DIR/source['file']);sheet=excel.sheet_names[0];df=pd.read_excel(excel,sheet_name=sheet,header=None)
        title=str(df.iloc[1,1]);match=re.search(r'Visitors to (.*?) by',title,re.I)
        site=match.group(1).strip() if match else title
        for i,row in df.iterrows():
            if len(row)<12:continue
            month=MONTHS.get(str(row.iloc[11]).strip().lower())
            if not month:continue
            for year,col in [(2024,2),(2025,5)]:
                foreign,jordanian,total=[number(row.iloc[col+j]) for j in range(3)]
                if total is None:continue
                if foreign+jordanian!=total:
                    issues.append(dict(source_id=id,site=site,year=year,month=month,issue="Reported total differs from components",reported_total=total,component_sum=foreign+jordanian,row=i+1))
                site_monthly.append(dict(site=site,year=year,month=month,foreign_visits=foreign,jordanian_visits=jordanian,total_visits=total,source_id=id,sheet=sheet,row=i+1))
    df=pd.read_excel(DIR/index['accommodation_2025_00']['file'],header=None)
    for i,row in df.iloc[4:18].iterrows():
        regions.append(dict(region=str(row.iloc[4]).strip(),name_ar=str(row.iloc[1]).strip(),year=2025,room_occupancy_pct=None if pd.isna(row.iloc[2]) else float(row.iloc[2])*100,bed_occupancy_pct=None if pd.isna(row.iloc[3]) else float(row.iloc[3])*100,source_id='accommodation_2025_00',sheet='Sheet1',row=i+1))
    df=pd.read_excel(DIR/index['accommodation_2025_08']['file'],header=None)
    accommodation=[dict(year=year,hotel_arrivals=float(df.iloc[5,col]),guest_nights=float(df.iloc[6,col]),occupied_room_nights=float(df.iloc[7,col]),source_id='accommodation_2025_08',sheet='Sheet1',rows=[6,7,8]) for year,col in [(2024,3),(2025,4)]]
    df=pd.read_excel(DIR/index['accommodation_2025_05']['file'],header=None)
    hotel_regions=[dict(region=str(df.iloc[3,col]).strip(),year=2025,guest_nights=float(df.iloc[17,col]),hotel_arrivals=float(df.iloc[18,col]),source_id='accommodation_2025_05',sheet='Recovered_Sheet1',column=col+1,rows=[18,19]) for col in range(2,19)]
    result=dict(schema_version=1,source_issues=issues,publisher='Jordan Ministry of Tourism and Antiquities',national_monthly=national,national_annual=annual,site_annual=sites,site_monthly=site_monthly,accommodation_annual=accommodation,occupancy_regions=regions,hotel_regions=hotel_regions,sources=sources,definitions={'national_arrivals':'Inbound overnight and same-day visitor trips, including nonresident Jordanians; not domestic tourism and not unique people. Underlying official estimates are preserved before display rounding.','site_visits':'Admissions/visits to each reported site; a person can visit multiple sites.','hotel_arrivals':'Guest check-ins at the covered tourist accommodation establishments; distinct from border arrivals.','regions':'MoTA reporting locations, not interchangeable with administrative governorates.','missing':'A blank published value remains null; no geographic allocation or missing-value imputation is performed.'})
    for key in ['site_annual','site_monthly','hotel_regions','occupancy_regions']:
        field='site' if key.startswith('site_') else 'region'
        for row in result[key]:row['display_name']=DISPLAY_NAMES.get(row[field],row[field])
    (DIR/'tourism.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('National months',len(national),'annual site rows',len(sites),'monthly site rows',len(site_monthly),'occupancy regions',len(regions))
    print('2025 arrivals',next(r for r in annual if r['year']==2025)['total_visitors'])
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true',help='Download pinned source files before normalization')
    args=parser.parse_args()
    if args.download: download_sources()
    normalize()
