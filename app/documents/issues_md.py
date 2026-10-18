"""확인 필요 목록(마크다운). 원장님이 판단해야 할 것만 모은다."""
from app.issues import BLOCK, DATA, LEGAL, RULE

ORDER = [BLOCK, DATA, RULE, LEGAL]


def write_issues_md(path, month, issues, assumptions):
    lines = [f"# {month} 급여 — 확인 필요 목록", "",
             "> 아래 항목은 프로그램이 판단하지 않고 사람에게 넘긴 것입니다. 확인 후 입력 파일·정책을 고치고 다시 실행하세요.", ""]
    for cat in ORDER:
        items = [i for i in issues if i.category == cat]
        if not items:
            continue
        lines += [f"## {cat} ({len(items)}건)", ""]
        for i in items:
            who = f"[{i.employee_id}] " if i.employee_id else ""
            when = f"{i.day.month}/{i.day.day} " if i.day else ""
            lines.append(f"- {who}{when}{i.message}")
        lines.append("")
    lines += ["## 가정·미반영 사항", ""] + [f"- {a}" for a in assumptions] + [""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
