from decimal import Decimal

from app.money import D, round_amount
from app.policy import load_policy


def test_floor_won_drops_fraction():
    assert round_amount(D("1199000.9"), "floor_won") == Decimal("1199000")


def test_round_won():
    assert round_amount(D("10.5"), "round_won") == Decimal("11")


def test_policy_loads_sample():
    p = load_policy("samples/2026-09/policy.yaml")
    assert p.min_hourly == Decimal("10320")
    assert p.substitute_confirmed is False
    assert p.late_after.hour == 9
