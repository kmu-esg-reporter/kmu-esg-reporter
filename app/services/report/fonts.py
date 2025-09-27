# app/services/report/fonts.py
from __future__ import annotations
import os, shutil
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.request import urlopen, Request

# 저장 위치: app/static/fonts
FONT_DIR = Path(__file__).resolve().parents[2] / "static" / "fonts"
FONT_DIR.mkdir(parents=True, exist_ok=True)

# 후보 URL들: (이 중 하나라도 성공하면 사용)
CANDIDATES: Dict[str, List[str]] = {
    # Noto Sans KR (static TTF 우선, variable도 후보)
    "NotoSansKR-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/notosanskr/static/NotoSansKR-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-VariableFont_wght.ttf",
    ],
    "NotoSansKR-Bold.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/notosanskr/static/NotoSansKR-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-VariableFont_wght.ttf",
    ],
    # Nanum Gothic (fallback)
    "NanumGothic-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
    ],
    "NanumGothic-Bold.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
    ],
}

# 최종적으로 템플릿이 참조할 "표준 파일명"
KR_STD_REG = FONT_DIR / "KRBody-Regular.ttf"
KR_STD_BLD = FONT_DIR / "KRBody-Bold.ttf"


def _is_valid_ttf(p: Path) -> bool:
    try:
        with p.open("rb") as f:
            head = f.read(4)
        # 0x00010000 (TTF) 또는 'OTTO' (OTF) 허용
        return head in (b"\x00\x01\x00\x00", b"OTTO")
    except Exception:
        return False


def _try_download(url: str, dst: Path) -> bool:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as r:
            data = r.read()
        tmp = dst.with_suffix(dst.suffix + ".part")
        with tmp.open("wb") as f:
            f.write(data)
        tmp.replace(dst)
        return True
    except Exception:
        return False


def _ensure_one(name: str) -> Path | None:
    """
    후보 URL들을 돌며 name(예: 'NotoSansKR-Regular.ttf')을 다운로드 시도.
    성공하면 로컬 경로 반환, 전부 실패하면 None.
    """
    dst = FONT_DIR / name
    if dst.exists() and _is_valid_ttf(dst):
        return dst
    for url in CANDIDATES.get(name, []):
        if _try_download(url, dst) and _is_valid_ttf(dst):
            return dst
    return None


def ensure_fonts() -> Dict[str, Path]:
    """
    1) NotoSansKR Regular/Bold 우선 확보
    2) 실패 시 NanumGothic Regular/Bold 확보
    3) 최종적으로 KRBody-Regular/ KRBody-Bold 로 '복사' (표준 파일명)
    """
    FONT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Noto 우선
    noto_reg = _ensure_one("NotoSansKR-Regular.ttf")
    noto_bld = _ensure_one("NotoSansKR-Bold.ttf")

    reg_src = noto_reg
    bld_src = noto_bld

    # 2) 하나라도 없으면 Nanum으로 대체
    if reg_src is None:
        reg_src = _ensure_one("NanumGothic-Regular.ttf")
    if bld_src is None:
        bld_src = _ensure_one("NanumGothic-Bold.ttf")

    # 3) 최종 확인
    if reg_src is None or not _is_valid_ttf(reg_src):
        raise RuntimeError("KR Regular 폰트 다운로드 실패 (Noto/Nanum 모두 실패)")
    if bld_src is None or not _is_valid_ttf(bld_src):
        raise RuntimeError("KR Bold 폰트 다운로드 실패 (Noto/Nanum 모두 실패)")

    # 4) 표준 파일명으로 복사(덮어쓰기)
    if KR_STD_REG.resolve() != reg_src.resolve():
        shutil.copyfile(reg_src, KR_STD_REG)
    if KR_STD_BLD.resolve() != bld_src.resolve():
        shutil.copyfile(bld_src, KR_STD_BLD)

    return {
        "regular": KR_STD_REG,
        "bold": KR_STD_BLD,
    }
