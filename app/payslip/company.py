"""명세서 회사 설정(company.yaml): 회사 정보·로고·직인·색상·문구·항목 목록."""
import os
from dataclasses import dataclass

import yaml

from app.xlsx import InputError

MAX_ROWS = 10   # 실물 양식의 항목 행 수


@dataclass(frozen=True)
class Company:
    name: str
    name_en: str
    business_no: str
    ceo: str
    logo_path: str
    seal_path: str
    primary: str
    accent: str
    head_text: str
    thanks: str
    contact: str
    mail_from: str
    pay_items: tuple
    deduction_items: tuple
    pay_day: int = 0        # 다음 달 며칠에 지급하는지. 0이면 명세서에 지급일을 적지 않는다.


def load_company(path) -> Company:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    base = os.path.dirname(os.path.abspath(path))
    pay, ded = tuple(raw["pay_items"]), tuple(raw["deduction_items"])
    for label, items in (("pay_items", pay), ("deduction_items", ded)):
        if len(items) > MAX_ROWS:
            raise InputError(f"company.yaml: {label} {len(items)}개 — 명세서 양식은 최대 {MAX_ROWS}행")
    c = raw["colors"]
    def _asset(key):
        v = raw.get(key)
        return os.path.normpath(os.path.join(base, v)) if v else ""

    return Company(raw["name"], raw.get("name_en", ""), raw["business_no"], raw["ceo"],
                   _asset("logo"), _asset("seal"),
                   c["primary"], c["accent"], c["head_text"], raw["thanks"], raw["contact"], raw["mail_from"], pay, ded, int(raw.get("pay_day", 0)))
