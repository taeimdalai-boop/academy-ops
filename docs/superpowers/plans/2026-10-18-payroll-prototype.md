# 학원 급여 자동화 프로토타입 — 구현 계획서

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 가상 9월 입력 파일로 직원별 급여를 계산해 계산표·명세서·메일 초안·확인 필요 목록을 만드는 파이썬 프로그램과 `/payroll` 스킬.

**Architecture:** 모듈(인사·근태·수업·급여·문서)을 PROJECT_SPEC 경계대로 나눈다. 근태·수업 결과는 `PayrollInput`(표준 급여 입력)으로 바뀌고, 계산 엔진은 그것과 정책만 본다. 캡스 전용 코드는 연결기 폴더에만 둔다.

**Tech Stack:** Python 3.14, openpyxl, PyYAML, reportlab(맑은 고딕 TTF), pytest

**설계서:** `docs/superpowers/specs/2026-10-18-payroll-prototype-design.md`

## Global Constraints

- 금액은 `decimal.Decimal`. 반올림 = 정책 `rounding: floor_won`(원 단위 미만 절사).
- 계산 엔진(`app/payroll/engine.py`)은 엑셀 파일을 읽지 않는다 — `PayrollInput` 목록과 `Contract`·`Policy`만 받는다.
- 캡스 모드 번호 변환은 `app/attendance/connectors/adt_caps/mapper.py`에만 둔다.
- 메일 초안 본문에 숫자 금액(예: `1,560,000`, `원`) 없음.
- 최저시급 미달 직원은 명세서를 만들지 않고 CLI 종료 코드 2.
- 실명·연락처는 가상값만 사용(강사A, `t01@example.com`).
- 실행: `python -m app.cli run --month 2026-09 --input samples/2026-09 --output out/2026-09`
- 시험: `python -m pytest -q` (작업 폴더 `academy-ops/`)

---

## 가상 데이터와 손계산 정답 (모든 시험의 기준)

**정책** `min_hourly: 10320`(2026 최저시급, 확인 필요 표시) · `session_minutes: 60` · `substitute_rate: substitute_own`(`confirmed: false`) · `late_after: "09:00"` · `max_daily_hours: 8`

| ID | 이름 | 형태 | 단가 | 입력 사실 | 지급 | 공제 | 실지급 |
|:--|:--|:--|--:|:--|--:|--:|--:|
| T01 | 강사A | 시수제 | 30,000 | 월·수·금 4시수(52) − 9/16 휴강 4 + 9/17 보강 4 = 52시수, 인센티브 200,000 | 1,760,000 | 0 | 1,760,000 |
| T02 | 강사B | 시수제 | 32,000 | 화·목 3시수(27) − 9/10 대체로 빠짐 3 = 24시수, AI지원금 100,000 | 868,000 | 0 | 868,000 |
| T03 | 강사C | 시수제 | 28,000 | 토 5시수(20) + 9/10 대체 3 = 23시수, 가불 공제 100,000 | 644,000 | 100,000 | 544,000 |
| T04 | 강사D | 시수제 | 9,000 | 화 2시수(10) — **최저시급 미달 → 계산 중단** | — | — | — |
| A01 | 행정A | 월급제 | 2,500,000 / 209h | 지각 9/3·9/17 (공제 안 함, 확인 필요) | 2,500,000 | 0 | 2,500,000 |
| A02 | 행정B | 시간제 | 11,000 | 평일 22일 × 13~18시 5h = 110h, 9/22 퇴근 누락(0h) −5, 9/9 외출 30분 −0.5, 9/29 09:00~18:30(9.5h) +4.5 → **109h** (9/15 퇴근 누락은 보정 파일로 18:00) | 1,199,000 | 0 | 1,199,000 |

합계: 지급 6,971,000 · 공제 100,000 · 실지급 6,871,000

**반드시 나와야 할 확인 필요 항목**: 대체 시급 가정(9/10) · 존재하지 않는 수업 S999 변경 · 캡스 미등록 사원번호 9999 · A02 9/22 퇴근 누락 · A02 9/29 8시간 초과 · A01 지각 2일 · T04 최저시급 미달 · 세금·4대보험 미반영

---

## File Structure

