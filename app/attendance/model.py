"""표준 출퇴근 기록. 장비(캡스 등)와 무관한 형식 — 근태·급여는 이것만 안다."""
from dataclasses import dataclass
from datetime import datetime

CHECK_IN = "CHECK_IN"
CHECK_OUT = "CHECK_OUT"
BREAK_OUT = "BREAK_OUT"
BREAK_IN = "BREAK_IN"
ACCESS = "ACCESS"
MEAL = "MEAL"


@dataclass(frozen=True)
class AttendanceEvent:
    employee_id: str
    at: datetime
    kind: str
