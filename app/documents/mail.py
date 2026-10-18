"""메일 초안. 금액은 절대 넣지 않는다(PROJECT_SPEC 14.3) — 상세는 명세서·포털에서 확인. 발송하지 않음."""


def write_mail_draft(path, statement, month, org="우리컴퓨터학원"):
    y, m = month.split("-")
    body = (
        f"받는 사람: {statement.email}\n"
        f"제목: [{org}] {int(y)}년 {int(m)}월 급여명세서 안내\n"
        "\n"
        f"{statement.name} 선생님, 안녕하세요.\n"
        f"{int(m)}월 급여명세서가 준비되었습니다.\n"
        "첨부한 명세서에서 항목별 계산 근거를 확인해 주시고, 문의 사항은 원장님께 말씀해 주세요.\n"
        "\n"
        f"{org} 드림\n"
        "\n"
        "--- (초안 — 원장님 확인 후 발송. 이 프로그램은 메일을 보내지 않습니다) ---\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
