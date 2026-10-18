"""직원별 급여명세서 PDF (A4 1장). PDF는 출력 형식일 뿐 급여 원장이 아니다."""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle

from app.payroll.engine import describe

FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_registered = False


def _fonts():
    global _registered
    if not _registered:
        pdfmetrics.registerFont(TTFont("Malgun", os.path.join(FONT_DIR, "malgun.ttf")))
        pdfmetrics.registerFont(TTFont("MalgunBd", os.path.join(FONT_DIR, "malgunbd.ttf")))
        _registered = True


def write_payslip(path, statement, month, org="우리컴퓨터학원"):
    _fonts()
    navy = colors.HexColor("#1A3A5C")
    title = ParagraphStyle("t", fontName="MalgunBd", fontSize=16, textColor=navy, spaceAfter=4)
    body = ParagraphStyle("b", fontName="Malgun", fontSize=9.5, leading=14)
    small = ParagraphStyle("s", fontName="Malgun", fontSize=8, leading=11, textColor=colors.HexColor("#666666"))
    cell = ParagraphStyle("c", fontName="Malgun", fontSize=8.5, leading=11)

    y, m = month.split("-")
    story = [
        Paragraph(f"{int(y)}년 {int(m)}월 급여명세서", title),
        Paragraph(f"{org} · {statement.name} ({statement.employee_id})", body),
        Spacer(1, 6 * mm),
    ]
    rows = [["항목", "구분", "계산", "금액(원)", "근거"]]
    for l in statement.lines:
        rows.append([Paragraph(l.item, cell), l.side, Paragraph(describe(l), cell),
                     f"{l.amount:,.0f}", Paragraph(l.basis, cell)])
    rows += [["지급 합계", "", "", f"{statement.gross:,.0f}", ""],
             ["공제 합계", "", "", f"{statement.deductions:,.0f}", ""],
             ["실지급액", "", "", f"{statement.net:,.0f}", ""]]
    t = Table(rows, colWidths=[28 * mm, 12 * mm, 48 * mm, 24 * mm, 58 * mm], repeatRows=1)
    n = len(rows)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Malgun", 8.5),
        ("FONT", (0, 0), (-1, 0), "MalgunBd", 9),
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D7DE")),
        ("BACKGROUND", (0, n - 3), (-1, -1), colors.HexColor("#E6F1FB")),
        ("FONT", (0, n - 1), (-1, n - 1), "MalgunBd", 10),
    ]))
    story += [t, Spacer(1, 6 * mm),
              Paragraph("※ 소득세·4대보험 공제는 이 명세서에 반영되지 않았습니다(별도 처리).", small),
              Paragraph("※ 프로토타입 출력물 — 가상 데이터로 생성되었으며 실제 지급 근거가 아닙니다.", small)]
    SimpleDocTemplate(path, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=18 * mm, bottomMargin=18 * mm, title=f"{month} 급여명세서").build(story)
