"""배정 시간표 + 휴강·대체·보강 기록 → 강사별 인정 시수 줄."""
from dataclasses import dataclass
from decimal import Decimal

from app.hr.contracts import to_date
from app.issues import DATA, RULE, Issue
from app.money import D
from app.xlsx import read_rows

REGULAR, SUBSTITUTE, MAKEUP = "REGULAR", "SUBSTITUTE", "MAKEUP"


@dataclass(frozen=True)
class TeachingLine:
    employee_id: str
    kind: str
    hours: Decimal
    basis: str


def compute_teaching(schedule_path, changes_path, contracts, policy, year, month):
    sessions = {}
    for r in read_rows(schedule_path, ["수업ID", "날짜", "강사ID", "시수"]):
        d = to_date(r["날짜"])
        if d.year == year and d.month == month:
            sessions[str(r["수업ID"]).strip()] = {"day": d, "emp": str(r["강사ID"]).strip(), "hours": D(r["시수"])}

    issues, lines = [], []
    cancelled, substituted, makeups = set(), {}, []
    changes = read_rows(changes_path, ["수업ID", "유형", "대체강사ID", "날짜", "강사ID", "시수"]) if changes_path else []
    for r in changes:
        sid, kind = str(r["수업ID"]).strip(), str(r["유형"]).strip()
        if kind == "보강":
            makeups.append({"sid": sid, "day": to_date(r["날짜"]), "emp": str(r["강사ID"]).strip(), "hours": D(r["시수"])})
            continue
        if sid not in sessions:
            issues.append(Issue(DATA, None, None, f"변경 기록의 수업ID {sid}가 이번 달 시간표에 없어 반영하지 않음"))
            continue
        if kind == "휴강":
            cancelled.add(sid)
        elif kind == "대체":
            sub = str(r["대체강사ID"] or "").strip()
            if sub not in contracts:
                issues.append(Issue(DATA, None, sessions[sid]["day"], f"수업 {sid} 대체강사 '{sub}'가 직원 명부에 없어 반영하지 않음"))
                continue
            substituted[sid] = sub
        else:
            issues.append(Issue(DATA, None, None, f"수업 {sid}의 변경 유형 '{kind}'를 알 수 없어 반영하지 않음"))

    per_emp = {}
    for sid, s in sessions.items():
        if not contracts[s["emp"]].active_on(s["day"]):
            issues.append(Issue(DATA, s["emp"], s["day"], f"수업 {sid}가 계약 기간 밖이라 제외"))
            continue
        acc = per_emp.setdefault(s["emp"], {"assigned": D(0), "cancel": D(0), "subbed_out": D(0)})
        acc["assigned"] += s["hours"]
        if sid in cancelled:
            acc["cancel"] += s["hours"]
        elif sid in substituted:
            acc["subbed_out"] += s["hours"]
            sub = substituted[sid]
            lines.append(TeachingLine(sub, SUBSTITUTE, s["hours"],
                                      f"{s['day'].month}/{s['day'].day} {s['emp']} 수업 대체 {s['hours']:g}시수"))
            if not policy.substitute_confirmed:
                issues.append(Issue(RULE, sub, s["day"],
                                    f"대체 수업({sid}) 시급을 '대체 강사 본인 시급'으로 계산함 — 원장님 확인 필요(인터뷰 C1)"))

    for emp, a in per_emp.items():
        hours = a["assigned"] - a["cancel"] - a["subbed_out"]
        basis = f"배정 {a['assigned']:g}"
        if a["cancel"]:
            basis += f" − 휴강 {a['cancel']:g}"
        if a["subbed_out"]:
            basis += f" − 대체로 빠짐 {a['subbed_out']:g}"
        lines.append(TeachingLine(emp, REGULAR, hours, basis + f" = {hours:g}시수"))

    for m in makeups:
        if m["emp"] not in contracts:
            issues.append(Issue(DATA, None, m["day"], f"보강 {m['sid']} 강사 '{m['emp']}'가 명부에 없어 반영하지 않음"))
            continue
        lines.append(TeachingLine(m["emp"], MAKEUP, m["hours"], f"{m['day'].month}/{m['day'].day} 보강 {m['hours']:g}시수"))
    return lines, issues
