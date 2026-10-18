"""가상 9월 입력 데이터 생성. 실명·연락처 없음. 정답은 계획서의 손계산 표와 같다.

실행: python tools/make_samples.py samples/2026-09
"""
import json
import os
import sys
from datetime import date, timedelta

from openpyxl import Workbook

YEAR, MONTH = 2026, 9


def days_in_month():
    d = date(YEAR, MONTH, 1)
    while d.month == MONTH:
        yield d
        d += timedelta(days=1)


def save(path, header, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    wb.save(path)


def employees(out):
    save(os.path.join(out, "employees.xlsx"),
         ["직원ID", "이름", "직군", "급여형태", "시급", "월급", "월소정근로시간", "계약시작", "계약종료", "이메일"],
         [
             ["T01", "강사A", "강사", "시수제", 30000, None, None, date(2026, 3, 1), None, "t01@example.com"],
             ["T02", "강사B", "강사", "시수제", 32000, None, None, date(2026, 3, 1), None, "t02@example.com"],
             ["T03", "강사C", "강사", "시수제", 28000, None, None, date(2026, 3, 1), None, "t03@example.com"],
             ["T04", "강사D", "강사", "시수제", 9000, None, None, date(2026, 9, 1), None, "t04@example.com"],
             ["A01", "행정A", "행정", "월급제", None, 2500000, 209, date(2025, 1, 1), None, "a01@example.com"],
             ["A02", "행정B", "행정", "시간제", 11000, None, None, date(2026, 6, 1), None, "a02@example.com"],
         ])


# 강사별 고정 시간표: 요일(0=월) → (시작, 종료, 시수, 과정)
WEEKLY = {
    "T01": ({0, 2, 4}, "14:00", "18:00", 4, "국비 컴활2급"),
    "T02": ({1, 3}, "19:00", "22:00", 3, "개별 ITQ"),
    "T03": ({5}, "10:00", "15:00", 5, "주말 엑셀"),
    "T04": ({1}, "10:00", "12:00", 2, "개별 한글"),
}


def schedule(out):
    rows = []
    for d in days_in_month():
        for emp, (wdays, start, end, hours, course) in WEEKLY.items():
            if d.weekday() in wdays:
                rows.append([f"S{d:%m%d}-{emp}", d, start, end, course, emp, hours])
    save(os.path.join(out, "schedule.xlsx"), ["수업ID", "날짜", "시작", "종료", "과정", "강사ID", "시수"], rows)


def class_changes(out):
    save(os.path.join(out, "class_changes.xlsx"),
         ["수업ID", "유형", "대체강사ID", "날짜", "시작", "종료", "강사ID", "시수", "비고"],
         [
             ["S0916-T01", "휴강", None, None, None, None, None, None, "강사 개인 사유"],
             ["S0910-T02", "대체", "T03", None, None, None, None, None, "강사B 병가"],
             ["MK0917-T01", "보강", None, date(2026, 9, 17), "14:00", "18:00", "T01", 4, "9/16 휴강분 보강"],
             ["S999", "휴강", None, None, None, None, None, None, "잘못 입력된 수업ID (시험용)"],
         ])


def caps_events(out):
    rows = []

    def ev(emp, name, d, hhmm, mode):
        h, m = (int(x) for x in hhmm.split(":"))
        rows.append([emp, name, f"{d:%Y-%m-%d} {h:02d}:{m:02d}:00", mode, "정문-01"])

    late = {3: "09:12", 17: "09:05"}
    for d in days_in_month():
        if d.weekday() >= 5:
            continue
        # 행정A (월급제): 08:50 출근, 18:00 퇴근, 지각 2일
        ev("A01", "행정A", d, late.get(d.day, "08:50"), 1)
        if d.day == 8:
            ev("A01", "행정A", d, "12:10", 6)          # 식사 기록(급여 무관)
        ev("A01", "행정A", d, "18:00", 2)
        # 행정B (시간제)
        if d.day == 29:
            ev("A02", "행정B", d, "09:00", 1)
            ev("A02", "행정B", d, "18:30", 2)
            continue
        ev("A02", "행정B", d, "13:00", 1)
        if d.day == 2:
            ev("A02", "행정B", d, "13:00", 1)          # 같은 분 중복 태그
        if d.day == 9:
            ev("A02", "행정B", d, "15:00", 3)
            ev("A02", "행정B", d, "15:30", 4)
        if d.day not in (15, 22):                       # 9/15·9/22 퇴근 태그 누락
            ev("A02", "행정B", d, "18:00", 2)
    ev("9999", "미등록", date(2026, 9, 5), "10:00", 5)   # 명부에 없는 사원번호
    save(os.path.join(out, "caps_events.xlsx"), ["사원번호", "이름", "일시", "모드", "단말기"], rows)


def corrections(out):
    save(os.path.join(out, "attendance_corrections.xlsx"),
         ["직원ID", "날짜", "보정출근", "보정퇴근", "사유"],
         [["A02", date(2026, 9, 15), "13:00", "18:00", "퇴근 태그 누락 — 원장 확인"]])


def allowances(out):
    save(os.path.join(out, "allowances.xlsx"),
         ["직원ID", "항목", "구분", "금액", "사유"],
         [
             ["T01", "인센티브", "지급", 200000, "9월 모집 인센티브"],
             ["T02", "AI 지원금", "지급", 100000, "AI 활용 수업 지원"],
             ["T03", "가불 상환", "공제", 100000, "9/5 가불분"],
         ])


POLICY = """# 급여 정책 — 확정되지 않은 값은 confirmed: false (결과에 '가정 사용' 표시)
min_hourly:
  value: 10320          # 2026년 최저시급(원). 고시값 확인 필요
  confirmed: false
session_minutes: 60      # 1시수 = 60분 (인터뷰 B1 미확정)
rounding: floor_won      # 원 단위 미만 절사
substitute_rate:
  value: substitute_own  # 대체 수업 시급 = 대체 강사 본인 시급 (인터뷰 C1 미확정)
  confirmed: false
late_after: "09:00"      # 월급제 지각 기준 시각
max_daily_hours: 8       # 초과 시 법정 검토 표시(가산수당은 계산하지 않음)
"""

EXPECTED = {
    "month": "2026-09",
    "employees": {
        "T01": {"gross": 1760000, "deductions": 0, "net": 1760000},
        "T02": {"gross": 868000, "deductions": 0, "net": 868000},
        "T03": {"gross": 644000, "deductions": 100000, "net": 544000},
        "T04": {"blocked": True},
        "A01": {"gross": 2500000, "deductions": 0, "net": 2500000},
        "A02": {"gross": 1199000, "deductions": 0, "net": 1199000},
    },
    "totals": {"gross": 6971000, "deductions": 100000, "net": 6871000},
}


def main(out):
    os.makedirs(out, exist_ok=True)
    employees(out)
    schedule(out)
    class_changes(out)
    caps_events(out)
    corrections(out)
    allowances(out)
    with open(os.path.join(out, "policy.yaml"), "w", encoding="utf-8") as f:
        f.write(POLICY)
    with open(os.path.join(out, "expected.json"), "w", encoding="utf-8") as f:
        json.dump(EXPECTED, f, ensure_ascii=False, indent=2)
    print("samples written:", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "samples/2026-09")
