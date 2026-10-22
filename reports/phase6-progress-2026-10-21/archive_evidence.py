"""Archivo de evidencias de este avance; no modifica fuentes ni datos históricos."""

from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET


DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[1]


def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def hashed(path): return sha256(path.read_bytes()).hexdigest()
def write(name, value):
    with (DIRECTORY/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


before = load(DIRECTORY/'source-before-verified-suite.json')
after = {name:hashed(ROOT/name) for name in before}
assert before == after, 'Las fuentes cambiaron durante la selección final.'
archive = DIRECTORY/'tested-source-bytes'
for name in before:
    source = (ROOT/name).resolve()
    assert source.is_relative_to(ROOT)
    target = archive/name
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(source.read_bytes())
    assert hashed(target) == before[name]


def nodes(path): return {line.strip() for line in path.read_text(encoding='utf-8-sig').splitlines() if line.startswith('tests/') and '::' in line}
old = nodes(ROOT/'reports/phase5-2-completion-2026-10-21/collection.log')
current = nodes(DIRECTORY/'collection.log')
assert len(old)==1673 and old.issubset(current) and len(current)==1802
new = current-old
assert len(new)==129 and all(name.startswith(('tests/test_tv_','tests/test_tradingview_cli.py::')) for name in new)
suite = ET.parse(DIRECTORY/'verified-suite.xml').getroot().find('testsuite')
assert suite is not None and suite.get('tests')=='396'
assert all(suite.get(key)=='0' for key in ('errors','failures','skipped'))
previous_audit = load(ROOT/'reports/phase5-2-completion-2026-10-21/read-only-check.json')['source_sha256']
audited = load(DIRECTORY/'read-only-audit.json')['source_sha256']
assert all(audited.get(name)==value and hashed(ROOT/name)==value for name,value in previous_audit.items())
check = load(DIRECTORY/'artificial-check-final-v2/evidence-manifest.json')
assert all(hashed(ROOT/name)==value for name,value in check['source_sha256'].items())
production = {name:(ROOT/'.local'/name).exists() for name in ('simulation/ledger.sqlite3','conversations/chat.sqlite3')}
assert not any(production.values()), 'El ensayo no debe crear almacenes de producción.'

summary = {
    'collected':1802,'previous_phase5_2_nodes_preserved':1673,'phase6_new_nodes':129,
    'selected_tests_passed':396,'selected_suite':'verified-suite.xml',
    'selected_duration_seconds':suite.get('time'),'source_bytes_stable':True,
    'source_sha256':before,'full_suite_executed':False,
    'full_suite_attempt':'interrupted_before_completion_no_full_result',
    'cache':'disabled','temporary_policy':'new_GUID_per_run',
    'previous_audit_files_preserved':len(previous_audit),'current_audit_files':len(audited),
    'production_stores_exist':production,
    'project_status_sha256':hashed(ROOT/'docs/PROJECT_STATUS.md'),
    'project_status_updated_in_phase6':False,'phase6_complete':False,
    'head':'47d2fc5158de4be2926ad683484d40eb2cee0984','commit_or_push_performed':False,
}
write('verification-manifest.json',summary)
write('diagnostic-summary.json',{
    'full_suite':'Attempt interrupted; partial output retained, no complete result.',
    'initial_artificial_check':'Wrong expected constant in harness; original script and diagnosis retained under artificial-check.',
    'intermediate_new_suite':{'tests_passed':123,'tests_failed':2,'original_terminal_output_archived':False,
        'diagnostics':['Depth test relied on Python recursion behaviour; explicit 64-level limit added.',
                       'Windows aborted an early rejected HTTP request with unread body; bounded body discard added.']},
    'final_affected_suite':'396 passed with stable source bytes; see verified-suite.xml.',
})
manifest = {
    'protocol':'tiresias_phase6_progress_evidence_v1','created_at':datetime.now(UTC).isoformat(),
    'phase_complete':False,'artificial_data':True,'pine_compiled':False,'external_connection':False,
    'real_model_requests':0,'real_account_orders':0,
    'report_sha256':hashed(ROOT/'reports/phase6-progress-2026-10-21.md'),
    'files_sha256':{path.relative_to(DIRECTORY).as_posix():hashed(path) for path in sorted(DIRECTORY.rglob('*')) if path.is_file() and path!=DIRECTORY/'evidence-manifest.json'},
}
write('evidence-manifest.json',manifest)
print(json.dumps({key:summary[key] for key in ('collected','previous_phase5_2_nodes_preserved','phase6_new_nodes','selected_tests_passed','source_bytes_stable','previous_audit_files_preserved','phase6_complete')},indent=2))
