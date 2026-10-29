"""Decode each selected JSON-stat cell and enforce the unchanged coverage gate."""
from itertools import product
from pathlib import Path
import csv,gzip,hashlib,json,math
from config import ROOT,COUNTRIES,YEARS,SECTORS

def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def table(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def cell(container,index,default=None):
    if isinstance(container,dict):return container.get(str(index),default)
    if isinstance(container,list):return container[index] if index<len(container) else default
    return default

def ingest(root=ROOT):
    manifest=json.loads((root/'data/source/manifest.json').read_text(encoding='utf-8'));assert manifest['status']=='COMPLETE'
    rows=[];lookup={};labels={}
    for response in manifest['responses']:
        blob=(root/response['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==response['stored_sha256']
        data=json.loads(gzip.decompress(blob));assert data['class']=='dataset'
        dimensions=[]
        for dim in data['id']:
            category=data['dimension'][dim]['category'];index=category['index']
            dimensions.append(sorted(index,key=index.get) if isinstance(index,dict) else index)
            labels.setdefault(dim,{}).update(category.get('label',{}))
        for i,keys in enumerate(product(*dimensions)):
            k=dict(zip(data['id'],keys));assert k['freq']=='A' and k['geo']==response['country'] and int(k['time']) in YEARS and k['nace_r2'] in ['C',*SECTORS]
            metric='energy' if response['dataset']=='env_ac_pefa04' else 'output'
            assert k.get('indic_pefa','NETDOM_EUSE')=='NETDOM_EUSE' and k.get('na_item','P1')=='P1'
            value=cell(data['value'],i);status=cell(data.get('status',{}),i,'')
            row={'country':k['geo'],'year':int(k['time']),'nace':k['nace_r2'],'metric':metric,'unit':k['unit'],
                 'value':value,'flag':status or '', 'dataset':response['dataset']}
            key=(row['country'],row['year'],row['nace'],metric,row['unit']);assert key not in lookup
            lookup[key]=row;rows.append(row)
    (root/'results').mkdir(exist_ok=True);table(root/'data/observations.csv',rows)
    panel=[];countries=[];reconciliation=[]
    for country in COUNTRIES:
        reasons=[];flags=set()
        for year in YEARS:
            for nace in ['C',*SECTORS]:
                values={}
                for metric,unit,field in [('energy','TJ','energy_tj'),('output','CP_MEUR','output_cp'),('output','PYP_MEUR','output_pyp'),('output','CLV_I15','volume_index')]:
                    r=lookup.get((country,year,nace,metric,unit));value=r['value'] if r else None;flag=r['flag'] if r else ''
                    flags.update(flag)
                    if field!='volume_index' and (value is None or not math.isfinite(value) or value<=0):reasons.append(f'{year}/{nace}/{field}:missing,nonfinite or nonpositive')
                    values[field]=value;values[field+'_flag']=flag
                panel.append({'country':country,'year':year,'nace':nace,'sector_label':labels['nace_r2'][nace],**values})
            for field,metric,unit in [('energy_tj','energy','TJ'),('output_cp','output','CP_MEUR'),('output_pyp','output','PYP_MEUR')]:
                parts=[lookup.get((country,year,s,metric,unit),{}).get('value') for s in SECTORS]
                aggregate=lookup.get((country,year,'C',metric,unit),{}).get('value')
                delta=math.fsum(parts)-aggregate if all(v is not None and math.isfinite(v) for v in parts) and aggregate is not None else None
                reconciliation.append({'country':country,'year':year,'measure':field,'sector_sum':math.fsum(parts) if all(v is not None for v in parts) else None,'published_c':aggregate,'difference':delta})
                if delta is None or abs(delta)>2:reasons.append(f'{year}/{field}:aggregate reconciliation outside2source units')
        if flags.intersection({'b','d'}):reasons.append('Published break/definition flag in the fixed panel')
        countries.append({'country':country,'eligible':not reasons,'reasons':sorted(set(reasons)),'source_flags':sorted(flags)})
    table(root/'data/panel.csv',panel);table(root/'results/source_reconciliation.csv',reconciliation)
    report={'status':'PASS_SOURCE_GATE' if sum(r['eligible'] for r in countries)>=4 else 'SOURCE_COVERAGE_HOLD',
            'responses':len(manifest['responses']),'observations':len(rows),'panel_rows':len(panel),'countries':countries,
            'eligible_countries':[r['country'] for r in countries if r['eligible']],
            'source_sha256':hashlib.sha256((root/'data/source/manifest.json').read_bytes()).hexdigest(),
            'scope':'All fixed countries/years/sectors retained;positive complete coverage and published aggregate reconciliation required;no decomposition or ranking performed.'}
    write(root/'results/source_accounting.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['countries']}),flush=True)
    print(json.dumps(countries),flush=True)
    assert report['status']=='PASS_SOURCE_GATE','Preserve the source hold;do not lower the fixed criteria.'

if __name__=='__main__':ingest()
