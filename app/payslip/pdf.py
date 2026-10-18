"""HTML → PDF: 헤드리스 Edge로 인쇄 (실물 명세서와 같은 방식)."""
import os
import pathlib
import shutil
import subprocess
import time

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    return shutil.which("msedge")


def html_to_pdf(html_path, pdf_path, edge):
    # 프로필은 출력 폴더 옆에 둔다 — 시스템 임시 폴더(일부 PC에서 보안 프로그램이 가로챔)에선 조용히 실패함
    # 문서마다 별도 프로필 — 직전 Edge가 같은 프로필을 쥐고 있으면 새 호출이 인쇄 없이 끝나는 경우가 있음
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    profile = os.path.join(_profile_dir(os.path.dirname(os.path.abspath(pdf_path))), str(abs(hash(stem))))
    subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                    f"--user-data-dir={profile}", f"--print-to-pdf={os.path.abspath(pdf_path)}",
                    pathlib.Path(os.path.abspath(html_path)).as_uri()],
                   check=True, capture_output=True, timeout=90)
    for _ in range(120):                     # 최대 30초
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            return
        time.sleep(0.25)
    raise RuntimeError(f"PDF 생성 실패: {pdf_path}")


def _profile_dir(pdf_dir):
    return os.path.join(os.path.dirname(pdf_dir), ".edge-profile")   # pdf/ 옆 (결과 폴더를 어지럽히지 않게)


def cleanup_profile(pdf_dir):
    path = _profile_dir(os.path.abspath(pdf_dir))
    for _ in range(10):                      # Edge가 잠깐 파일을 쥐고 있을 수 있음
        shutil.rmtree(path, ignore_errors=True)
        if not os.path.exists(path):
            return
        time.sleep(0.5)
