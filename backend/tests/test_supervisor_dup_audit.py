"""dup_audit finds the SAME fact in several places — and stays conservative."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "dup_audit", Path(__file__).resolve().parents[2] / "scripts" / "supervisor" / "dup_audit.py")
dup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dup)


def _f(res, rule_part):
    return next(f for f in res["findings"] if rule_part in f["rule"])


def test_same_cheque_in_one_account_is_certain_and_other_account_is_review():
    data = {"guarantors": [
        {"account_no": "1", "cheque_no": "CHQ 100"}, {"account_no": "1", "cheque_no": "chq-100"},
        {"account_no": "2", "cheque_no": "CHQ 100"},
        {"account_no": "3", "cheque_no": "999999", "is_deleted": True},
        {"account_no": "3", "cheque_no": "999999"},
    ]}
    r = dup.find_duplicates(data)
    assert _f(r, "guarantors: same cheque twice")["groups"] == 1
    assert _f(r, "guarantors: same cheque twice")["level"] == "probable"  # a cheque may sit in two registry years
    cross = _f(r, "guarantors: same cheque number under several")
    assert cross["groups"] == 1 and cross["level"] == "review"


def test_deleted_rows_and_blank_keys_are_never_duplicates():
    data = {"fixed_deposits": [
        {"account_no": "1", "fd_number": ""}, {"account_no": "1", "fd_number": ""},
        {"account_no": "1", "fd_number": "FD1", "is_deleted": True}, {"account_no": "1", "fd_number": "FD1"},
    ]}
    r = dup.find_duplicates(data)
    assert r["certain_groups"] == 0


def test_identical_file_hash_and_identity_numbers_across_accounts():
    data = {"attachments": [{"account_no": "1", "content_sha256": "aa"}, {"account_no": "2", "content_sha256": "aa"}],
            "customer_profiles": [{"account_no": "1", "passport_no": "P123456"}, {"account_no": "2", "passport_no": "p-123456"}]}
    r = dup.find_duplicates(data)
    assert _f(r, "attachments: identical file under several")["groups"] == 1
    assert _f(r, "same passport_no")["groups"] == 1
    assert r["certain_groups"] == 0 and r["review_groups"] == 2


def test_examples_carry_account_numbers_not_names():
    r = dup.find_duplicates({"customers": [{"account_no": "7", "name": "SECRET NAME LLC"}, {"account_no": "7", "name": "x"}]})
    assert "SECRET" not in str(r)


def test_extraction_sample_rotates_weekly_and_skips_unfiled_accounts():
    spec2 = importlib.util.spec_from_file_location(
        "extraction_sample", Path(__file__).resolve().parents[2] / "scripts" / "supervisor" / "extraction_sample.py")
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "supervisor"))
    ex = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(ex)
    data = {
        "attachments": [{"id": f"a{i}", "account_no": str(i), "drive_file_id": "d", "original_name": "x.pdf"} for i in range(40)]
        + [{"id": "u", "account_no": "cust-unknown", "drive_file_id": "d"}, {"id": "n", "account_no": "999"}],
        "customer_profiles": [{"account_no": str(i), "passport_no": "P1"} for i in range(40)] + [{"account_no": "999"}],
    }
    w1, w2 = ex.pick(data, 5, "2026-W40"), ex.pick(data, 5, "2026-W41")
    assert len(w1) == 5 and [x["account_no"] for x in w1] != [x["account_no"] for x in w2]
    assert w1 == ex.pick(data, 5, "2026-W40"), "deterministic within a week"
    assert all(x["account_no"] not in ("cust-unknown", "999") for x in w1 + w2)
    assert w1[0]["files"][0]["download"].endswith("/download")