| 파일 | 책임 |
|:--|:--|
| `app/money.py` | `D()`, `round_amount()` |
| `app/policy.py` | `Policy` dataclass, `load_policy()` |
| `app/issues.py` | `Issue` dataclass, 분류 상수 |
| `app/xlsx.py` | 시트를 dict 행 목록으로 읽기 + 필수 열 검사 |
| `app/hr/contracts.py` | `Contract`, `load_contracts()` |
| `app/attendance/model.py` | `AttendanceEvent`, 이벤트 종류 상수 |
| `app/attendance/connectors/adt_caps/mapper.py` | 캡스 모드 → 표준 종류 |
| `app/attendance/connectors/adt_caps/connector.py` | 캡스 엑셀 → 이벤트 + 이슈 |
| `app/attendance/connectors/adt_caps/config.yaml` | 캡스 열 이름 설정 |
| `app/attendance/daily.py` | 일별 근태·월 집계 |
| `app/classes/teaching.py` | 시간표 + 변경 → 강사별 시수 줄 |
| `app/payroll/inputs.py` | `PayrollInput`, `build_inputs()` |
| `app/payroll/engine.py` | `Statement`, `calculate()` |
| `app/documents/workbook.py` · `payslip.py` · `mail.py` · `issues_md.py` | 결과물 4종 |
| `app/cli.py` | 전체 실행, `run.json` |
| `tools/make_samples.py` | 가상 데이터 생성 |
| `samples/2026-09/*` | 입력 + `expected.json` |
| `.claude/skills/payroll/SKILL.md` (상위 `SaaS개발/`) | 스킬 |

---

### Task 1: 공통 기반 + 가상 데이터

**Files:** Create `app/__init__.py`, `app/money.py`, `app/policy.py`, `app/issues.py`, `app/xlsx.py`, `tools/make_samples.py`, `samples/2026-09/*`, `tests/test_money_policy.py`

**Interfaces — Produces:**
- `D(x) -> Decimal` · `round_amount(amount: Decimal, rule: str) -> Decimal` (`floor_won`, `round_won`)
- `Policy(min_hourly: Decimal, min_hourly_confirmed: bool, session_minutes: int, rounding: str, substitute_rate: str, substitute_confirmed: bool, late_after: time, max_daily_hours: Decimal)` · `load_policy(path) -> Policy`
- `Issue(category: str, employee_id: str|None, day: date|None, message: str)` · 분류 `DATA`(데이터 이상)·`RULE`(규칙 미확정)·`LEGAL`(법정 검토)·`BLOCK`(계산 중단)
- `read_rows(path, required: list[str]) -> list[dict]` — 열 없으면 `InputError("파일명: 열 '<이름>' 없음")`

- [ ] **Step 1: 실패하는 시험 작성**

```python
from decimal import Decimal
from app.money import D, round_amount
from app.policy import load_policy

def test_floor_won_drops_fraction():
    assert round_amount(D("1199000.9"), "floor_won") == Decimal("1199000")

def test_policy_loads_sample():
    p = load_policy("samples/2026-09/policy.yaml")
    assert p.min_hourly == Decimal("10320")
    assert p.substitute_confirmed is False
    assert p.late_after.hour == 9
```

- [ ] **Step 2:** `python -m pytest tests/test_money_policy.py -q` → FAIL (모듈 없음)
- [ ] **Step 3:** 위 인터페이스대로 구현 + `tools/make_samples.py`로 위 표의 가상 데이터 6개 파일과 `expected.json` 생성
- [ ] **Step 4:** 시험 PASS 확인
- [ ] **Step 5:** `git commit -m "feat: money, policy, samples"`

### Task 2: 인사(계약) 읽기

**Files:** Create `app/hr/__init__.py`, `app/hr/contracts.py`, `tests/test_contracts.py`

**Interfaces — Produces:** `Contract(employee_id, name, role, pay_type, hourly_rate: Decimal|None, monthly_salary: Decimal|None, monthly_hours: Decimal|None, start: date, end: date|None, email)` · `Contract.effective_hourly() -> Decimal` (월급제는 월급÷월 소정시간) · `Contract.active_on(d: date) -> bool` · `load_contracts(path) -> dict[str, Contract]`

```python
from decimal import Decimal
from datetime import date
from app.hr.contracts import load_contracts

def test_contracts():
    c = load_contracts("samples/2026-09/employees.xlsx")
    assert set(c) == {"T01","T02","T03","T04","A01","A02"}
    assert c["T01"].pay_type == "시수제" and c["T01"].hourly_rate == Decimal("30000")
    assert c["A01"].effective_hourly().quantize(Decimal("1")) == Decimal("11962")
    assert c["T01"].active_on(date(2026, 9, 1))
```

- [ ] 시험 작성 → FAIL → 구현 → PASS → commit `feat: hr contracts`

### Task 3: 캡스 연결기

