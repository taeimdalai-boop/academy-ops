"""급여 계산 결과(out/<month>/)를 읽어 자체 완결 HTML 대시보드 한 장을 만든다.

사용: python tools/make_dashboard.py out/2026-09 docs/index.html
대시보드는 계산 결과를 '보여주기만' 한다. 계산도 수정도 하지 않는다.
"""
import html
import json
import re
import sys
from pathlib import Path

NAVY, NAVY2, GOLD, INK = "#0a1128", "#101b3d", "#e8b64c", "#1a1a1a"

# 평가자가 설치 없이 바로 열어볼 수 있는 실제 산출물. outputs/ 에 함께 배포한다.
ARTIFACTS = [
    ("명세서 — 강사A", "outputs/payslip_T01_2026-09.pdf", "직원에게 주는 문서 (A4 1장)"),
    ("명세서 — 강사B", "outputs/payslip_T02_2026-09.pdf", ""),
    ("명세서 — 강사C", "outputs/payslip_T03_2026-09.pdf", ""),
    ("명세서 — 행정A", "outputs/payslip_A01_2026-09.pdf", ""),
    ("명세서 — 행정B", "outputs/payslip_A02_2026-09.pdf", ""),
    ("계산근거 — 강사A", "outputs/basis_T01_2026-09.pdf", "금액이 어떻게 나왔는지 검산하는 내부 자료"),
    ("급여계산표", "outputs/payroll_2026-09.xlsx", "요약·명세항목·근태집계·확인필요 4시트"),
    ("확인 필요 목록", "outputs/issues_2026-09.md", "사람에게 넘긴 항목 전문"),
    ("실행 기록", "outputs/run.json", "입력 파일 해시·정책값·합계"),
]


LABELS = {
    "substitute_own": "대체 강사 본인 시급",
    "substitute_original": "원 담당 강사 시급",
    "floor_won": "원 단위 미만 절사",
    "round_won": "원 단위 반올림",
}


def label(v):
    return LABELS.get(str(v), str(v))


def won(n):
    return f"{int(n):,}원"


def parse_issues(md_path):
    """확인필요_*.md를 ## 섹션 단위로 쪼갠다."""
    if not md_path.exists():
        return []
    sections, cur = [], None
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            cur = {"title": m.group(1).strip(), "items": []}
            sections.append(cur)
        elif cur is not None and line.strip().startswith("- "):
            cur["items"].append(line.strip()[2:].strip())
    return [s for s in sections if s["items"]]


def strip_md(s):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s)


