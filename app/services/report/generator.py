# app/services/reports/esg/generator.py
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .sections import render_environment, render_social, render_governance, TPL_DIR
from .types import ESGReportContext, ESGSectionContext

_base_env = Environment(
    loader=FileSystemLoader(str(TPL_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

def _pad(items: List[Dict[str, Any]], min_len: int, filler: Dict[str, Any]) -> List[Dict[str, Any]]:
    """2페이지 분량 보장을 위해 항목 수 최소 길이 확보."""
    items = list(items or [])
    while len(items) < min_len:
        items.append(filler.copy())
    return items

def _mk_yoy(cur: Any, prev: Any) -> Any:
    try:
        if cur is None or prev in (None, 0):
            return None
        return round((cur - prev) / prev * 100, 2)
    except Exception:
        return None

def _normalize_env(metrics: Dict[str, Any]) -> Dict[str, Any]:
    m = dict(metrics or {})
    cur = m.get("current_status", {})
    trends = m.get("trends", [])
    prev = (trends[-2] if len(trends) >= 2 else {}) or {}

    energy_use = cur.get("energy_use")
    ghg = cur.get("green_use") or cur.get("ghg_emissions")
    renew_ratio = cur.get("renewable_ratio")

    overview = {
        "최신 연도": cur.get("latest_year") or "N/A",
        "에너지 사용량(MWh)": f"{energy_use:,.1f}" if energy_use else "N/A",
        "온실가스 배출량(tCO₂e)": f"{ghg:,.1f}" if ghg else "N/A",
        "재생에너지 사용(Y/N)": cur.get("renewable_yn") or "N",
        "재생에너지 비율(%)": f"{renew_ratio:.1%}" if renew_ratio else "0%",
    }

    # 직원 수 기반 집약도 계산
    total_employees = cur.get("total_employees", 0)
    energy_intensity = None
    ghg_intensity = None
    
    if total_employees and total_employees > 0:
        if energy_use:
            energy_intensity = f"{energy_use/total_employees:.2f}"
        if ghg:
            ghg_intensity = f"{ghg/total_employees:.2f}"
    
    kpis = [
        {"label": "에너지 집약도(MWh/인)", "value": energy_intensity or "직원 정보 없음", "note": "총 직원 수 기준"},
        {"label": "GHG 집약도(tCO₂e/인)", "value": ghg_intensity or "직원 정보 없음", "note": "총 직원 수 기준"},
        {"label": "YoY 에너지 증감(%)", "value": f"{_mk_yoy(energy_use, prev.get('energy_use')):.1f}%" if _mk_yoy(energy_use, prev.get("energy_use")) else "데이터 부족"},
        {"label": "YoY 배출량 증감(%)", "value": f"{_mk_yoy(ghg, prev.get('green_use') or prev.get('ghg_emissions')):.1f}%" if _mk_yoy(ghg, prev.get("green_use") or prev.get("ghg_emissions")) else "데이터 부족"},
        {"label": "재생에너지 구매/자체발전 계획", "value": cur.get("renewable_plan", "미등록")},
    ]

    highlights = [
        {"title": "전력 사용 데이터 커버리지", "desc": m.get("coverage_note", "사업장별 월별 데이터 수집 상태 점검 필요")},
        {"title": "배출계수 적용 일관성", "desc": "K-ETS/IPCC 계수 최신 버전 사용 여부 확인"},
        {"title": "스코프3 범주 파악", "desc": "구매재화·물류·폐기물 등 고배출 범주 식별"},
    ]

    actions = [
        {"action": "EMS(에너지 관리시스템) 도입/고도화", "impact": "실시간 모니터링 및 피크 제어로 3~7% 절감 기대"},
        {"action": "조명 LED 전환/인버터 제어", "impact": "간단 투자로 단기 절감"},
        {"action": "재생에너지 전기구매(PPA/GPPA) 검토", "impact": "재생 비율 상향"},
        {"action": "스코프3 스크리닝", "impact": "중장기 감축 로드맵 수립 기반"},
    ]

    risks = [
        {"risk": "전력단가 상승 리스크", "mitigation": "피크 관리·계약 최적화"},
        {"risk": "배출권 가격 변동", "mitigation": "조기감축·내부 탄소가격 도입"},
    ]

    # 2페이지 보장: 항목 수 패딩 (의미있는 항목으로 변경)
    kpis = _pad(kpis, 6, {"label": "탄소중립 목표년도", "value": "2050", "note": "국가 탄소중립 목표"})
    highlights = _pad(highlights, 4, {"title": "추가 하이라이트", "desc": "데이터 입력 필요"})
    actions = _pad(actions, 6, {"action": "추가 과제", "impact": "데이터 입력 필요"})
    risks = _pad(risks, 3, {"risk": "추가 리스크", "mitigation": "대응방안 수립"})

    return {
        "overview": overview,
        "trends": trends,              # 그래프/표 템플릿에서 사용
        "kpis": kpis,
        "highlights": highlights,
        "actions": actions,
        "risks": risks,
        "notes": m.get("notes", []),
    }

def _normalize_soc(metrics: Dict[str, Any]) -> Dict[str, Any]:
    
    # m = dict(metrics or {})
    # diversity = m.get("diversity", {})
    # safety = m.get("safety", {})
    # board = m.get("board_composition", {})

    # overview = {
    #     "총 인원": diversity.get("total_employees"),
    #     "여성 비율(%)": diversity.get("female_ratio"),
    #     "총 산재 건수": safety.get("total_accidents"),
    #     "산재율(%)": safety.get("accident_rate"),
    #     "무재해 인원": safety.get("zero_accident_employees"),
    #     "여성 이사 비율(%)": board.get("female_board_ratio"),
    # }
    
    m = dict(metrics or {})
    diversity = m.get("diversity", {})
    safety = m.get("safety", {})
    board = m.get("board_composition", {})

    # 잘못된 키 수정
    overview = {
        "총 인원": diversity.get("total_employees"),
        "여성 비율(%)": round(diversity.get("female_ratio", 0) * 100, 1),  
        "총 산재 건수": safety.get("total_accidents"),
        "산재율(%)": round(safety.get("accident_rate", 0) * 100, 2),
        "무재해 인원": safety.get("zero_accident_employees"),
        "여성 이사 비율(%)": round(board.get("female_board_ratio", 0) * 100, 1),
    }


    diversity_list = [
        {"label": "남성(명)", "value": diversity.get("male_count")},
        {"label": "여성(명)", "value": diversity.get("female_count")},
        {"label": "장애인 고용률(%)", "value": diversity.get("disabled_ratio")},
        {"label": "청년 고용률(%)", "value": diversity.get("youth_ratio")},
    ]
    safety_list = [
        {"label": "사망사고(건)", "value": safety.get("fatal_accidents")},
        {"label": "휴업 손실일(일)", "value": safety.get("lost_days")},
        {"label": "산안법 위반(건)", "value": safety.get("violations")},
    ]
    training_list = [
        {"label": "직원 1인당 교육시간(시간)", "value": m.get("training", {}).get("hours_per_emp")},
        {"label": "안전교육 이수율(%)", "value": m.get("training", {}).get("safety_completion")},
        {"label": "리더십/윤리 교육(%)", "value": m.get("training", {}).get("ethics_completion")},
    ]

    programs = [
        {"title": "산재 다발 공정 개선", "desc": "위험성평가 및 공정 재배치"},
        {"title": "여성 리더십 프로그램", "desc": "멘토링·승진경로 설계"},
        {"title": "협력사 안전 점검", "desc": "현장 합동 점검 및 가이드 제공"},
    ]
    actions = [
        {"action": "중대재해 예방체계 점검", "impact": "법정 이행·사고 예방"},
        {"action": "다양성 KPI 도입", "impact": "조직문화 개선"},
        {"action": "연 2회 안전보건 감사", "impact": "리스크 발견/시정 조치"},
    ]

    # 2페이지 보장
    diversity_list = _pad(diversity_list, 6, {"label": "추가 다양성 지표", "value": None})
    safety_list = _pad(safety_list, 6, {"label": "추가 안전 지표", "value": None})
    training_list = _pad(training_list, 4, {"label": "추가 교육 지표", "value": None})
    programs = _pad(programs, 4, {"title": "추가 프로그램", "desc": "내용 입력 필요"})
    actions = _pad(actions, 6, {"action": "추가 과제", "impact": "내용 입력 필요"})

    return {
        "overview": overview,
        "diversity": diversity_list,
        "safety": safety_list,
        "training": training_list,
        "programs": programs,
        "actions": actions,
        "stories": m.get("stories", []),
    }

def _normalize_gov(metrics: Dict[str, Any]) -> Dict[str, Any]:
    m = dict(metrics or {})
    basic = m.get("basic_governance", {})
    board = m.get("board", {})
    policies = [
        {"label": "윤리경영", "value": "운영" if basic.get("ethics_policy") else "부재"},
        {"label": "컴플라이언스", "value": "운영" if basic.get("compliance_policy") else "부재"},
        {"label": "내부고발제도", "value": "운영" if basic.get("whistleblower") else "부재"},
        {"label": "개인정보보호", "value": "운영" if basic.get("privacy_policy") else "부재"},
    ]
    overview = {
        "사외이사 수": basic.get("external_directors"),
        "위원회 설치": basic.get("committees", ["감사", "보상", "ESG"]),
        "윤리경영": "Y" if basic.get("ethics_policy") else "N",
        "컴플라이언스": "Y" if basic.get("compliance_policy") else "N",
    }
    board_table = [
        {"role": "사내이사", "count": board.get("inside", None)},
        {"role": "사외이사", "count": board.get("outside", None)},
        {"role": "여성 이사", "count": board.get("female", None)},
        {"role": "독립성 충족(명)", "count": board.get("independent", None)},
    ]
    risks = [
        {"risk": "이사회 독립성 미흡", "mitigation": "사외이사 확대·전문성 보강"},
        {"risk": "준법 리스크", "mitigation": "연간 컴플라이언스 교육/점검"},
        {"risk": "데이터 관리 미흡", "mitigation": "ISMS/ISO27001 수준 맞춤 관리"},
    ]
    actions = [
        {"action": "ESG 위원회 정례화", "impact": "거버넌스 투명성 강화"},
        {"action": "이해관계자 고충 채널", "impact": "분쟁 예방·신뢰 제고"},
        {"action": "반부패·공정거래 교육", "impact": "법적 리스크 저감"},
    ]

    # 2페이지 보장
    policies = _pad(policies, 6, {"label": "추가 정책", "value": "검토 필요"})
    board_table = _pad(board_table, 6, {"role": "추가 항목", "count": None})
    risks = _pad(risks, 4, {"risk": "추가 리스크", "mitigation": "대응방안 수립"})
    actions = _pad(actions, 6, {"action": "추가 과제", "impact": "내용 입력 필요"})

    return {
        "overview": overview,
        "policies": policies,
        "board_table": board_table,
        "risks": risks,
        "actions": actions,
        "disclosures": m.get("disclosures", []),
    }

def build_report_html(
    *,
    company_info: Dict[str, Any],
    period_label: str,
    summary_metrics: Dict[str, Any],
    env_metrics: Dict[str, Any],
    soc_metrics: Dict[str, Any],
    gov_metrics: Dict[str, Any],
) -> str:
    env_metrics = _normalize_env(env_metrics)
    soc_metrics = _normalize_soc(soc_metrics)
    gov_metrics = _normalize_gov(gov_metrics)

    env_html = render_environment(ESGSectionContext(title="Environmental", metrics=env_metrics))
    soc_html = render_social(ESGSectionContext(title="Social", metrics=soc_metrics))
    gov_html = render_governance(ESGSectionContext(title="Governance", metrics=gov_metrics))

    base = _base_env.get_template("base.html")
    ctx = ESGReportContext(
        company=company_info,
        period_label=period_label,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        summary=summary_metrics or {},
        env=ESGSectionContext(title="Environmental", metrics=env_metrics),
        soc=ESGSectionContext(title="Social", metrics=soc_metrics),
        gov=ESGSectionContext(title="Governance", metrics=gov_metrics),
    )
    css_styles = """
    <style>
    body { font-family: 'KRBody', sans-serif; margin: 20px; line-height: 1.6; }
    h1, h2, h3 { font-family: 'KRBodyBold', sans-serif; color: #2c3e50; }
    .metric-box { border: 1px solid #ddd; padding: 10px; margin: 5px; border-radius: 5px; }
    .overview-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    .overview-table th, .overview-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .overview-table th { background-color: #f8f9fa; font-weight: bold; }
    .positive { color: #27ae60; } .negative { color: #e74c3c; } .neutral { color: #7f8c8d; }
    .section { margin: 20px 0; page-break-inside: avoid; }
    </style>
    """

    final_html =  base.render(
        report=ctx,
        env_html=env_html,
        soc_html=soc_html,
        gov_html=gov_html,
    )
    final_html = final_html.replace('<head>', f'<head>{css_styles}')
    return final_html