**Files:** Create `app/attendance/__init__.py`, `model.py`, `connectors/__init__.py`, `connectors/adt_caps/{__init__,mapper,connector}.py`, `config.yaml`, `tests/test_caps.py`

**Interfaces:** Consumes `read_rows`, `Issue`. Produces `AttendanceEvent(employee_id: str, at: datetime, kind: str)`; kinds `CHECK_IN, CHECK_OUT, BREAK_OUT, BREAK_IN, ACCESS, MEAL`; `MODE_MAP = {1:CHECK_IN, 2:CHECK_OUT, 3:BREAK_OUT, 4:BREAK_IN, 5:ACCESS, 6..10:MEAL}`; `load_events(path, known_ids: set[str]) -> tuple[list[AttendanceEvent], list[Issue]]` — 같은 사람·종류·분 중복 1건으로, 미등록 사원번호는 제외 + `DATA` 이슈

```python
from app.attendance.connectors.adt_caps.connector import load_events
from app.attendance.connectors.adt_caps.mapper import to_kind

def test_mode_map():
    assert to_kind(1) == "CHECK_IN" and to_kind(7) == "MEAL"

def test_load_events_dedup_and_unknown():
    ev, issues = load_events("samples/2026-09/caps_events.xlsx", {"A01","A02"})
    a02_0902_in = [e for e in ev if e.employee_id=="A02" and e.at.day==2 and e.kind=="CHECK_IN"]
    assert len(a02_0902_in) == 1
    assert any("9999" in i.message for i in issues)
```

- [ ] 시험 작성 → FAIL → 구현 → PASS → commit `feat: adt caps connector`

### Task 4: 일별 근태·월 집계

**Files:** Create `app/attendance/daily.py`, `tests/test_daily.py`

**Interfaces:** Produces `DailyRecord(day, check_in, check_out, break_minutes, work_minutes, note)` · `MonthlyAttendance(employee_id, days: list[DailyRecord], work_minutes: int, late_days: list[date])` · `summarize_month(events, corrections_path|None, contracts, policy, year, month) -> tuple[dict[str, MonthlyAttendance], list[Issue]]`. 퇴근 누락 + 보정 없음 → 0분 + `DATA` 이슈. 하루 > `max_daily_hours` → `LEGAL` 이슈. 월급제 지각 → `RULE` 이슈.

```python
from app.attendance.connectors.adt_caps.connector import load_events
from app.attendance.daily import summarize_month
from app.hr.contracts import load_contracts
from app.policy import load_policy

def _run():
    c = load_contracts("samples/2026-09/employees.xlsx")
    p = load_policy("samples/2026-09/policy.yaml")
    ev, _ = load_events("samples/2026-09/caps_events.xlsx", set(c))
    return summarize_month(ev, "samples/2026-09/attendance_corrections.xlsx", c, p, 2026, 9)

def test_a02_hours_109():
    att, _ = _run()
    assert att["A02"].work_minutes == 109 * 60

def test_issues_present():
    att, issues = _run()
    msgs = " ".join(i.message for i in issues)
    assert "퇴근" in msgs and "8시간" in msgs and "지각" in msgs
    assert len(att["A01"].late_days) == 2
```

- [ ] 시험 작성 → FAIL → 구현 → PASS → commit `feat: daily attendance`

### Task 5: 수업 시수

**Files:** Create `app/classes/__init__.py`, `teaching.py`, `tests/test_teaching.py`

**Interfaces:** Produces `TeachingLine(employee_id, kind: "REGULAR"|"SUBSTITUTE"|"MAKEUP", hours: Decimal, basis: str)` · `compute_teaching(schedule_path, changes_path, contracts, policy, year, month) -> tuple[list[TeachingLine], list[Issue]]`. 휴강·대체는 존재하는 수업ID만, 없으면 `DATA` 이슈. 대체 건마다 `substitute_confirmed`가 False면 `RULE` 이슈.

```python
from decimal import Decimal
from app.classes.teaching import compute_teaching
from app.hr.contracts import load_contracts
from app.policy import load_policy

def _hours(lines, emp):
    return sum((l.hours for l in lines if l.employee_id == emp), Decimal(0))

def test_hours():
    c = load_contracts("samples/2026-09/employees.xlsx"); p = load_policy("samples/2026-09/policy.yaml")
    lines, issues = compute_teaching("samples/2026-09/schedule.xlsx", "samples/2026-09/class_changes.xlsx", c, p, 2026, 9)
    assert _hours(lines, "T01") == 52 and _hours(lines, "T02") == 24 and _hours(lines, "T03") == 23
    assert any("S999" in i.message for i in issues)
    assert any(i.category == "RULE" and "대체" in i.message for i in issues)
```

