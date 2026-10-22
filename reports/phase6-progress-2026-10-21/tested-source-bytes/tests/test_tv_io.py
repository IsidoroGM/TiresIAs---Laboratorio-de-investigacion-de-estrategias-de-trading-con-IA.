"""Importaciones explícitas, originales conservados y reanudación sin contabilizar dos veces."""

from copy import deepcopy
from hashlib import sha256

import pytest

from trading_ai.tv_contracts import checksum, make_contract
from trading_ai.tv_io import BundleRepository, import_csv, parse_numeric, preview_csv, validate_mapping
from trading_ai.tv_simulation import SimulationLedger


@pytest.fixture
def inputs(tmp_path):
    contract=make_contract(fast=2,slow=3,ticker='SYNTH:EURUSD',start='2020-01-01T00:00:00Z',end='2021-01-01T00:00:00Z',capital='100',cost_rate='0.01')
    mapping={'protocol':'tiresias_execution_csv_mapping_v1','columns':{
        'execution_id':'id','sequence':'seq','side':'acción','quantity':'cantidad','price':'precio','fee':'coste',
        'signal_at':'señal','executed_at':'ejecución'},'delimiter':';','decimal_separator':',','grouping_separator':'.',
        'sides':{'Entrada larga':'buy','Salida larga':'sell'},'time_format':'iso8601','sequence_mode':'column','source_is_simulated':True}
    raw=('id;seq;acción;cantidad;precio;coste;señal;ejecución\n'
         'buy-1;1;Entrada larga;1;10,00;0,10;2020-01-01T23:00:00Z;2020-01-02T00:00:00Z\n'
         'sell-1;2;Salida larga;1;12,00;0,12;2020-01-02T23:00:00Z;2020-01-03T00:00:00Z\n').encode('utf-8-sig')
    ledger=SimulationLedger(tmp_path);ledger.register(contract)
    return contract,mapping,raw,ledger


def test_preview_preserves_exact_numeric_meaning_and_has_no_side_effect(inputs,tmp_path):
    contract,mapping,raw,ledger=inputs
    before=list(tmp_path.rglob('*'))
    preview=preview_csv(raw,mapping,contract)
    assert not preview['errors'] and preview['rows'][0]['event']['price']=='10'
    assert preview['raw_sha256']==sha256(raw).hexdigest()
    assert preview['external_format_verified'] is False
    assert before==list(tmp_path.rglob('*'))
    assert ledger.account(checksum(contract))['state']['cash']=='100'


def test_import_is_durable_idempotent_and_separate_from_processing(inputs,tmp_path):
    contract,mapping,raw,ledger=inputs
    preview=preview_csv(raw,mapping,contract)
    result=import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))
    assert result['rows']==2 and result['status']=='stored_in_inbox_not_processed'
    original=tmp_path/'.local'/'tradingview-imports'/result['id']/'original.csv'
    assert original.read_bytes()==raw
    assert ledger.account(checksum(contract))['state']['cash']=='100'
    assert import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))==result
    assert len(ledger.overview()['receipts'])==2
    ledger.process(checksum(contract))
    assert ledger.account(checksum(contract))['state']['cash']=='101.78'
    import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))
    assert ledger.process(checksum(contract))['applied']==[]


def test_partial_import_resumes_explicitly_without_duplicate_postings(inputs,tmp_path,monkeypatch):
    contract,mapping,raw,ledger=inputs
    preview=preview_csv(raw,mapping,contract)
    original=ledger.receive;calls=[]
    def fail_second(*args,**kwargs):
        calls.append(1)
        if len(calls)==2:raise OSError('interrupción artificial')
        return original(*args,**kwargs)
    monkeypatch.setattr(ledger,'receive',fail_second)
    with pytest.raises(OSError):import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))
    assert len(ledger.overview()['receipts'])==1
    monkeypatch.setattr(ledger,'receive',original)
    result=import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))
    assert result['rows']==2 and len(ledger.overview()['receipts'])==2
    assert ledger.process(checksum(contract))['applied']==['buy-1','sell-1']


