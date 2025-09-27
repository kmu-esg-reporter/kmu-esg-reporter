# app/services/report/types.py
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

@dataclass
class ESGSectionContext:
    title: str
    metrics: Dict[str, Any]         # 섹션용 계산 지표
    charts: Optional[List[str]] = None  # (선택) base64 이미지 등

@dataclass
class ESGReportContext:
    company: Dict[str, Any]         # {"cmp_nm":..., "cmp_sector":...}
    period_label: str               # "2025", "최근 3년" 등
    generated_at: str               # ISO 문자열
    summary: Dict[str, Any]         # 총괄 지표(요약 카드)
    env: ESGSectionContext
    soc: ESGSectionContext
    gov: ESGSectionContext