- [ ] 시험 작성 → FAIL → 구현 → PASS → commit `feat: teaching hours`

### Task 6: 표준 급여 입력 + 계산 엔진

**Files:** Create `app/payroll/__init__.py`, `inputs.py`, `engine.py`, `tests/test_engine.py`

**Interfaces:** Produces `PayrollInput(employee_id, source, item, side: "지급"|"공제", quantity: Decimal, unit, unit_rate: Decimal|None, amount: Decimal|None, basis)` · `build_inputs(contracts, attendance, teaching_lines, allowances_path, year, month) -> tuple[list[PayrollInput], list[Issue]]` · `StatementLine(item, side, quantity, unit, unit_rate, amount, basis)` · `Statement(employee_id, name, email, lines, gross, deductions, net)` · `calculate(inputs, contracts, policy) -> tuple[dict[str, Statement], list[Issue]]` (최저시급 미달 직원은 결과에서 빠지고 `BLOCK` 이슈). 대체 시수 단가 = 정책 `substitute_own`이면 대체 강사 본인 시급.

```python
from decimal import Decimal
import json
# (Task 4·5의 로더로 입력을 만든 뒤)
def test_engine_matches_expected(pipeline):   # conftest.py의 fixture가 build_inputs→calculate 결과 반환
    statements, issues = pipeline
    expected = json.load(open("samples/2026-09/expected.json", encoding="utf-8"))
    for emp, e in expected["employees"].items():
        if e.get("blocked"):
            assert emp not in statements
        else:
            assert statements[emp].net == Decimal(e["net"]), emp
    assert any(i.category == "BLOCK" and i.employee_id == "T04" for i in issues)

def test_lines_sum(pipeline):
    for s in pipeline[0].values():
        assert s.gross - s.deductions == s.net
```

- [ ] 시험 작성(+`tests/conftest.py` fixture) → FAIL → 구현 → PASS → commit `feat: payroll inputs and engine`

### Task 7: 결과물 4종 + CLI

**Files:** Create `app/documents/{__init__,workbook,payslip,mail,issues_md}.py`, `app/cli.py`, `tests/test_cli.py`

**Interfaces:** `run(month: str, input_dir: str, output_dir: str) -> int` (0 정상, 2 계산 중단 직원 있음). 출력: `급여계산표_<월>.xlsx`(시트: 요약·명세항목·근태집계·확인필요), `명세서/<ID>_<월>.pdf`, `메일초안/<ID>.txt`, `확인필요_<월>.md`, `run.json`(입력 해시·정책·상태 `CALCULATED`).

```python
import re, os
from app.cli import run

def test_cli_end_to_end(tmp_path):
    code = run("2026-09", "samples/2026-09", str(tmp_path))
    assert code == 2                                   # T04 최저시급 미달
    assert (tmp_path / "급여계산표_2026-09.xlsx").exists()
    pdfs = sorted(os.listdir(tmp_path / "명세서"))
    assert pdfs == ["A01_2026-09.pdf","A02_2026-09.pdf","T01_2026-09.pdf","T02_2026-09.pdf","T03_2026-09.pdf"]
    for f in os.listdir(tmp_path / "메일초안"):
        body = (tmp_path / "메일초안" / f).read_text(encoding="utf-8")
        assert not re.search(r"\d{1,3}(,\d{3})+|\d+\s*원", body)
    md = (tmp_path / "확인필요_2026-09.md").read_text(encoding="utf-8")
    for word in ["S999", "9999", "T04", "대체", "8시간", "지각", "4대보험"]:
        assert word in md
```

- [ ] 시험 작성 → FAIL → 구현 → PASS → 실제 실행해 PDF 한 장 눈으로 확인 → commit `feat: documents and cli`

### Task 8: `/payroll` 스킬

**Files:** Create `D:\우리컴퓨터\SaaS개발\.claude\skills\payroll\SKILL.md`

- [ ] 스킬 작성: 발동 키워드(급여 계산, 급여 돌려줘, /payroll), 입력 폴더 점검 → CLI 실행 → 종료 코드 해석 → 확인 필요 목록 요약 보고 → **발송·확정은 하지 않음** 명시, 챌린지 서식 6항목과 대응
- [ ] 스킬 절차대로 한 번 실행해 보고 결과 확인 → commit `feat: payroll skill`
