from datetime import date
from decimal import Decimal

from app.hr.contracts import load_contracts


def test_contracts():
    c = load_contracts("samples/2026-09/employees.xlsx")
    assert set(c) == {"T01", "T02", "T03", "T04", "A01", "A02"}
    assert c["T01"].pay_type == "시수제" and c["T01"].hourly_rate == Decimal("30000")
    assert c["A01"].effective_hourly().quantize(Decimal("1")) == Decimal("11962")
    assert c["T01"].active_on(date(2026, 9, 1))
    assert not c["T04"].active_on(date(2026, 8, 31))
