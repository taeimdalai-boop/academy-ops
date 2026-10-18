import json
from decimal import Decimal

from app.payroll.engine import calculate
from app.payroll.inputs import PayrollInput

EXPECTED = json.load(open("samples/2026-09/expected.json", encoding="utf-8"))


def test_engine_matches_expected(pipeline):
    statements, _ = pipeline
    for emp, e in EXPECTED["employees"].items():
        if e.get("blocked"):
            assert emp not in statements
        else:
            s = statements[emp]
            assert (s.gross, s.deductions, s.net) == (Decimal(e["gross"]), Decimal(e["deductions"]), Decimal(e["net"])), emp


def test_min_wage_blocks_t04(pipeline):
    _, issues = pipeline
    assert any(i.category == "계산 중단" and i.employee_id == "T04" for i in issues)


def test_lines_sum(pipeline):
    for s in pipeline[0].values():
        paid = sum((l.amount for l in s.lines if l.side == "지급"), Decimal(0))
        ded = sum((l.amount for l in s.lines if l.side == "공제"), Decimal(0))
        assert (paid, ded, paid - ded) == (s.gross, s.deductions, s.net)


def test_rounding_floor(contracts, policy):
    inp = [PayrollInput("A02", "attendance", "근무수당", "지급", Decimal("1.5051"), "HOUR", Decimal("11000"), None, "시험")]
    s, _ = calculate(inp, contracts, policy)
    assert s["A02"].gross == Decimal("16556")      # 16,556.1 → 절사
