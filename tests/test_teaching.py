from decimal import Decimal


def _hours(lines, emp, kind=None):
    return sum((l.hours for l in lines if l.employee_id == emp and (kind is None or l.kind == kind)), Decimal(0))


def test_hours(teaching):
    lines, _ = teaching
    assert _hours(lines, "T01") == 52
    assert _hours(lines, "T02") == 24
    assert _hours(lines, "T03") == 23
    assert _hours(lines, "T03", "SUBSTITUTE") == 3
    assert _hours(lines, "T01", "MAKEUP") == 4


def test_issues(teaching):
    _, issues = teaching
    assert any("S999" in i.message for i in issues)
    assert any(i.category == "규칙 미확정" and "대체" in i.message for i in issues)
