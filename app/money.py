"""금액 계산 공통. 금액은 항상 Decimal로 다룬다(부동소수점 오차 방지)."""
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal


def D(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def round_amount(amount: Decimal, rule: str) -> Decimal:
    """rule: floor_won(원 단위 미만 절사) | round_won(원 단위 반올림)."""
    if rule == "floor_won":
        return amount.quantize(Decimal("1"), rounding=ROUND_FLOOR)
    if rule == "round_won":
        return amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    raise ValueError(f"알 수 없는 반올림 규칙: {rule}")
