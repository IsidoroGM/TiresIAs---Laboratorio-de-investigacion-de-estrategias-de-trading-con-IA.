"""Download the official installer only; never start it or accept a license."""
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

root=Path(__file__).resolve().parents[2]
target=root/'.local/jforex/downloads/JForex4_windows-x64.exe'
url='https://platform.dukascopy.com/jforex4-installer/JForex4_windows-x64.exe'
maximum=512*1024*1024

def allowed(value):
    parsed=urlparse(value)
    if parsed.scheme!='https' or parsed.hostname not in ('platform.dukascopy.com','www.dukascopy.com'):
        raise ValueError('Unexpected installer origin or transport')

class Redirects(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        allowed(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

target.parent.mkdir(parents=True,exist_ok=True)
if target.exists():raise FileExistsError('Installer already present; inspect rather than overwrite')
partial=target.with_suffix('.exe.part')
opener=build_opener(Redirects())
with opener.open(Request(url,headers={'User-Agent':'TiresIAs-local-setup/1'}),timeout=30) as response:
    allowed(response.url)
    length=int(response.headers.get('Content-Length','0'))
    if length>maximum:raise ValueError('Installer exceeds the download bound')
    count=0;digest=sha256()
    with partial.open('xb') as stream:
        while chunk:=response.read(1024*1024):
            count+=len(chunk)
            if count>maximum:raise ValueError('Installer exceeds the download bound')
            stream.write(chunk);digest.update(chunk)
    if length and count!=length:raise ValueError('Incomplete download')
    with partial.open('rb') as stream:
        if stream.read(2)!=b'MZ':raise ValueError('Not a Windows executable')
    final_url=response.url
partial.rename(target)
metadata={'url':url,'final_url':final_url,'bytes':count,'sha256':digest.hexdigest(),
    'installer_executed':False,'account_created':False,'terms_accepted':False}
target.with_suffix('.download.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata))
