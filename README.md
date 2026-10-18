# academy-ops — 학원 급여 자동화 프로토타입

학원 운영 SaaS(`D:\우리컴퓨터\근태관리\PROJECT_SPEC.md`)의 **급여 계산 엔진**을 먼저 검증하는 프로토타입입니다.
가상 9월 데이터(강사 4·행정 2)로 동작합니다.

```bash
python tools/make_samples.py samples/2026-09     # 가상 데이터 다시 만들기
python -m app.cli run --month 2026-09 --input samples/2026-09 --output out/2026-09
python -m pytest -q
```

결과(`out/2026-09/`): `급여계산표_2026-09.xlsx` · `명세서/*.pdf` · `메일초안/*.txt` · `확인필요_2026-09.md` · `run.json`

**급여대장 → 월급명세서 PDF** (워크플로우랩 더미):

```bash
python tools/make_payslip_samples.py samples/payslip/workflowlab
python -m app.payslip.cli --ledger samples/payslip/workflowlab/급여대장_2026-09.xlsx --company samples/payslip/workflowlab/company.yaml --output out/payslips/2026-09
```

- 설계서: `docs/superpowers/specs/2026-10-18-payroll-prototype-design.md` · `docs/superpowers/specs/2026-10-18-payslip-ledger-design.md`
- 구현 계획서: `docs/superpowers/plans/2026-10-18-payroll-prototype.md`
- 스킬: `.claude/skills/payroll/SKILL.md` (`/payroll 2026-09`)

필요 패키지: `openpyxl`, `PyYAML`, `reportlab`, `pytest` · 한글 PDF는 Windows 맑은 고딕 글꼴 사용