def test_invalid_rows_or_wrong_approval_cannot_start_import(inputs,tmp_path):
    contract,mapping,raw,ledger=inputs
    invalid=raw.replace(b'12,00',b'not-a-price')
    preview=preview_csv(invalid,mapping,contract)
    assert preview['errors'][0]['line']==3
    with pytest.raises(ValueError):import_csv(tmp_path,ledger,invalid,mapping,contract,approved_preview_sha256=checksum(preview))
    with pytest.raises(ValueError):import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256='f'*64)
    assert ledger.overview()['receipts']==[]
    assert not (tmp_path/'.local'/'tradingview-imports').exists()


@pytest.mark.parametrize('changed',[
    lambda raw:raw.replace(b'precio;',b'cantidad;'),
    lambda raw:raw.replace(b'precio;',b'unknown;'),
    lambda raw:raw.replace(b';12,00;',b';12,00;extra;'),
    lambda raw:raw.replace(b'2020-01-01T23:00:00Z',b'2020-01-01T23:00:00'),
    lambda raw:raw.replace(b'sell-1',b'buy-1'),
    lambda raw:raw.replace(b'Salida larga',b'Sell mystery'),
])
def test_does_not_guess_headers_timezones_actions_or_identities(inputs,changed):
    contract,mapping,raw,_=inputs
    try:result=preview_csv(changed(raw),mapping,contract)
    except ValueError:return
    assert result['errors']


@pytest.mark.parametrize('value',['1.23,00','1,00.000','1.000,00.000','1.000,00 USD','1_000','NaN','1e4','1,,2'])
def test_ambiguous_or_decorated_csv_number_is_rejected(inputs,value):
    _,mapping,_,_=inputs
    with pytest.raises(ValueError):parse_numeric(value,mapping)


def test_declared_thousands_unknown_fee_and_trade_number(inputs):
    contract,mapping,raw,_=inputs
    assert parse_numeric('1.000,25',mapping)=='1000.25'
    mapping=deepcopy(mapping);mapping['columns']['fee']=None;mapping['sequence_mode']='trade_number'
    result=preview_csv(raw.replace(b'sell-1;2;',b'sell-1;1;'),mapping,contract)
    assert not result['errors']
    assert [row['event']['sequence'] for row in result['rows']]==[1,2]
    assert result['rows'][0]['event']['fee'] is None


def test_duplicate_sequence_is_an_error_before_receiving_any_row(inputs):
    contract,mapping,raw,ledger=inputs
    preview=preview_csv(raw.replace(b'sell-1;2;',b'sell-1;1;'),mapping,contract)
    assert 'Secuencia duplicada' in preview['errors'][0]['reason']
    assert not ledger.overview()['receipts']


def test_original_tampering_is_detected_before_resume(inputs,tmp_path):
    contract,mapping,raw,ledger=inputs;preview=preview_csv(raw,mapping,contract)
    result=import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))
    (tmp_path/'.local'/'tradingview-imports'/result['id']/'original.csv').write_bytes(b'changed')
    with pytest.raises(ValueError,match='cambiaron'):import_csv(tmp_path,ledger,raw,mapping,contract,approved_preview_sha256=checksum(preview))
    assert len(ledger.overview()['receipts'])==2


def test_bundle_repository_is_idempotent_and_read_only_until_creation(tmp_path):
    repository=BundleRepository(tmp_path)
    assert repository.overview()=={'bundles':[],'warnings':[]}
    assert not (tmp_path/'.local').exists()
    contract=make_contract()
    first=repository.create(contract)
    assert first['created']
    assert repository.get(first['id'])['contract']==contract
    assert repository.create(contract)=={'id':first['id'],'created':False}
    assert repository.overview()['bundles'][0]['pine_compiled'] is False
    path=tmp_path/'.local'/'tradingview-bundles'/first['id']/'strategy.pine'
    path.write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError):repository.get(first['id'])
    assert repository.overview()['warnings']


def test_rejects_mapping_that_guesses_cost_or_reuses_columns(inputs):
    _,mapping,_,_=inputs
    for key,value in [('fee','precio'),('quantity',None)]:
        wrong=deepcopy(mapping);wrong['columns'][key]=value
        with pytest.raises(ValueError):validate_mapping(wrong)
