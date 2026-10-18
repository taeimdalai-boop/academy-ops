from app.attendance.connectors.adt_caps.connector import load_events
from app.attendance.connectors.adt_caps.mapper import to_kind


def test_mode_map():
    assert to_kind(1) == "CHECK_IN"
    assert to_kind(2) == "CHECK_OUT"
    assert to_kind(7) == "MEAL"


def test_load_events_dedup_and_unknown():
    ev, issues = load_events("samples/2026-09/caps_events.xlsx", {"A01", "A02"})
    a02_0902_in = [e for e in ev if e.employee_id == "A02" and e.at.day == 2 and e.kind == "CHECK_IN"]
    assert len(a02_0902_in) == 1
    assert all(e.employee_id != "9999" for e in ev)
    assert any("9999" in i.message for i in issues)
