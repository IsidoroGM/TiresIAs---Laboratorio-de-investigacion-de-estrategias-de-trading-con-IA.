"""Unknown fields remain unknown and missing fills never shift later matches."""

import base64
from copy import deepcopy
import csv
import io
import json

import pytest

from trading_ai.execution_comparison import (ExecutionComparisons, POLICY, compare, declaration_template,
    mapping_template, normalize_csv, declaration, policy, validate_mapping)
from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.tv_service import SimulationService
from trading_ai.tv_simulation import SimulationLedger
from test_conversation_prices import make_prices


def reference():
    return {"configuration": {"pair":"EUR/USD","currency":"USD","strategy":"sma","fast":20,"slow":60},
        "source":{"start_date":"2025-01-01","end_date_exclusive":"2026-01-01"},"sessions_sha256":"a"*64,
        "hypothetical_fills":[{"side":side,"executed_at":f"2025-01-{day:02}T00:00:00.000Z","signal_at":f"2025-01-{day:02}T00:00:00.000Z",
            "quantity":"1","price":price,"assumed_commission":"0.01"}
            for day,side,price in ((2,"buy","10"),(3,"sell","12"),(4,"buy","11"))]}


def metadata(value):
    return {"producer":"Synthetic parser test, not an external engine","origin":"synthetic_fixture",
        **{key:value["configuration"][key] for key in ("pair","currency","strategy","fast","slow")},
        "start_date":value["source"]["start_date"],"end_date_exclusive":value["source"]["end_date_exclusive"],"sessions_sha256":value["sessions_sha256"]}


def csv_bytes(value):
    stream=io.StringIO(newline="");writer=csv.DictWriter(stream,fieldnames=list(mapping_template()["columns"]));writer.writeheader()
    for index,fill in enumerate(value["hypothetical_fills"]):
        writer.writerow({"external_id":"fixture-"+str(index+1),"executed_at":fill["executed_at"],"signal_at":fill["signal_at"],
            "side":fill["side"],"quantity":fill["quantity"],"price":fill["price"],"fee":fill["assumed_commission"]})
    return stream.getvalue().encode("utf-8")


def normalized(value=None):return normalize_csv(csv_bytes(value or reference()),mapping_template())
def contrasted(rows=None,settings=None,declared=None):
    value=reference();return compare(value,rows or normalized(),settings or dict(POLICY),declared or metadata(value))


def test_roundtrip_matches_declared_fields_without_external_authentication():
    result=contrasted()
    assert result["status"]=="matching_fields_unverified_origin" and len(result["pairs"])==3
    assert not result["missing"] and not result["extra"]


def test_missing_middle_row_does_not_shift_following_alignment():
    data=normalized();del data["rows"][1]
    result=contrasted(data)
    assert [(item["reference"]["index"],item["external"]["line"]) for item in result["pairs"]]==[(1,2),(3,4)]
    assert result["missing"][0]["index"]==2 and result["status"]=="differences"


def test_input_order_does_not_define_pairs_and_timestamps_normalize_to_utc():
    data=normalized();data["rows"].reverse()
    data["rows"][0]["executed_at"]="2025-01-04T00:00:00.000Z"
    result=contrasted(data)
    assert result["status"]=="matching_fields_unverified_origin"
    raw=csv_bytes(reference()).replace(b"2025-01-02T00:00:00.000Z",b"2025-01-02T01:00:00+01:00")
    assert normalize_csv(raw,mapping_template())["rows"][0]["executed_at"]=="2025-01-02T00:00:00.000Z"


@pytest.mark.parametrize("field,value",[("quantity","2"),("price","10.1"),("fee","0.02"),("signal_at","2025-01-01T23:00:00.000Z")])
def test_field_differences_are_not_hidden(field,value):
    data=normalized();data["rows"][0][field]=value
    result=contrasted(data)
    assert result["status"]=="differences" and result["pairs"][0]["differences"][0]["field"]==field


def test_shifted_time_needs_declared_unique_window_and_remains_a_difference():
    data=normalized();data["rows"][0]["executed_at"]="2025-01-02T00:01:00.000Z"
    strict=contrasted(data)
    assert len(strict["missing"])==len(strict["extra"])==1
    settings={**POLICY,"alignment_window_seconds":60}
    aligned=contrasted(data,settings)
    assert len(aligned["pairs"])==3 and aligned["pairs"][0]["differences"][0]["external_minus_python_seconds"]==60
    accepted=contrasted(data,{**settings,"time_tolerance_seconds":60})
    assert accepted["status"]=="matching_fields_unverified_origin"


def test_ambiguous_duplicates_are_never_merged_or_picked_by_position():
    data=normalized();data["rows"].append({**data["rows"][0],"line":5,"external_id":"partial-other-id"})
    result=contrasted(data)
    assert result["ambiguous"][0]["external_lines"]==[2,5]
    assert len(result["pairs"])==2 and result["status"]=="differences"


