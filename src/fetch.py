"""Twelve sequential official requests, or exact offline snapshot verification."""
from datetime import datetime,timezone
from pathlib import Path
import gzip,hashlib,json,subprocess,sys,tempfile,urllib.parse,urllib.request
from config import ROOT,COUNTRIES,SECTORS

def sha(blob):return hashlib.sha256(blob).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def fetch():
    folder=ROOT/'data/source';folder.mkdir(parents=True,exist_ok=True);manifest=folder/'manifest.json'
    if manifest.exists():
        data=json.loads(manifest.read_text(encoding='utf-8'))
        assert data['status']=='COMPLETE','Retain an incomplete acquisition and investigate; do not overwrite it.'
        for r in data['responses']:
            blob=(ROOT/r['file']).read_bytes();assert sha(blob)==r['stored_sha256']
            assert sha(gzip.decompress(blob))==r['response_sha256']
        assert len(data['responses'])==12
        print('Verified twelve exact Eurostat responses; offline, no source refresh.');return
    record={'status':'ACQUIRING','started_utc':datetime.now(timezone.utc).isoformat(),
        'source':'Eurostat official aggregate statistical API;see DATA_RIGHTS.md','responses':[],
        'analysis_performed':False,'historical_vintages':'Unavailable;current revised snapshots only'}
    for country in COUNTRIES:
        for dataset in ['env_ac_pefa04','nama_10_a64']:
            params=[('lang','en'),('freq','A'),('geo',country),('sinceTimePeriod','2015'),('untilTimePeriod','2023')]
            params += [('nace_r2',s) for s in ['C',*SECTORS]]
            params += [('indic_pefa','NETDOM_EUSE'),('unit','TJ')] if dataset=='env_ac_pefa04' else [('na_item','P1'),('unit','CP_MEUR'),('unit','PYP_MEUR'),('unit','CLV_I15')]
            url='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'+dataset+'?'+urllib.parse.urlencode(params)
            try:
                if sys.platform=='win32':
                    # Windows' native TLS trust store works for the source's
                    # chain; neither the client nor server validation is bypassed.
                    with tempfile.TemporaryDirectory(prefix='eurostat-') as temporary:
                        target=Path(temporary)/'response.json'
                        subprocess.run(['powershell','-NoProfile','-NonInteractive','-File',str(ROOT/'src/download.ps1'),'-Uri',url,'-OutFile',str(target)],check=True,capture_output=True)
                        blob=target.read_bytes()
                else:
                    request=urllib.request.Request(url,headers={'User-Agent':'ManufacturingEnergyResearch/0.1 (https://github.com/S3R3Bii/manufacturing-energy-exposure)'})
                    with urllib.request.urlopen(request,timeout=45) as response:blob=response.read()
                decoded=json.loads(blob);assert decoded.get('class')=='dataset' and 'error' not in decoded
                filename=f'data/source/{country}-{dataset}.json.gz';stored=gzip.compress(blob,mtime=0);(ROOT/filename).write_bytes(stored)
                record['responses'].append({'country':country,'dataset':dataset,'url':url,'file':filename,
                    'retrieved_utc':datetime.now(timezone.utc).isoformat(),'updated':decoded.get('updated'),
                    'response_sha256':sha(blob),'stored_sha256':sha(stored),'id':decoded['id'],'size':decoded['size']})
                write(manifest,record);print(country,dataset,'retained;no outcome analysis',flush=True)
            except Exception as error:
                record.update(status='SOURCE_ACQUISITION_HOLD',failed_request=url,error=type(error).__name__+': '+str(error));write(manifest,record);raise
    record.update(status='COMPLETE',completed_utc=datetime.now(timezone.utc).isoformat());write(manifest,record)

if __name__=='__main__':fetch()
