"""사람이 판단해야 할 항목. 조용히 넘어가지 않고 전부 여기에 모은다."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

DATA = "데이터 이상"
RULE = "규칙 미확정"
LEGAL = "법정 검토"
BLOCK = "계산 중단"


@dataclass(frozen=True)
class Issue:
    category: str
    employee_id: Optional[str]
    day: Optional[date]
    message: str
