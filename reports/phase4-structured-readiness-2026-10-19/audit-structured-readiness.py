"""Auditoría puntual con verificadores existentes; no autoriza generación."""
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from trading_ai.idea_memory import capture_memory
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _canonical, _seal
from trading_ai.structured_draft_context import _claims
from trading_ai.structured_draft_request import verify_draft_request
from trading_ai.structured_review_memory import _capture_claims
from trading_ai import structured_ideas as ideas

root = Path(__file__).resolve().parent.parent
request_dir = root / '.local/structured-draft-requests/1646833181eb44c386eb32872f245afa'
context_dir = root / '.local/structured-draft-contexts/2d35c3461d234499a1c9300470f6f130'
memory_dir = root / '.local/structured-review-memory/ad12b5680d6a4cb3aab5fa7d6f0fec7a'

def prohibited(*args, **kwargs):
    raise AssertionError('Auditoría sin proveedor, red o cálculos.')

with patch('trading_ai.ai.create_provider', prohibited), patch('socket.socket.connect', prohibited), \
     patch('trading_ai.rules.RuleStrategy.generate_signals', prohibited):
    request = verify_draft_request(request_dir)
    reference = request['reference']
    frozen = Path(reference['frozen_dir'])
    old = lambda name: json.loads((context_dir / name).read_bytes())
    checks = {
        'legacy_memory_matches_current': _canonical(old('memory.json')) == _canonical(capture_memory(frozen)),
        'rules_memory_matches_current': _canonical(old('rules-memory.json')) == _canonical(ideas._rules_memory(reference, frozen)),
        'rule_claims_match_current': _canonical(old('claims.json')) == _canonical(_claims(reference)),
        'session_claims_match_current': _canonical(json.loads((memory_dir/'sessions.json').read_bytes())) == _canonical(_capture_claims(reference)),
    }
assert all(checks.values()), checks
unchanged = 0
for relative in ('phase4-research-session-2026-10-19/first-proposal', 'phase4-idea-memory-2026-10-19',
                 'phase4-structured-ideas-2026-10-19', 'phase4-structured-pipeline-2026-10-19',
                 'phase4-structured-revision-2026-10-19', 'phase4-structured-brief-2026-10-19',
                 'phase4-structured-draft-2026-10-19', 'phase4-structured-draft-context-2026-10-19',
                 'phase4-structured-review-memory-2026-10-19', 'phase4-structured-draft-request-2026-10-19'):
    directory = root / 'reports' / relative
    snapshot = json.loads((directory / 'snapshot.json').read_bytes())
    for name, item in snapshot['files'].items():
        assert sha256((directory / name).read_bytes()).hexdigest() == item['sha256']
        assert sha256(Path(item['source']).read_bytes()).hexdigest() == item['sha256']
        unchanged += 1
assert unchanged == 201
journal = RunJournal(root / '.local/structured-readiness-audits')
record = {'schema_version': 1, 'status': 'verified_not_authorized', 'executable': False,
          'request_dir': str(request_dir), 'request_sha256': request['request_sha256'],
          'freshness_at_audit_only': checks, 'archive_copies_and_originals_unchanged': unchanged,
          'submitted': False, 'generation_ready': False, 'provider_context_fit_verified': False,
          'remaining_gates': ['atomic freshness check at future reservation', 'provider token limits',
                              'explicit controlled generation reservation and provenance'],
          'new_usage': {'model_requests': 0, 'api_cost_usd': '0', 'backtests': 0},
          'audit_script_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
_seal(journal, 'audit.json', record, 'structured_readiness_audit_completed')
target = root / 'reports/phase4-structured-readiness-2026-10-19'
target.mkdir(exist_ok=False)
files = {}
for path in (*journal.directory.iterdir(), Path(__file__)):
    raw = path.read_bytes()
    name = path.name
    (target / name).write_bytes(raw)
    files[name] = {'source': str(path), 'sha256': sha256(raw).hexdigest()}
(target/'snapshot.json').write_text(json.dumps({'schema_version':1,'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'run':str(journal.directory),'checks':checks,'unchanged':unchanged},ensure_ascii=False))
