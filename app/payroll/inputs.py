"""각 모듈의 결과를 표준 급여 입력(PayrollInput)으로 바꾼다 (PROJECT_SPEC 8.2).
계산 엔진은 이 목록만 본다 — 엑셀·캡스·시간표를 모른다."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.classes.teaching import MAKEUP, REGULAR, SUBSTITUTE
from app.issues import DATA, Issue
from app.money import D
from app.xlsx import read_rows

ITEM_BY_KIND = {REGULAR: "정규 강의료", SUBSTITUTE: "대체 강의료", MAKEUP: "보강 강의료"}


@dataclass(frozen=True)
class PayrollInput:
    employee_id: str
    source: str               # classes | attendance | hr | manual
    item: str
    side: str                 # 지급 | 공제
    quantity: Decimal
    unit: str                 # SESSION(시수) | HOUR | MONTH | FIXED
    unit_rate: Optional[Decimal]   # None이면 엔진이 계약 시급 적용
    amount: Optional[Decimal]      # 고정 금액 항목
    basis: str


def build_inputs(contracts, attendance, teaching_lines, allowances_path, year, month):
    inputs, issues = [], []
    order = {REGULAR: 0, MAKEUP: 1, SUBSTITUTE: 2}
    for line in sorted(teaching_lines, key=lambda l: (l.employee_id, order[l.kind])):
        if contracts[line.employee_id].pay_type != "시수제":
            issues.append(Issue(DATA, line.employee_id, None, f"시수제가 아닌 직원에게 수업 시수가 있어 제외: {line.basis}"))
            continue
        inputs.append(PayrollInput(line.employee_id, "classes", ITEM_BY_KIND[line.kind], "지급",
                                   line.hours, "SESSION", None, None, line.basis))

    for emp, c in contracts.items():
        att = attendance.get(emp)
        if c.pay_type == "시간제":
            minutes = att.work_minutes if att else 0
            worked = sum(1 for d in att.days if d.work_minutes > 0) if att else 0
            fixed = sum(1 for d in att.days if d.note.startswith("수기 보정")) if att else 0
            basis = f"근무 {worked}일, 총 {D(minutes) / 60:g}시간" + (f" (수기 보정 {fixed}건 포함)" if fixed else "")
            inputs.append(PayrollInput(emp, "attendance", "근무수당", "지급", D(minutes) / 60, "HOUR", None, None, basis))
        elif c.pay_type == "월급제":
            late = len(att.late_days) if att else 0
            basis = "월 고정급" + (f" (지각 {late}일 — 공제 규칙 미확정, 공제 안 함)" if late else "")
            inputs.append(PayrollInput(emp, "hr", "기본급", "지급", D(1), "MONTH", c.monthly_salary, None, basis))

    if allowances_path:
        for r in read_rows(allowances_path, ["직원ID", "항목", "구분", "금액", "사유"]):
            emp, side = str(r["직원ID"]).strip(), str(r["구분"]).strip()
            if emp not in contracts:
                issues.append(Issue(DATA, emp, None, f"수당·공제 '{r['항목']}'의 직원ID {emp}가 명부에 없어 제외"))
                continue
            if side not in ("지급", "공제"):
                issues.append(Issue(DATA, emp, None, f"수당·공제 '{r['항목']}' 구분 '{side}'를 알 수 없어 제외"))
                continue
            inputs.append(PayrollInput(emp, "manual", str(r["항목"]), side, D(1), "FIXED", None, D(r["금액"]),
                                       str(r["사유"] or "")))
    return inputs, issues
