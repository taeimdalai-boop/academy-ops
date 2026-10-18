from datetime import date


def test_a02_hours_109(attendance):
    att, _ = attendance
    assert att["A02"].work_minutes == 109 * 60


def test_missing_checkout_counts_zero_and_is_reported(attendance):
    att, issues = attendance
    d22 = next(r for r in att["A02"].days if r.day == date(2026, 9, 22))
    assert d22.work_minutes == 0
    assert any(i.employee_id == "A02" and i.day == date(2026, 9, 22) and "퇴근" in i.message for i in issues)


def test_correction_applied(attendance):
    att, _ = attendance
    d15 = next(r for r in att["A02"].days if r.day == date(2026, 9, 15))
    assert d15.work_minutes == 300


def test_long_day_and_late_reported(attendance):
    att, issues = attendance
    msgs = " ".join(i.message for i in issues)
    assert "8시간" in msgs and "지각" in msgs
    assert att["A01"].late_days == [date(2026, 9, 3), date(2026, 9, 17)]