def build(out_dir: Path, dst: Path):
    run = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    month = run["month"]
    emps = run["employees"]
    totals = run["totals"]
    policy = run["policy"]
    blocked = run.get("blocked", [])
    issues = parse_issues(out_dir / f"확인필요_{month}.md")

    rows = "".join(
        f"<tr><td class=id>{html.escape(k)}</td>"
        f"<td class=n>{won(v['gross'])}</td>"
        f"<td class=n>{won(v['deductions'])}</td>"
        f"<td class='n net'>{won(v['net'])}</td></tr>"
        for k, v in sorted(emps.items())
    )
    for b in blocked:
        rows += (
            f"<tr class=blocked><td class=id>{html.escape(b)}</td>"
            f"<td class=stop colspan=3>계산 중단 — 명세서 미생성</td></tr>"
        )

    artifact_html = "".join(
        '<li><a href="{}"><span class=nm>{}</span>{}<span class=ex>{}</span></a></li>'.format(
            href, html.escape(name),
            f'<span class=ds>{html.escape(desc)}</span>' if desc else "",
            href.rsplit(".", 1)[-1].upper())
        for name, href, desc in ARTIFACTS
    )

    issue_html = "".join(
        "<section class=issue><h3>{}</h3><ul>{}</ul></section>".format(
            html.escape(s["title"]),
            "".join(f"<li>{html.escape(strip_md(i))}</li>" for i in s["items"]),
        )
        for s in issues
    )

    doc = f"""<!doctype html>
<html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>급여 계산 결과 {month}</title>
<style>
:root{{--navy:{NAVY};--navy2:{NAVY2};--gold:{GOLD};--ink:{INK};--line:#d8d8d8;--bg:#fbfbfa}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:"맑은 고딕","Malgun Gothic",system-ui,sans-serif;line-height:1.65}}
.wrap{{max-width:900px;margin:0 auto;padding:0 16px 72px}}
header{{background:var(--navy);color:#fff;padding:36px 0 30px;margin-bottom:34px}}
header .wrap{{padding-bottom:0}}
.kicker{{color:var(--gold);font-size:13px;letter-spacing:.14em;margin:0 0 6px}}
h1{{margin:0;font-size:27px;letter-spacing:-.02em}}
.sub{{margin:10px 0 0;color:#b9c2d6;font-size:14px}}
h2{{font-size:17px;margin:40px 0 14px;padding-bottom:7px;
border-bottom:2px solid var(--navy)}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}
th,td{{padding:9px 10px;border-bottom:1px solid var(--line);font-size:14.5px}}
th{{text-align:right;color:#555;font-size:12.5px;font-weight:600;
border-bottom:2px solid var(--navy)}}
th:first-child{{text-align:left}}
td.id{{font-weight:700;letter-spacing:.03em}}
td.n{{text-align:right;white-space:nowrap}}
th{{white-space:nowrap}}
td.net{{font-weight:700}}
tr.blocked td{{background:#fff6f4}}
td.stop{{text-align:right;color:#a3301c;font-weight:600;font-size:13.5px}}
tfoot td{{border-top:2px solid var(--navy);border-bottom:none;
padding-top:12px;font-weight:700;font-size:15px;white-space:nowrap}}
tfoot td.net{{color:var(--navy)}}
.note{{margin:12px 0 0;font-size:13px;color:#666}}
.files{{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}}
.files li{{border-bottom:1px solid var(--line)}}
.files a{{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline;
padding:10px 2px;text-decoration:none;color:var(--navy2)}}
.files a:hover{{background:#fff}}
.files .nm{{font-weight:700;font-size:14.5px}}
.files .ds{{font-size:13px;color:#666}}
.files .ex{{margin-left:auto;font-size:11.5px;letter-spacing:.08em;color:#8a8a8a}}
.issue{{margin:0 0 20px}}
.issue h3{{font-size:14px;margin:0 0 7px;color:var(--navy2)}}
.issue ul{{margin:0;padding-left:19px}}
.issue li{{font-size:14px;margin-bottom:5px;color:#333}}
.thesis{{border-left:4px solid var(--gold);background:#fff;padding:15px 18px;
margin:0 0 26px;font-size:14.5px}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:5px 18px;margin:0;font-size:14px}}
dt{{color:#666}}dd{{margin:0;font-weight:600}}
footer{{margin-top:48px;padding-top:16px;border-top:1px solid var(--line);
font-size:12.5px;color:#777}}
code{{background:#eceff5;padding:1px 5px;border-radius:3px;font-size:13px}}
@media(max-width:560px){{h1{{font-size:22px}}th,td{{padding:8px 6px;font-size:13.5px}}}}
</style></head><body>
<header><div class=wrap>
<p class=kicker>ACADEMY-OPS · 급여 계산 엔진</p>
<h1>{month} 급여 계산 결과</h1>
<p class=sub>실행 {html.escape(run['run_at'])} · 상태 {html.escape(run['status'])}</p>
</div></header>
<div class=wrap>

<p class=thesis>{html.escape(run.get('note', ''))}</p>

<h2>급여대장</h2>
<table><thead><tr><th>직원</th><th>지급</th><th>공제</th><th>실지급</th></tr></thead>
<tbody>{rows}</tbody>
<tfoot><tr><td>합계 · {len(emps)}명</td>
<td class=n>{won(totals['gross'])}</td>
<td class=n>{won(totals['deductions'])}</td>
<td class='n net'>{won(totals['net'])}</td></tr></tfoot></table>
<p class=note>명세서 PDF {len(emps)}건 · 메일 초안 {len(emps)}건 생성.
메일은 <strong>초안만</strong> 만들고 발송하지 않는다.</p>

<h2>확인 필요 {run.get('issue_count', 0)}건</h2>
{issue_html}

<h2>산출물 — 눌러서 바로 열기</h2>
<ul class=files>{artifact_html}</ul>
<p class=note>아래 파일은 위 계산을 실제로 돌려 나온 것이다. 모두 <strong>가상 샘플 데이터</strong>다.</p>

<h2>적용한 정책값</h2>
<dl>
<dt>최저시급</dt><dd>{won(policy['min_hourly'])}</dd>
<dt>대체강사 시급</dt><dd>{html.escape(label(policy['substitute_rate']))}</dd>
<dt>반올림</dt><dd>{html.escape(label(policy['rounding']))}</dd>
<dt>1시수</dt><dd>{policy['session_minutes']}분</dd>
</dl>

<footer>
이 페이지는 <code>out/{month}/run.json</code>과 <code>확인필요_{month}.md</code>를 읽어
<code>tools/make_dashboard.py</code>가 생성한다. 계산은 CLI가 하고, 이 화면은 결과를 보여주기만 한다.<br>
표시된 수치는 모두 <strong>가상 샘플 데이터</strong>다. 실제 급여 자료가 아니다.
</footer>
</div></body></html>
"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(doc, encoding="utf-8")
    return dst


if __name__ == "__main__":
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "out/2026-09")
    dst = Path(sys.argv[2] if len(sys.argv) > 2 else "docs/index.html")
    print("생성:", build(out_dir, dst))
