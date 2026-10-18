"""월급명세서 HTML — 실물 양식(A4, pt 좌표)을 그대로 재현. 이미지는 base64로 넣어 HTML 하나로 완결."""
import base64
import html
import os

ROW_H = 20.3   # 항목 행 높이(pt) — 실물 측정값


def _img(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def _won(v):
    return "-" if v is None else f"{v:,.0f}"


def _card(left, icon, title, rows, total_label, total, c):
    body = []
    for i, (label, amount) in enumerate(rows):
        top = 61 + i * ROW_H
        body.append(f'<div class="cell lbl" style="top:{top}pt">{html.escape(label)}</div>'
                    f'<div class="cell amt" style="top:{top}pt">{_won(amount)}</div>')
    return f"""
<div class="card" style="left:{left}pt">
  <div class="ico">{icon}</div><div class="ctitle">{title}</div>
  <div class="thead"><span class="th1">항목</span><span class="th2">금액(원)</span></div>
  <div class="vline"></div>
  {''.join(body)}
  <div class="tot"><span class="tlbl">{total_label}</span><span class="tamt">{_won(total)}</span></div>
</div>"""


def render_html(slip, company, base_dir=None):
    c = company
    e = html.escape
    info_l = [("성명", slip.name), ("사원번호", slip.employee_no), ("직책", slip.title), ("생년월일", slip.birth)]
    info_r = [("지급년월", slip.month_label), ("지급일", slip.pay_date), ("입사일", slip.hired), ("지급구분", slip.kind)]
    info = "".join(
        f'<div class="lab" style="left:{lx}pt;top:{95 + i * 19}pt">{e(k)}</div>'
        f'<div class="val" style="left:{vx}pt;top:{95 + i * 19}pt">{e(v)}</div>'
        for col, (lx, vx) in ((info_l, (259, 311)), (info_r, (415, 468))) for i, (k, v) in enumerate(col))
    note = f"비고: {e(slip.note)}" if slip.note else "비고: -"
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>{e(slip.name)}_급여명세서_{slip.month}</title>
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Malgun Gothic', '맑은 고딕', sans-serif; color: #111827; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ position: relative; width: 595.28pt; height: 841.89pt; overflow: hidden; background: #fff; }}
.page > div, .card > div {{ position: absolute; }}
.title {{ top: 14pt; left: 0; width: 100%; text-align: center; font-size: 25.5pt; font-weight: 700; color: {c.primary}; letter-spacing: .12em; }}
.sub {{ top: 52pt; left: 0; width: 100%; text-align: center; font-size: 9.7pt; font-weight: 700; color: {c.accent}; letter-spacing: .55em; }}
.rule {{ top: 83pt; left: 36pt; width: 524pt; height: 1pt; background: #e6ebf2; }}
.logo {{ top: 104pt; left: 36pt; width: 56pt; height: 56pt; }}
.logo img {{ width: 100%; height: 100%; }}
.cname {{ top: 96pt; left: 100pt; font-size: 10.5pt; font-weight: 700; }}
.cinfo {{ left: 100pt; font-size: 9pt; color: #4b5563; }}
.divider {{ top: 98pt; left: 240pt; width: 1pt; height: 69pt; background: #e4e9f1; }}
.lab {{ font-size: 9pt; font-weight: 700; color: {c.primary}; }}
.val {{ font-size: 9pt; color: #111827; }}
.card {{ top: 184pt; width: 258pt; height: 297pt; border: .75pt solid #e1e7f0; background: #fff; }}
.ico {{ top: 10pt; left: 16pt; width: 19pt; height: 19pt; border-radius: 50%; background: {c.accent}; color: #fff; font-size: 10.5pt; font-weight: 700; text-align: center; line-height: 19pt; }}
.ctitle {{ top: 8pt; left: 44pt; font-size: 13.5pt; font-weight: 700; color: {c.primary}; }}
.thead {{ top: 36pt; left: 0; width: 100%; height: 24pt; background: #f4f6fa; border-top: .75pt solid #e1e7f0; border-bottom: .75pt solid #e1e7f0; font-size: 9.7pt; font-weight: 700; color: {c.head_text}; }}
.thead span {{ position: absolute; top: 5pt; text-align: center; }}
.th1 {{ left: 0; width: 129pt; }} .th2 {{ left: 129pt; width: 129pt; }}
.vline {{ top: 36pt; left: 129pt; width: .75pt; height: 260pt; background: #e1e7f0; }}
.cell {{ font-size: 9.7pt; height: {ROW_H}pt; line-height: {ROW_H}pt; }}
.lbl {{ left: 16pt; width: 112pt; color: #374151; white-space: nowrap; }}
.amt {{ left: 129pt; width: 112pt; text-align: right; color: #111827; }}
.tot {{ top: 263pt; left: 0; width: 100%; height: 33pt; background: #fbfcfe; border-top: .75pt solid #e1e7f0; }}
.tlbl {{ position: absolute; left: 16pt; top: 5pt; font-size: 13.5pt; font-weight: 700; color: {c.primary}; }}
.tamt {{ position: absolute; right: 16pt; top: 3pt; font-size: 15.7pt; font-weight: 700; color: {c.primary}; }}
.net {{ top: 490pt; left: 36pt; width: 524pt; height: 42pt; background: {c.primary}; color: #fff; }}
.net > span {{ position: absolute; }}
.nlbl {{ left: 18pt; top: 7pt; font-size: 16.5pt; font-weight: 700; }}
.nsub {{ left: 130pt; top: 12pt; font-size: 9.7pt; }}
.namt {{ right: 22pt; top: 4pt; font-size: 21.7pt; font-weight: 700; }}
.nwon {{ margin-left: 10pt; }}
.infobox {{ top: 544pt; left: 37pt; width: 521pt; height: 82pt; border: .75pt solid #e1e7f0; }}
.infobox > div {{ position: absolute; }}
.iico {{ top: 21pt; left: 16pt; width: 41pt; height: 40pt; border-radius: 8pt; background: #f1f3f8; color: {c.accent}; font-size: 18.7pt; font-weight: 700; text-align: center; line-height: 40pt; }}
.ititle {{ top: 22pt; left: 67pt; font-size: 12pt; font-weight: 700; color: {c.primary}; line-height: 16pt; }}
.itext {{ top: 9pt; left: 121pt; width: 392pt; font-size: 9.7pt; color: #374151; line-height: 15pt; }}
.itext p + p {{ margin-top: 12pt; }}
.thanks {{ top: 638pt; left: 36pt; width: 524pt; height: 30pt; background: #f4f6fa; text-align: center; line-height: 30pt; font-size: 10.5pt; font-weight: 700; color: {c.primary}; }}
.sign {{ top: 742pt; left: 0; width: 100%; text-align: center; font-size: 16pt; font-weight: 700; letter-spacing: .18em; color: #1f2937; }}
.seal {{ top: 722pt; left: 334pt; width: 62pt; height: 62pt; opacity: .85; }}   /* 회사명 끝에 겹치게 (실물과 같은 배치) */
.seal img {{ width: 100%; height: 100%; }}
</style></head>
<body><div class="page">
  <div class="title">월 급 명 세 서</div>
  <div class="sub">PAY STATEMENT</div>
  <div class="rule"></div>
  <div class="logo"><img src="{_img(c.logo_path)}" alt="{e(c.name)} 로고"></div>
  <div class="cname">{e(c.name)}</div>
  <div class="cinfo" style="top:119pt">사업자등록번호</div>
  <div class="cinfo" style="top:134pt">{e(c.business_no)}</div>
  <div class="cinfo" style="top:149pt">대표자&nbsp;&nbsp;{e(c.ceo)}</div>
  <div class="divider"></div>
  {info}
  {_card(36, "₩", "지급내역", slip.pay_rows(), "지급총액", slip.gross, c)}
  {_card(302, "−", "공제내역", slip.deduction_rows(), "공제총액", slip.deductions, c)}
  <div class="net"><span class="nlbl">실지급액</span><span class="nsub">지급총액 - 공제총액</span>
    <span class="namt">{_won(slip.net)}<span class="nwon">원</span></span></div>
  <div class="infobox"><div class="iico">□</div><div class="ititle">근태 및<br>기타정보</div>
    <div class="itext"><p>{note}</p><p>{e(c.contact)}</p></div></div>
  <div class="thanks">{e(c.thanks)}</div>
  <div class="sign">{e(c.name)}</div>
  <div class="seal"><img src="{_img(c.seal_path)}" alt="직인"></div>
</div></body></html>"""
