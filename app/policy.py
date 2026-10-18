"""급여 정책 파일(policy.yaml). 확정되지 않은 값은 confirmed: false 로 둔다."""
from dataclasses import dataclass
from datetime import time
from decimal import Decimal

import yaml

from app.money import D


@dataclass(frozen=True)
class Policy:
    min_hourly: Decimal
    min_hourly_confirmed: bool
    session_minutes: int
    rounding: str
    substitute_rate: str          # substitute_own: 대체 강사 본인 시급
    substitute_confirmed: bool
    late_after: time
    max_daily_hours: Decimal


def load_policy(path) -> Policy:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    h, m = (int(x) for x in str(raw["late_after"]).split(":"))
    return Policy(
        min_hourly=D(raw["min_hourly"]["value"]),
        min_hourly_confirmed=bool(raw["min_hourly"]["confirmed"]),
        session_minutes=int(raw["session_minutes"]),
        rounding=raw["rounding"],
        substitute_rate=raw["substitute_rate"]["value"],
        substitute_confirmed=bool(raw["substitute_rate"]["confirmed"]),
        late_after=time(h, m),
        max_daily_hours=D(raw["max_daily_hours"]),
    )