def test_wrong_side_is_missing_and_extra_instead_of_a_silent_pair():
    data=normalized();data["rows"][0]["side"]="sell"
    result=contrasted(data)
    assert len(result["missing"])==len(result["extra"])==1


@pytest.mark.parametrize("field",["fee","signal_at"])
def test_missing_optional_fields_are_unknown_not_zero_or_invented(field):
    mapping=mapping_template();mapping["columns"][field]=None
    data=normalize_csv(csv_bytes(reference()),mapping)
    result=contrasted(data)
    assert field in result["unknown_fields"] and result["status"]=="incomplete_evidence"
    assert data["rows"][0][field] is None


def test_empty_report_does_not_establish_equivalence():
    value=reference();value["hypothetical_fills"]=[]
    data=normalize_csv(csv_bytes(value),mapping_template())
    assert compare(value,data,POLICY,metadata(value))["status"]=="inconclusive_no_fills"
    assert compare(reference(),data,POLICY,metadata(reference()))["status"]=="differences"


def test_bad_rows_block_comparison_of_the_valid_subset():
    raw=csv_bytes(reference()).replace(b",12,0.01,",b",invalid,0.01,")
    data=normalize_csv(raw,mapping_template())
    assert len(data["rows"])==2 and len(data["errors"])==1
    result=contrasted(data)
    assert result["status"]=="invalid_report" and not result["pairs"]


def test_duplicate_external_identity_and_crossed_columns_are_errors():
    raw=csv_bytes(reference()).replace(b"fixture-2",b"fixture-1")
    assert normalize_csv(raw,mapping_template())["errors"]
    mapping=mapping_template();mapping["columns"]["fee"]="price"
    with pytest.raises(ValueError):validate_mapping(mapping)


def test_units_decimal_separator_and_unknown_ids_are_explicit():
    mapping=mapping_template();mapping.update(delimiter=";",decimal_separator=",",quantity_multiplier="100000")
    mapping["columns"]["external_id"]=None
    stream=io.StringIO();writer=csv.writer(stream,delimiter=";");writer.writerow(list(mapping["columns"]))
    writer.writerow(["", "2025-01-02T00:00:00Z", "buy", "0,00001", "1,15", "0,01", "2025-01-02T00:00:00Z"])
    value=normalize_csv(stream.getvalue().encode(),mapping)["rows"][0]
    assert value["quantity"]=="1" and value["price"]=="1.15" and value["external_id"] is None


def test_numeric_comparison_keeps_precision_at_the_tolerance_boundary():
    data=normalized();data["rows"][0]["price"]="11.0000000000000000000000000001"
    result=contrasted(data,{**POLICY,"price_tolerance":"1"})
    assert result["status"]=="differences"


@pytest.mark.parametrize("field,value",[("pair","GBP/USD"),("currency","EUR"),("fast",15),("start_date","2024-01-01"),("sessions_sha256","b"*64)])
def test_incompatible_configuration_is_preserved(field,value):
    declared=metadata(reference());declared[field]=value
    result=contrasted(declared=declared)
    assert result["status"]=="incompatible_configuration" and result["metadata_differences"][0]["field"]==field


def test_unknown_metadata_is_never_copied_from_python():
    declared={**declaration_template(),"producer":"unidentified supplied file"}
    result=contrasted(declared=declared)
    assert result["status"]=="incomplete_evidence" and "sessions_sha256" in result["metadata_unknown"]


@pytest.mark.parametrize("change",["negative_tolerance","boolean_window","window_order","unknown_field","unrecognized_zone","zero_scale","unknown_origin"])
def test_invalid_controls_are_rejected(change):
    mapping=mapping_template();settings=dict(POLICY);declared=metadata(reference())
    if change=="negative_tolerance":settings["price_tolerance"]="-1"
    elif change=="boolean_window":settings["alignment_window_seconds"]=True
    elif change=="window_order":settings["time_tolerance_seconds"]=1
    elif change=="unknown_field":mapping["guess_timezone"]=True
    elif change=="unrecognized_zone":mapping["time_format"]="broker_local"
    elif change=="zero_scale":mapping["quantity_multiplier"]="0"
    else:declared["origin"]="verified_broker"
    with pytest.raises(ValueError):validate_mapping(mapping);policy(settings);declaration(declared)


@pytest.fixture
def repository(tmp_path):
    make_prices(tmp_path,days=180)
    service=DukascopyResearch(tmp_path)
    run=service.run(dataset="sample",capital="1000",quantity="1",commission_rate="0.001")["id"]
    value=service.get(run)
    assert len(value["hypothetical_fills"])>=3
    return ExecutionComparisons(tmp_path),{"run":run,"raw":csv_bytes(value),"name":"synthetic-executions.csv",
        "mapping":mapping_template(),"tolerances":dict(POLICY),"metadata":metadata(value)}


