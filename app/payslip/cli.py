"""급여대장 → 월급명세서 PDF + 메일 초안.

python -m app.payslip.cli --ledger <급여대장.xlsx> --company <company.yaml> --output <폴더>
종료 코드: 0 정상 · 1 입력 오류 · 2 일부 직원 미생성(합계 불일치 등) · 3 Edge 없음(HTML까지만)
"""
import argparse
import os
import sys

from app.payslip.company import load_company
from app.payslip.ledger import load_ledger
from app.payslip.mail import write_eml
from app.payslip.pdf import cleanup_profile, find_edge, html_to_pdf
from app.payslip.render import render_html
from app.xlsx import InputError


def run_payslips(ledger, company_yaml, output):
    try:
        company = load_company(company_yaml)
        slips, issues = load_ledger(ledger, company)
    except InputError as e:
        print(f"[입력 오류] {e}", file=sys.stderr)
        return 1
    for sub in ("html", "pdf", "mail"):
        os.makedirs(os.path.join(output, sub), exist_ok=True)
    edge = find_edge()
    made = 0
    for s in slips:
        base = f"{s.name}_급여명세서_{s.month}"
        html_path = os.path.join(output, "html", base + ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(render_html(s, company))
        if not edge:
            continue
        pdf_path = os.path.join(output, "pdf", base + ".pdf")
        html_to_pdf(html_path, pdf_path, edge)
        made += 1
        if s.email:
            write_eml(os.path.join(output, "mail", f"{s.employee_no}.eml"), s, company, pdf_path)
    if edge:
        cleanup_profile(os.path.join(output, "pdf"))
    else:
        issues.append("Microsoft Edge를 찾지 못해 PDF를 만들지 못함 (HTML만 생성)")
    with open(os.path.join(output, "확인필요.md"), "w", encoding="utf-8") as f:
        f.write("# 월급명세서 — 확인 필요\n\n" + ("\n".join(f"- {i}" for i in issues) if issues else "- 없음") +
                "\n\n> 메일 초안은 발송되지 않았습니다. 확인 후 직접 발송하세요.\n")
    print(f"명세서 PDF {made}건 · 미생성 {len(slips) - made + sum('합계 불일치' in i for i in issues)}건 · 결과: {output}")
    if not edge:
        return 3
    return 2 if any("합계 불일치" in i for i in issues) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="급여대장 → 월급명세서 PDF")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--company", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args(argv)
    return run_payslips(a.ledger, a.company, a.output)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
