"""Append the UI access outcome to this still-open increment, preserving all priors."""
from hashlib import sha256
import json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
out=root/'reports/phase6-jforex-strategy-2026-10-22'
manifest_path=out/'manifest.json'
manifest=json.loads(manifest_path.read_bytes())
def digest(path):return sha256(path.read_bytes()).hexdigest()
for name,expected in manifest['evidence_sha256'].items():assert digest(out/name)==expected
status={'jforex_installation_and_running_window_discovered':True,'tool':'Windows Computer Use',
    'operation':'get_window_state','result':'Computer Use app approval timed out','window_access_granted':False,
    'app_input_actions_sent':0,'authentication_dialogs_automated':False,'credential_files_read':False,
    'passwords_or_keys_requested':False,'window_title_copied_to_report':False,'screenshots_copied_to_report':False,
    'native_jforex_compilation_verified':False,'native_jforex_tester_run':False,
    'user_preference_question_pending':'retry application access or use the prepared package manually'}
path=out/'ui-access.json';assert not path.exists()
path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=out/'README.md'
with readme.open('a',encoding='utf-8') as stream:
    stream.write('\nTras la auditoría se intenta inspeccionar la ventana de JForex mediante Windows\n'
        'Computer Use. La herramienta devuelve «Computer Use app approval timed out».\n'
        'No se obtiene captura ni se envía ninguna entrada a la aplicación. El nombre\n'
        'de la ventana no se copia a este informe. Se solicita al usuario elegir entre\n'
        'reintentar el permiso de acceso o seguir las instrucciones manualmente.\n'
        'Esto no es una compilación nativa fallida ni un rechazo de la estrategia.\n')
(out/'tested-source/record-ui-access.py').write_bytes(Path(__file__).read_bytes())
manifest['ui_access_outcome']='app_approval_timed_out'
manifest['evidence_sha256']={p.relative_to(out).as_posix():digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=manifest_path}
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,expected in manifest['evidence_sha256'].items():assert digest(out/name)==expected
print(json.dumps({'ui_access_outcome':manifest['ui_access_outcome'],'app_inputs':0,'tests_passed':manifest['tests_passed'],
    'evidence_files':len(manifest['evidence_sha256']),'manifest_sha256':digest(manifest_path)}))
