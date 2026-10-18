"""급여 계산 한 번에 실행.

python -m app.cli run --month 2026-09 --input samples/2026-09 --output out/2026-09
종료 코드: 0 정상 · 1 입력 오류 · 2 계산 중단된 직원 있음(최저시급 미달 등)
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

from app.attendance.connectors.adt_caps.connector import load_events
from app.attendance.daily import summarize_month
from app.classes.teaching import compute_teaching
from app.documents.issues_md import write_issues_md
from app.documents.mail import write_mail_draft
from app.documents.payslip import write_payslip
from app.documents.workbook import write_workbook
from app.hr.contracts import load_contracts
from app.issues import BLOCK
from app.payroll.engine import calculate
from app.payroll.inputs import build_inputs
from app.policy import load_policy
from app.xlsx import InputError

FILES = ["employees.xlsx", "caps_events.xlsx", "schedule.xlsx", "class_changes.xlsx", "allowances.xlsx", "policy.yaml"]
OPTIONAL = ["attendance_corrections.xlsx"]


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def run(month, input_dir, output_dir):
    year, mon = (int(x) for x in month.split("-"))
    p = lambda name: os.path.join(input_dir, name)
    try:
        missing = [f for f in FILES if not os.path.exists(p(f))]
        if missing:
            raise InputError(f"입력 폴더 {input_dir}에 파일 없음: {', '.join(missing)}")
        policy = load_policy(p("policy.yaml"))
        contracts = load_contracts(p("employees.xlsx"))
        events, issues = load_events(p("caps_events.xlsx"), set(contracts))
        corr = p(OPTIONAL[0]) if os.path.exists(p(OPTIONAL[0])) else None
        attendance, i2 = summarize_month(events, corr, contracts, policy, year, mon)
        teaching, i3 = compute_teaching(p("schedule.xlsx"), p("class_changes.xlsx"), contracts, policy, year, mon)
        inputs, i4 = build_inputs(contracts, attendance, teaching, p("allowances.xlsx"), year, mon)
        statements, i5 = calculate(inputs, contracts, policy)
    except InputError as e:
        print(f"[입력 오류] {e}", file=sys.stderr)
        return 1
    issues = issues + i2 + i3 + i4 + i5
    blocked = sorted({i.employee_id for i in issues if i.category == BLOCK})

    assumptions = ["소득세·4대보험 공제는 계산하지 않음 (원장님 인터뷰 A5 이후 결정)",
                   "연장·휴일 가산수당, 주휴수당은 계산하지 않음 (법정 검토 필요)"]
    if not policy.min_hourly_confirmed:
        assumptions.append(f"최저시급 {policy.min_hourly:,.0f}원은 확인 전 값")
    if not policy.substitute_confirmed:
        assumptions.append("대체 수업 시급 = 대체 강사 본인 시급 (원장님 확인 전)")
    assumptions.append(f"1시수 = {policy.session_minutes}분, 원 단위 미만 {'절사' if policy.rounding == 'floor_won' else '반올림'}")

    os.makedirs(os.path.join(output_dir, "명세서"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "메일초안"), exist_ok=True)
    write_workbook(os.path.join(output_dir, f"급여계산표_{month}.xlsx"), statements, attendance, issues, blocked)
    for emp, s in statements.items():
        write_payslip(os.path.join(output_dir, "명세서", f"{emp}_{month}.pdf"), s, month)
        write_mail_draft(os.path.join(output_dir, "메일초안", f"{emp}.txt"), s, month)
    write_issues_md(os.path.join(output_dir, f"확인필요_{month}.md"), month, issues, assumptions)

    totals = {k: int(sum(getattr(s, k) for s in statements.values())) for k in ("gross", "deductions", "net")}
    meta = {
        "month": month, "status": "CALCULATED", "run_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {f: _sha(p(f)) for f in FILES + OPTIONAL if os.path.exists(p(f))},
        "policy": {"min_hourly": str(policy.min_hourly), "substitute_rate": policy.substitute_rate,
                   "rounding": policy.rounding, "session_minutes": policy.session_minutes},
        "employees": {e: {"gross": int(s.gross), "deductions": int(s.deductions), "net": int(s.net)} for e, s in statements.items()},
        "blocked": blocked, "totals": totals, "issue_count": len(issues),
        "note": "CALCULATED = 계산만 완료. 확정·공개·지급은 사람이 한다.",
    }
    with open(os.path.join(output_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"{month} 급여 계산 완료 — 명세서 {len(statements)}명, 계산 중단 {len(blocked)}명, 확인 필요 {len(issues)}건")
    print(f"지급 {totals['gross']:,}원 · 공제 {totals['deductions']:,}원 · 실지급 {totals['net']:,}원")
    if blocked:
        print(f"[계산 중단] {', '.join(blocked)} — 확인필요_{month}.md 참고")
    print(f"결과: {output_dir}")
    return 2 if blocked else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="학원 급여 계산 프로토타입")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--month", required=True, help="YYYY-MM")
    r.add_argument("--input", required=True)
    r.add_argument("--output", required=True)
    a = ap.parse_args(argv)
    return run(a.month, a.input, a.output)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
