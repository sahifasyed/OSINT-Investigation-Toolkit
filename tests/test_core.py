import os
import tempfile

import pytest

from ovt.custody import CustodyLog
from ovt.timestamps import normalise, sequence_check


@pytest.fixture
def tmp_evidence(tmp_path):
    f = tmp_path / "artifact.bin"
    f.write_bytes(b"evidence content")
    return str(f)


def test_register_and_verify(tmp_path, tmp_evidence):
    log = CustodyLog(log_path=str(tmp_path / "log.json"), analyst="test")
    eid = log.register(tmp_evidence, source="unit test")
    assert eid == "E0001"
    assert log.verify(eid, tmp_evidence) is True


def test_verify_detects_tampering(tmp_path, tmp_evidence):
    log = CustodyLog(log_path=str(tmp_path / "log.json"), analyst="test")
    eid = log.register(tmp_evidence, source="unit test")
    with open(tmp_evidence, "ab") as f:
        f.write(b" tampered")
    assert log.verify(eid, tmp_evidence) is False
    actions = [e["action"] for e in log.entries(eid)]
    assert "integrity_check" in actions


def test_duplicate_registration_reuses_id(tmp_path, tmp_evidence):
    log = CustodyLog(log_path=str(tmp_path / "log.json"), analyst="test")
    first = log.register(tmp_evidence, source="a")
    second = log.register(tmp_evidence, source="b")
    assert first == second


def test_normalise_exif_format():
    ts = normalise("2026:03:12 09:30:00")
    assert ts["utc"].year == 2026
    assert ts["assumption"] == "naive timestamp, UTC assumed"


def test_normalise_with_offset():
    ts = normalise("12/03/2026 09:30", assume_tz_offset_hours=2)
    assert ts["utc"].hour == 7  # 09:30 UTC+2 -> 07:30 UTC


def test_normalise_rejects_garbage():
    with pytest.raises(ValueError):
        normalise("not a date")


def test_sequence_check_orders_and_flags():
    a = normalise("2026-03-12T10:00:00Z")
    b = normalise("2026-03-12T09:00:00Z")
    c = normalise("2026-03-12T10:00:00Z")
    ordered, clashes = sequence_check([("A", a), ("B", b), ("C", c)])
    assert ordered[0][0] == "B"
    assert ("A", "C") in clashes or ("C", "A") in clashes
