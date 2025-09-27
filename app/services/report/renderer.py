# app/services/report/renderer.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Union
from xhtml2pdf import pisa
from xhtml2pdf.files import pisaFileObject
from .fonts import ensure_fonts, FONT_DIR
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging
from urllib.parse import urlparse, unquote


logger = logging.getLogger(__name__)

# repo root / app root 계산
PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = PROJECT_ROOT / "app"

def _link_callback(uri: str, rel: Optional[str]) -> str:
    """xhtml2pdf가 리소스를 읽을 수 있도록 로컬 파일 '경로 문자열'을 반환한다."""
    if not uri:
        return uri

    # 1) file:///... 들어오면 OS 경로로 변환
    if uri.startswith("file:///"):
        p = urlparse(uri)
        # Windows: /C:/... 형태 → C:/... 로
        path = unquote(p.path.lstrip("/"))
        return path

    # 2) /app/... (우리 템플릿에서 쓰는 절대경로) → 앱 루트 기준 절대경로
    if uri.startswith("/app/"):
        rel_path = uri[len("/app/"):]
        abs_path = (APP_ROOT / rel_path).resolve()
        return str(abs_path)

    # 3) 그 외 절대경로(/...) → repo 루트 기준
    if uri.startswith("/"):
        abs_path = (PROJECT_ROOT / uri.lstrip("/")).resolve()
        return str(abs_path)

    # 4) 이미 절대경로면 그대로
    p = Path(uri)
    if p.is_absolute():
        return str(p)

    # 5) 상대경로는 repo 루트 기준으로
    return str((PROJECT_ROOT / uri).resolve())

def html_to_pdf(html_str: str, out_path: Union[str, Path]) -> Path:
    # 폰트 확보 (없으면 다운로드)
    fonts = ensure_fonts()
    reg = Path(fonts["regular"])
    bld = Path(fonts["bold"])

    pisaFileObject.getNamedFile = lambda self: self.uri

    if not reg.exists() or not bld.exists():
        raise RuntimeError(f"폰트가 없습니다. regular={reg}, bold={bld}")

    # ReportLab에 폰트 등록 (CSS font-family 이름과 동일하게)
    pdfmetrics.registerFont(TTFont("KRBody", str(reg)))
    pdfmetrics.registerFont(TTFont("KRBodyBold", str(bld)))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 디버깅용 로그(원하면 삭제)
    logger.info("[PDF] Using fonts: regular=%s, bold=%s", reg, bld)
    logger.info("[PDF] Output path: %s", out_path)

    with open(out_path, "wb") as f:
        result = pisa.CreatePDF(
            src=html_str,
            dest=f,
            encoding="utf-8",
            link_callback=_link_callback,  # ★ 중요: 경로 문자열 반환
        )

    if result.err:
        raise RuntimeError("xhtml2pdf 변환 실패")
    return out_path
