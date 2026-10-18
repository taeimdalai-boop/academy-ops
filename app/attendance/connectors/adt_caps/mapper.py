"""캡스 모드 번호 → 표준 이벤트 종류. 캡스 전용 값은 이 파일에만 둔다 (PROJECT_SPEC 5.2)."""
from app.attendance import model

MODE_MAP = {1: model.CHECK_IN, 2: model.CHECK_OUT, 3: model.BREAK_OUT, 4: model.BREAK_IN, 5: model.ACCESS}
MODE_MAP.update({m: model.MEAL for m in range(6, 11)})


def to_kind(mode):
    return MODE_MAP.get(int(mode))
