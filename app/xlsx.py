"""엑셀 첫 시트를 행 dict 목록으로 읽는다. 필수 열이 없으면 InputError."""
import os

from openpyxl import load_workbook


class InputError(Exception):
    pass


def read_rows(path, required):
    if not os.path.exists(path):
        raise InputError(f"입력 파일 없음: {path}")
    ws = load_workbook(path, read_only=True, data_only=True).active
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(rows, [])]
    for col in required:
        if col not in header:
            raise InputError(f"{os.path.basename(path)}: 열 '{col}' 없음")
    out = []
    for r in rows:
        if r is None or all(v is None for v in r):
            continue
        out.append(dict(zip(header, r)))
    return out
