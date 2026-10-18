"""캡스 엑셀 내보내기 → 표준 출퇴근 기록."""
import os
from datetime import datetime

import yaml

from app.attendance.connectors.adt_caps.mapper import to_kind
from app.attendance.model import AttendanceEvent
from app.issues import DATA, Issue
from app.xlsx import read_rows

CONFIG = os.path.join(os.path.dirname(__file__), "config.yaml")


def _columns():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)["columns"]


def _to_dt(v) -> datetime:
    return v if isinstance(v, datetime) else datetime.fromisoformat(str(v).strip())


def load_events(path, known_ids):
    """반환: (이벤트 목록, 이슈 목록). 같은 사람·종류·분의 중복은 1건, 미등록 사원번호는 제외."""
    col = _columns()
    rows = read_rows(path, [col["employee_id"], col["timestamp"], col["mode"]])
    events, issues, seen, unknown = [], [], set(), {}
    for r in rows:
        emp = str(r[col["employee_id"]]).strip()
        at = _to_dt(r[col["timestamp"]]).replace(second=0, microsecond=0)
        kind = to_kind(r[col["mode"]])
        if kind is None:
            issues.append(Issue(DATA, emp, at.date(), f"캡스 모드 '{r[col['mode']]}'를 알 수 없어 제외"))
            continue
        if emp not in known_ids:
            unknown.setdefault(emp, at.date())
            continue
        key = (emp, kind, at)
        if key in seen:
            continue
        seen.add(key)
        events.append(AttendanceEvent(emp, at, kind))
    for emp, d in unknown.items():
        issues.append(Issue(DATA, emp, d, f"캡스 사원번호 {emp}가 직원 명부에 없어 기록 제외"))
    events.sort(key=lambda e: (e.employee_id, e.at))
    return events, issues
