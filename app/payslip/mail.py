"""메일 초안(.eml, PDF 첨부). 본문에 금액 없음. 이 프로그램은 발송하지 않는다."""
import os
from email.message import EmailMessage


def write_eml(path, slip, company, pdf_path):
    y, m = slip.month.split("-")
    msg = EmailMessage()
    msg["From"] = company.mail_from
    msg["To"] = slip.email
    msg["Subject"] = f"[{company.name}] {y}년 {int(m)}월 급여명세서"
    msg["X-Unsent"] = "1"          # Outlook에서 열면 보내기 전 초안으로 열림
    msg.set_content(
        f"{slip.name}님, 안녕하세요.\n\n"
        f"{int(m)}월 급여명세서를 첨부해 드립니다.\n"
        "첨부 파일에서 지급·공제 내역을 확인해 주세요.\n\n"
        f"{company.contact}\n\n"
        f"{company.name} 드림\n"
    )
    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))
    with open(path, "wb") as f:
        f.write(bytes(msg))
