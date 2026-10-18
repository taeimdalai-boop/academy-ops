"""계산 엔진. 입력: PayrollInput 목록 + 계약 + 정책. 출력: 직원별 명세(Statement).
법정 하한(최저시급) 미달이면 그 직원은 계산하지 않는다 — 법정 금액으로 자동 대체하지 않음."""
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.issues import BLOCK, Issue
from app.money import D, round_amount
from app.xlsx import InputError

UNIT_LABEL = {"SESSION": "시수", "HOUR": "시간", "MONTH": "개월", "FIXED": ""}


@dataclass(frozen=True)
class StatementLine:
    item: str
    side: str
    quantity: Decimal
    unit: str
    unit_rate: Optional[Decimal]
    amount: Decimal
    basis: str


@dataclass
class Statement:
    employee_id: str
    name: str
    email: str
    lines: list = field(default_factory=list)
    gross: Decimal = D(0)
    deductions: Decimal = D(0)
    net: Decimal = D(0)


def calculate(inputs, contracts, policy):
    if policy.substitute_rate != "substitute_own":
        raise InputError(f"policy.yaml: substitute_rate '{policy.substitute_rate}'는 아직 지원하지 않음")
    by_emp = defaultdict(list)
    for i in inputs:
        by_emp[i.employee_id].append(i)

    statements, issues = {}, []
    for emp in sorted(by_emp):
        c = contracts[emp]
        hourly = c.effective_hourly()
        if hourly < policy.min_hourly:
            issues.append(Issue(BLOCK, emp, None,
                                f"최저시급 미달: 시급 {hourly:,.0f}원 < {policy.min_hourly:,.0f}원 — 명세서를 만들지 않음, 계약 확인 필요"))
            continue
        s = Statement(emp, c.name, c.email)
        for i in by_emp[emp]:
            rate = i.unit_rate
            if i.amount is not None:
                amount = round_amount(i.amount, policy.rounding)
            else:
                if rate is None:
                    rate = c.hourly_rate
                amount = round_amount(i.quantity * rate, policy.rounding)
            s.lines.append(StatementLine(i.item, i.side, i.quantity, i.unit, rate, amount, i.basis))
        s.gross = sum((l.amount for l in s.lines if l.side == "지급"), D(0))
        s.deductions = sum((l.amount for l in s.lines if l.side == "공제"), D(0))
        s.net = s.gross - s.deductions
        statements[emp] = s
    return statements, issues


def describe(line: StatementLine) -> str:
    """산출근거 한 줄: '52시수 × 30,000원 = 1,560,000원'."""
    if line.unit == "FIXED" or line.unit_rate is None:
        return f"{line.amount:,.0f}원"
    return f"{line.quantity:g}{UNIT_LABEL[line.unit]} × {line.unit_rate:,.0f}원 = {line.amount:,.0f}원"
