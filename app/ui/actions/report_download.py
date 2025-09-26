# app/ui/actions/report_download.py
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.services.report.generator import build_report_html
from app.services.report.renderer import html_to_pdf
from app.data.processors.data_processor import ESGDataProcessor

PERIOD_LABELS = {
    "current_year": "Current Year",
    "last_year": "Previous Year",
    "last_3_years": "Last 3 Years",
    "all_time": "All Available Data",
}

def _safe_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).rstrip()

async def generate_esg_pdf(db: Session, cmp_num: str, options: Dict[str, Any]) -> Path:
    """
    1) DB에서 종합 리포트 데이터 수집
    2) HTML 생성
    3) PDF 렌더링
    """
    dp = ESGDataProcessor(db)

    # 1) 데이터 수집 (당신의 processor가 반환하는 구조에 맞춰 사용)
    # 기대 구조 예: {"company_info": {...}, "summary": {...}, "esg_metrics": {"environmental": {...}, "social": {...}, "governance": {...}}}
    report = dp.generate_comprehensive_report(cmp_num)
    if "error" in report:
        raise RuntimeError(report["error"])

    company_info = report.get("company_info", {})
    summary = report.get("summary", {})
    esg = report.get("esg_metrics", {})

    env_metrics = esg.get("environmental", {})
    soc_metrics = esg.get("social", {})
    gov_metrics = esg.get("governance", {})

    period = options.get("period", "current_year")
    period_label = PERIOD_LABELS.get(period, period)

    # 2) HTML 생성
    html = build_report_html(
    company_info=company_info,
    period_label=period_label,
    summary_metrics=summary,
    env_metrics=env_metrics,
    soc_metrics=soc_metrics,
    gov_metrics=gov_metrics,
    # narratives=report.get("narratives", {}),
)

    # 3) PDF 저장 경로
    out_dir = Path("generated_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    company_name = _safe_name(company_info.get("cmp_nm", cmp_num or "company"))
    
    # 현재 시간 
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # 예: 2025-09-26_16-30-45

    # PDF 파일명에 시간 포함
    out_path = out_dir / f"ESG_Report_{company_name}_{timestamp}.pdf"
    
    # 4) PDF 렌더링
    return html_to_pdf(html, out_path)
