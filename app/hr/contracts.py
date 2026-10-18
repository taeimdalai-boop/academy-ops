"""직원·근로계약. 급여 계산 조건은 코드가 아니라 이 계약 레코드에서 읽는다."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.money import D
from app.xlsx import InputError, read_rows

PAY_TYPES = {"시수제", "시간제", "월급제"}
REQUIRED = ["직원ID", "이름", "직군", "급여형태", "시급", "월급", "월소정근로시간", "계약시작", "계약종료", "이메일"]


def to_date(v) -> Optional[date]:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])


@dataclass(frozen=True)
class Contract:
    employee_id: str
    name: str
    role: str
    pay_type: str
    hourly_rate: Optional[Decimal]
    monthly_salary: Optional[Decimal]
    monthly_hours: Optional[Decimal]
    start: date
    end: Optional[date]
    email: str

    def effective_hourly(self) -> Decimal:
        """최저시급 비교용 시급. 월급제는 월급 ÷ 월 소정근로시간."""
        if self.pay_type == "월급제":
            return self.monthly_salary / self.monthly_hours
        return self.hourly_rate

    def active_on(self, d: date) -> bool:
        return self.start <= d and (self.end is None or d <= self.end)


def load_contracts(path) -> dict:
    out = {}
    for r in read_rows(path, REQUIRED):
        emp = str(r["직원ID"]).strip()
        pay_type = str(r["급여형태"]).strip()
        if pay_type not in PAY_TYPES:
            raise InputError(f"employees.xlsx: {emp} 급여형태 '{pay_type}'는 지원하지 않음 ({', '.join(sorted(PAY_TYPES))})")
        num = lambda v: None if v in (None, "") else D(v)
        c = Contract(emp, str(r["이름"]), str(r["직군"]), pay_type, num(r["시급"]), num(r["월급"]),
                     num(r["월소정근로시간"]), to_date(r["계약시작"]), to_date(r["계약종료"]), str(r["이메일"]))
        if pay_type == "월급제" and not (c.monthly_salary and c.monthly_hours):
            raise InputError(f"employees.xlsx: {emp} 월급제인데 월급 또는 월소정근로시간 없음")
        if pay_type != "월급제" and not c.hourly_rate:
            raise InputError(f"employees.xlsx: {emp} {pay_type}인데 시급 없음")
        out[emp] = c
    return out
