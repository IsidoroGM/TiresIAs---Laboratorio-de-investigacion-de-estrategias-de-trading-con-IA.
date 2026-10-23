"""Sparse offline API-double replay of Python opens/closes; no JForex engine."""
import csv
from datetime import datetime
from pathlib import Path
import json
import io
import os
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'reports/phase6-jforex-strategy-2026-10-22'
link=json.loads((out/'reference-link.json').read_bytes())
reference=root/'.local/dukascopy-research'/link['id']
daily=json.loads((reference/'input-daily.json').read_bytes())
quotes=root/'.local/ev-data/jforex-sparse-quotes.csv'
def milliseconds(value):return int(datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()*1000)
with io.StringIO(newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['at','bid','ask'])
    for day in daily['sessions']:
        writer.writerow([milliseconds(day['first_observed_open_at']),day['bid']['open'],day['ask']['open']])
        writer.writerow([milliseconds(day['last_observed_close_at'])-1,day['bid']['close'],day['ask']['close']])
    last=daily['sessions'][-1]
    # A fixture marker, not an observed provider quote; proves no order after end.
    writer.writerow([milliseconds('2025-12-25T00:00:00.000Z'),last['bid']['close'],last['ask']['close']])
    raw=stream.getvalue().encode('utf-8')
if quotes.exists():assert quotes.read_bytes()==raw
else:quotes.write_bytes(raw)
java_root=Path('C:/Program Files/Eclipse Adoptium/jdk-25.0.2.10-hotspot/bin')
api=Path('C:/Program Files/JForex4/libs/demo/4.9.8/jforex-api-4.9.8.jar')
build=root/'.local/jforex/strategy-evidence-final-classes';build.mkdir(exist_ok=False)
compiled=subprocess.run([str(java_root/'javac.exe'),'--release','21','-encoding','UTF-8','-cp',str(api),'-d',str(build),
    str(root/'integrations/jforex/TiresiasSmaUtcTester.java'),str(root/'tests/jforex/JForexHarness.java')],cwd=root,capture_output=True,check=True)
(out/'javac-final.log').write_bytes(compiled.stdout+compiled.stderr)
values=subprocess.run([str(java_root/'java.exe'),'-cp',os.pathsep.join((str(build),str(api))),'JForexHarness','replay',
    str(root/'.local/jforex/sparse-offline-final-replay'),str(quotes),'20','60','2025-01-01','2025-12-25'],
    cwd=root,check=True,capture_output=True,timeout=60)
(out/'offline-replay-final.log').write_bytes(values.stdout+values.stderr)
assert not json.loads(values.stdout)['rejected']
print(values.stdout.decode().strip())
