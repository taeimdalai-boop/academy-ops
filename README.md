# academy-ops — 학원 급여 자동화 프로토타입

학원 운영 SaaS(`D:\우리컴퓨터\근태관리\PROJECT_SPEC.md`)의 **급여 계산 엔진**을 먼저 검증하는 프로토타입입니다.
가상 9월 데이터(강사 4·행정 2)로 동작합니다.

```bash
python tools/make_samples.py samples/2026-09     # 가상 데이터 다시 만들기
python -m app.cli run --month 2026-09 --input samples/2026-09 --output out/2026-09
python -m pytest -q
```

결과(`out/2026-09/`):

| 산출물 | 쓰임 |
|:---|:---|
| `명세서/<성명>_급여명세서_2026-09.pdf` | **직원에게 주는 문서.** 실물 양식(A4 1장, HTML→Edge 인쇄) |
| `계산근거/<직원ID>_2026-09.pdf` | 금액이 어떻게 나왔는지 검산하는 **내부 자료**(항목·수량·단가·근거) |
| `급여계산표_2026-09.xlsx` | 요약·명세항목·근태집계·확인필요 4시트 |
| `메일초안/*.txt` | 발송하지 않는다. 사람이 확인 후 보낸다 |
| `확인필요_2026-09.md` | 프로그램이 판단하지 않고 사람에게 넘긴 항목 |
| `run.json` | 실행 기록(입력 파일 해시·정책값·합계) |

`명세서`는 입력 폴더에 `company.yaml`이 있을 때만 만든다. 없으면 `계산근거`까지만 만든다.

**결과 대시보드** (계산 결과를 한 장으로 보는 화면):

```bash
python tools/make_dashboard.py out/2026-09 docs/index.html
```

`docs/index.html`은 `run.json`과 `확인필요_*.md`를 읽어 만든 **자체 완결 HTML 한 장**입니다.
계산은 CLI가 하고 이 화면은 결과를 보여주기만 합니다 — 계산도 수정도 하지 않습니다.
GitHub Pages를 `main` 브랜치의 `/docs`로 설정하면 그대로 공개됩니다.

**급여대장 → 월급명세서 PDF** (워크플로우랩 더미):

```bash
python tools/make_payslip_samples.py samples/payslip/workflowlab
python -m app.payslip.cli --ledger samples/payslip/workflowlab/급여대장_2026-09.xlsx --company samples/payslip/workflowlab/company.yaml --output out/payslips/2026-09
```

- 설계서: `docs/superpowers/specs/2026-10-18-payroll-prototype-design.md` · `docs/superpowers/specs/2026-10-18-payslip-ledger-design.md`
- 구현 계획서: `docs/superpowers/plans/2026-10-18-payroll-prototype.md`
- 스킬: `.claude/skills/payroll/SKILL.md` (`/payroll 2026-09`)

필요 패키지: `openpyxl`, `PyYAML`, `reportlab`, `pytest` · 한글 PDF는 Windows 맑은 고딕 글꼴 사용