def test_preview_save_read_and_replay_never_change_accounts_or_rerun(repository,monkeypatch):
    repo,values=repository
    def forbidden(*args,**kwargs):raise AssertionError("This path must not calculate strategies or accounts")
    monkeypatch.setattr("trading_ai.dukascopy_backtest.simulate",forbidden)
    before=SimulationLedger(repo.root).overview()
    preview=repo.preview(**values)
    assert not repo.directory.exists()
    saved=repo.save(approval_sha256=preview["approval_sha256"],**values)
    assert repo.save(approval_sha256=preview["approval_sha256"],**values)=={"id":saved["id"],"created":False}
    monkeypatch.setattr("trading_ai.execution_comparison.compare",forbidden)
    result=repo.get(saved["id"])
    assert result==preview["preview"] and not result["external_equivalence_verified"] and not result["external_format_verified"]
    assert SimulationLedger(repo.root).overview()==before and not (repo.root/".local/simulation").exists()
    assert repo.overview()["comparisons"][0]["inputs_verified_now"] is False


def test_changed_source_or_controls_invalidate_the_preview(repository):
    repo,values=repository;preview=repo.preview(**values)
    with pytest.raises(ValueError,match="cambiaron"):repo.save(approval_sha256=preview["approval_sha256"],**{**values,"tolerances":{**POLICY,"price_tolerance":"0.01"}})
    path=repo.root/".local/dukascopy-research"/values["run"]/"input-daily.json";path.write_bytes(b"{}")
    with pytest.raises(ValueError):repo.save(approval_sha256=preview["approval_sha256"],**values)
    assert not repo.directory.exists()


@pytest.mark.parametrize("name",["original.csv","comparison.json","reference-simulation.json","reference-input-manifest.json","reference-input-daily.json","summary.json"])
def test_changed_archived_file_is_rejected_on_read(repository,name):
    repo,values=repository;preview=repo.preview(**values);saved=repo.save(approval_sha256=preview["approval_sha256"],**values)
    (repo.directory/saved["id"]/name).write_bytes(b"altered")
    with pytest.raises(ValueError):repo.get(saved["id"])


def test_saved_report_is_independent_of_later_source_deletion(repository):
    repo,values=repository;preview=repo.preview(**values);saved=repo.save(approval_sha256=preview["approval_sha256"],**values)
    (repo.root/".local/dukascopy-research"/values["run"]/"simulation.json").unlink()
    assert repo.get(saved["id"])["reference_run"]==values["run"]


def test_metadata_query_does_not_validate_heavy_inputs(repository,monkeypatch):
    repo,values=repository;preview=repo.preview(**values);repo.save(approval_sha256=preview["approval_sha256"],**values)
    monkeypatch.setattr(repo,"get",lambda *args:(_ for _ in ()).throw(AssertionError("No full load")))
    assert repo.overview()["metadata_only"]


@pytest.mark.parametrize("name",["summary.json","manifest.json"])
def test_malformed_catalog_entry_is_visible_without_breaking_other_queries(repository,name):
    repo,values=repository;preview=repo.preview(**values);saved=repo.save(approval_sha256=preview["approval_sha256"],**values)
    (repo.directory/saved["id"]/name).write_bytes(b"[]")
    overview=repo.overview()
    assert not overview["comparisons"] and overview["warnings"]
    with pytest.raises(ValueError):repo.get(saved["id"])


def test_safe_ids_and_invalid_headers_have_no_storage(repository):
    repo,values=repository
    with pytest.raises(ValueError):repo.get("../outside")
    with pytest.raises(ValueError):repo.preview(**{**values,"raw":b"x,x\n1,2\n"})
    with pytest.raises(ValueError):repo.preview(**{**values,"name":"../report.csv"})
    assert not repo.directory.exists()


def test_http_preview_save_guards_and_origin_labels(repository):
    repo,values=repository
    from trading_ai.lab import create_server
    from test_conversation import request,auth
    import threading
    server=create_server(root=repo.root,port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        body={"action":"preview_execution_comparison",**{key:value for key,value in values.items() if key!="raw"},"csv_base64":base64.b64encode(values["raw"]).decode()}
        assert request(server,"/api/simulation","POST",json.dumps(body))[0]==403
        headers=auth(server)
        status,preview=request(server,"/api/simulation","POST",json.dumps(body),**headers)
        assert status==202 and not preview["preview"]["external_origin_verified"]
        status,saved=request(server,"/api/simulation","POST",json.dumps({**body,"action":"save_execution_comparison","approve_preview_sha256":preview["approval_sha256"]}),**headers)
        assert status==202
        assert request(server,"/api/simulation/execution-comparisons/"+saved["id"])[1]==preview["preview"]
        assert request(server,"/api/chat")[1]["reserved"]=={"model_requests":0,"experiments":0}
    finally:server.shutdown();thread.join();server.server_close()
