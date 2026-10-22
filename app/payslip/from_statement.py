"""계산 엔진 결과(Statement) → 명세서 데이터(Payslip) 어댑터.

계산하는 쪽(app.payroll)과 명세서를 그리는 쪽(app.payslip)은 서로를 모른다.
이 모듈만 둘을 안다. 금액은 손대지 않고 **표시 형식만** 맞춘다.
"""
from app.payslip.company import MAX_ROWS
from app.payslip.ledger import Payslip

# 실물 양식은 한 면에 항목 10행까지. 그보다 많으면 사람이 정리해야 한다.
_OVERFLOW = "항목 {n}개 — 명세서 양식 최대 {max}행을 넘음"


def build(statement, contract, month, pay_day=0):
    """Statement 1건 → Payslip 1건. 넘치면 (None, 사유) 를 돌려준다."""
    pay = [(l.item, l.amount) for l in statement.lines if l.side == "지급"]
    ded = [(l.item, l.amount) for l in statement.lines if l.side != "지급"]
    for rows in (pay, ded):
        if len(rows) > MAX_ROWS:
            return None, _OVERFLOW.format(n=len(rows), max=MAX_ROWS)

    slip = Payslip(
        month=month,
        pay_date=_pay_date(month, pay_day),
        employee_no=statement.employee_id,
        name=statement.name,
        title=getattr(contract, "role", "") or "",
        birth="-",                      # 급여 계산에 쓰지 않아 수집하지 않는다(PII 최소수집). 빈칸이 아니라 "-"로 그 사실을 드러낸다.
        hired=_date(getattr(contract, "start", None)),
        kind=getattr(contract, "pay_type", "") or "",
        email=statement.email or "",
        note="",
        pay=pay,
        deductions_list=ded,
        gross=statement.gross,
        deductions=statement.deductions,
        net=statement.net,
    )
    return slip, None


def _date(d):
    return f"{d:%Y.%m.%d}" if d else ""


def _pay_date(month, pay_day):
    """지급일은 급여 귀속월의 다음 달. pay_day가 0이면 적지 않는다."""
    if not pay_day:
        return "-"
    y, m = (int(x) for x in month.split("-"))
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y}년 {m:02d}월 {pay_day:02d}일"
