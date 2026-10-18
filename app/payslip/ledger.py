"""급여대장 엑셀(1행 = 직원 1명) → 직원별 명세 데이터. 합계 열이 있으면 대조한다."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.money import D
from app.payslip.company import MAX_ROWS
from app.xlsx import InputError, read_rows

COMMON = ["지급년월", "지급일", "사원번호", "성명", "직책", "생년월일", "입사일", "지급구분", "이메일", "비고"]
TOTALS = {"지급총액": "gross", "공제총액": "deductions", "실지급액": "net"}


@dataclass
class Payslip:
    month: str            # "2026-09"
    pay_date: str         # "2026년 10월 10일"
    employee_no: str
    name: str
    title: str
    birth: str
    hired: str
    kind: str
    email: str
    note: str
    pay: list             # [(항목, Decimal)]
    deductions_list: list
    gross: Decimal
    deductions: Decimal
    net: Decimal

    def pay_rows(self):
        return _pad(self.pay)

    def deduction_rows(self):
        return _pad(self.deductions_list)

    @property
    def month_label(self):
        y, m = self.month.split("-")
        return f"{y}년 {int(m):02d}월"


def _pad(rows):
    return list(rows) + [("-", None)] * (MAX_ROWS - len(rows))


def _text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        v = v.date()
    if isinstance(v, date):
        return f"{v:%Y.%m.%d}"
    return str(v).strip()


def _pay_date(v) -> str:
    if isinstance(v, datetime):
        v = v.date()
    if isinstance(v, date):
        return f"{v.year}년 {v.month:02d}월 {v.day:02d}일"
    return _text(v)


def _month(v) -> str:
    if isinstance(v, (datetime, date)):
        return f"{v.year}-{v.month:02d}"
    return str(v).strip()[:7]


def _num(v) -> Decimal:
    return D(0) if v in (None, "") else D(v)


def load_ledger(path, company):
    """반환: (명세 목록, 확인 필요 문장 목록). 회사 설정 항목이 열로 없으면 InputError."""
    rows = read_rows(path, COMMON + list(company.pay_items) + list(company.deduction_items))
    slips, issues = [], []
    for r in rows:
        no, name = _text(r["사원번호"]), _text(r["성명"])
        pay = [(k, _num(r[k])) for k in company.pay_items]
        ded = [(k, _num(r[k])) for k in company.deduction_items]
        gross = sum((v for _, v in pay), D(0))
        deductions = sum((v for _, v in ded), D(0))
        calc = {"gross": gross, "deductions": deductions, "net": gross - deductions}
        bad = [f"{col} 대장 {_num(r[col]):,.0f} ≠ 계산 {calc[key]:,.0f}"
               for col, key in TOTALS.items() if col in r and r[col] not in (None, "") and _num(r[col]) != calc[key]]
        if bad:
            issues.append(f"[{no} {name}] 합계 불일치 — {', '.join(bad)} → 명세서 만들지 않음")
            continue
        if not _text(r["이메일"]):
            issues.append(f"[{no} {name}] 이메일 없음 → PDF만 만들고 메일 초안 생략")
        slips.append(Payslip(_month(r["지급년월"]), _pay_date(r["지급일"]), no, name, _text(r["직책"]),
                             _text(r["생년월일"]), _text(r["입사일"]), _text(r["지급구분"]), _text(r["이메일"]),
                             _text(r["비고"]), pay, ded, gross, deductions, gross - deductions))
    return slips, issues
