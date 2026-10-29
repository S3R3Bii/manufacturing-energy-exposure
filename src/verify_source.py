"""Separate mixed-radix decoder and SQLite reconciliation of every source cell."""
from pathlib import Path
from decimal import Decimal
import csv,gzip,hashlib,json,math,sqlite3
ROOT=Path(__file__).resolve().parents[1]
SECTORS=['C10-C12','C13-C15','C16','C17','C18','C19','C20','C21','C22','C23','C24','C25','C26','C27','C28','C29','C30','C31_C32','C33']

def close(a,b):assert math.isclose(float(a),float(b),abs_tol=1e-7,rel_tol=1e-9),(a,b)
def verify(root=ROOT):
    manifest=json.loads((root/'data/source/manifest.json').read_text(encoding='utf-8'));assert manifest['status']=='COMPLETE' and len(manifest['responses'])==12
    con=sqlite3.connect(':memory:');con.execute('CREATE TABLE source(country TEXT,year INTEGER,nace TEXT,metric TEXT,unit TEXT,value REAL,flag TEXT,PRIMARY KEY(country,year,nace,metric,unit))')
    expected={}
    for r in manifest['responses']:
        blob=(root/r['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==r['stored_sha256']
        raw=gzip.decompress(blob);assert hashlib.sha256(raw).hexdigest()==r['response_sha256']
        d=json.loads(raw,parse_float=Decimal);assert d['class']=='dataset' and d['id']==r['id'] and d['size']==r['size']
        categories=[]
        for name in d['id']:
            ids=d['dimension'][name]['category']['index'];categories.append({v:k for k,v in ids.items()} if isinstance(ids,dict) else dict(enumerate(ids)))
        for n in range(math.prod(d['size'])):
            remain=n;keys={}
            for name,size,cat in reversed(list(zip(d['id'],d['size'],categories))):keys[name]=cat[remain%size];remain//=size
            assert remain==0 and keys['freq']=='A' and keys['geo']==r['country'] and 2015<=int(keys['time'])<=2023 and keys['nace_r2'] in ['C',*SECTORS]
            metric='energy' if r['dataset']=='env_ac_pefa04' else 'output'
            assert keys.get('indic_pefa','NETDOM_EUSE')=='NETDOM_EUSE' and keys.get('na_item','P1')=='P1'
            values=d['value'];v=values.get(str(n)) if isinstance(values,dict) else values[n]
            statuses=d.get('status',{});flag=(statuses.get(str(n),'') if isinstance(statuses,dict) else statuses[n]) or ''
            key=(keys['geo'],int(keys['time']),keys['nace_r2'],metric,keys['unit']);assert key not in expected
            expected[key]=(v,flag);con.execute('INSERT INTO source VALUES(?,?,?,?,?,?,?)',(*key,None if v is None else float(v),flag))
    with (root/'data/observations.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==len(expected)==4320
    seen=set()
    for r in rows:
        key=(r['country'],int(r['year']),r['nace'],r['metric'],r['unit']);assert key not in seen;seen.add(key)
        value,flag=expected[key];assert r['flag']==flag
        if value is None:assert r['value']==''
        else:close(Decimal(r['value']),value)
    with (root/'data/panel.csv').open(encoding='utf-8',newline='') as f:panel=list(csv.DictReader(f))
    assert len(panel)==1080
    for r in panel:
        for field,metric,unit in [('energy_tj','energy','TJ'),('output_cp','output','CP_MEUR'),('output_pyp','output','PYP_MEUR'),('volume_index','output','CLV_I15')]:
            value,flag=expected.get((r['country'],int(r['year']),r['nace'],metric,unit),(None,''));assert r[field+'_flag']==flag
            if value is None:assert r[field]==''
            else:close(r[field],value)
    eligibility={};coverage=[]
    for country in ['BE','DE','ES','FR','IT','NL']:
        missing=con.execute("SELECT count(*) FROM source WHERE country=? AND unit!='CLV_I15' AND (value IS NULL OR value<=0)",(country,)).fetchone()[0]
        flags={flag for flag, in con.execute('SELECT DISTINCT flag FROM source WHERE country=?',(country,))}
        broken=any('b' in flag or 'd' in flag for flag in flags)
        deltas=[]
        for year in range(2015,2024):
            for metric,unit in [('energy','TJ'),('output','CP_MEUR'),('output','PYP_MEUR')]:
                count,total=con.execute("SELECT count(value),sum(value) FROM source WHERE country=? AND year=? AND metric=? AND unit=? AND nace!='C'",(country,year,metric,unit)).fetchone()
                aggregate=con.execute("SELECT value FROM source WHERE country=? AND year=? AND metric=? AND unit=? AND nace='C'",(country,year,metric,unit)).fetchone()
                deltas.append(total-aggregate[0] if count==19 and aggregate and aggregate[0] is not None else None)
        okay=missing==0 and not broken and all(delta is not None and abs(delta)<=2 for delta in deltas)
        eligibility[country]=okay;coverage.append({'country':country,'missing_or_nonpositive_required_cells':missing,'break_or_definition_flag':broken,'eligible':okay,
            'max_defined_aggregate_difference':max(abs(x) for x in deltas if x is not None) if any(x is not None for x in deltas) else None})
    source=json.loads((root/'results/source_accounting.json').read_text(encoding='utf-8'))
    assert eligibility=={r['country']:r['eligible'] for r in source['countries']}
    assert source['eligible_countries']==[c for c in ['BE','DE','ES','FR','IT','NL'] if eligibility[c]]
    assert len(source['eligible_countries'])>=4 and source['status']=='PASS_SOURCE_GATE'
    report={'status':'PASS','responses_hashed':12,'all_cells_reconstructed':4320,'panel_rows_joined':1080,'country_source_checks':coverage,
        'scope':'Every API dimension/key/value/missing cell/flag,unique grain,normalized panel and SQL eligibility/aggregate check. No primary ingestion helper imported.',
        'absolute_tolerance':1e-7,'relative_tolerance':1e-9}
    (root/'results/INDEPENDENT_SOURCE_CHECK.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':verify()
