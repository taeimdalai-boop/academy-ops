"""표준 출퇴근 기록 → 일별 근태 → 월 집계. 추정하지 않는다: 빠진 기록은 0분 + 확인 필요."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Optional

from app.attendance import model
from app.hr.contracts import to_date
from app.issues import DATA, LEGAL, RULE, Issue
from app.xlsx import read_rows


@dataclass
class DailyRecord:
    day: date
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    break_minutes: int
    work_minutes: int
    note: str = ""


@dataclass
class MonthlyAttendance:
    employee_id: str
    days: list = field(default_factory=list)
    work_minutes: int = 0
    late_days: list = field(default_factory=list)
    long_days: list = field(default_factory=list)   # (날짜, 근무분)


def hm(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}시간 {m}분" if m else f"{h}시간"


def _to_time(v) -> time:
    if isinstance(v, time):
        return v
    if isinstance(v, datetime):
        return v.time()
    h, m = (int(x) for x in str(v).strip().split(":")[:2])
    return time(h, m)


def _load_corrections(path):
    if not path:
        return {}
    rows = read_rows(path, ["직원ID", "날짜", "보정출근", "보정퇴근", "사유"])
    out = {}
    for r in rows:
        d = to_date(r["날짜"])
        out[(str(r["직원ID"]).strip(), d)] = (
            datetime.combine(d, _to_time(r["보정출근"])),
            datetime.combine(d, _to_time(r["보정퇴근"])),
            str(r["사유"] or ""),
        )
    return out


def _break_minutes(events):
    total, started = 0, None
    for e in events:
        if e.kind == model.BREAK_OUT:
            started = e.at
        elif e.kind == model.BREAK_IN and started:
            total += int((e.at - started).total_seconds() // 60)
            started = None
    return total


def summarize_month(events, corrections_path, contracts, policy, year, month):
    corrections = _load_corrections(corrections_path)
    by_day = defaultdict(list)
    for e in events:
        if e.at.year == year and e.at.month == month:
            by_day[(e.employee_id, e.at.date())].append(e)
    for key in corrections:
        by_day.setdefault(key, [])

    result, issues = {}, []
    for (emp, d) in sorted(by_day):
        c = contracts[emp]
        evs = by_day[(emp, d)]
        if not c.active_on(d):
            issues.append(Issue(DATA, emp, d, "계약 기간 밖 출입 기록 — 근태에서 제외"))
            continue
        ins = [e.at for e in evs if e.kind == model.CHECK_IN]
        outs = [e.at for e in evs if e.kind == model.CHECK_OUT]
        check_in, check_out = (min(ins) if ins else None), (max(outs) if outs else None)
        note = ""
        if (emp, d) in corrections:
            check_in, check_out, reason = corrections[(emp, d)]
            note = f"수기 보정: {reason}"
        brk = _break_minutes(evs)
        if check_in and check_out:
            work = int((check_out - check_in).total_seconds() // 60) - brk
        else:
            work = 0
            if check_in or check_out:
                missing = "퇴근" if check_in else "출근"
                issues.append(Issue(DATA, emp, d, f"{missing} 기록 없음 — 근무시간 0으로 계산, 보정 파일에 추가 필요"))
                note = f"{missing} 누락"
        m = result.setdefault(emp, MonthlyAttendance(emp))
        if work > policy.max_daily_hours * 60:
            m.long_days.append((d, work))
        m.days.append(DailyRecord(d, check_in, check_out, brk, work, note))
        m.work_minutes += work
        if c.pay_type == "월급제" and check_in and check_in.time() > policy.late_after:
            m.late_days.append(d)

    for emp, m in result.items():
        if m.long_days:
            days = ", ".join(f"{d.month}/{d.day}({hm(w)})" for d, w in m.long_days[:5])
            more = f" 외 {len(m.long_days) - 5}일" if len(m.long_days) > 5 else ""
            issues.append(Issue(LEGAL, emp, None,
                                f"하루 {policy.max_daily_hours:g}시간 초과 {len(m.long_days)}일: {days}{more} — "
                                "출근~퇴근 체류시간 기준(점심 휴게시간 규칙 미확정이라 차감 안 함), 연장 가산수당은 계산하지 않음"))
        if m.late_days:
            days = ", ".join(f"{d.month}/{d.day}" for d in m.late_days)
            issues.append(Issue(RULE, emp, None, f"지각 {len(m.late_days)}일({days}) — 월급제 지각 공제 규칙 미확정이라 공제하지 않음"))
    return result, issues
