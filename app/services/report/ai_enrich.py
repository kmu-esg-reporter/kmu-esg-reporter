# app/services/report/ai_enrich.py
import asyncio
from asyncio.log import logger
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from .ai_schemas import EnvEnrichment, SocEnrichment, GovEnrichment

SYS = """당신은 ESG 보고서 작성 보조 AI입니다.
- 숫자/원시 지표는 절대 고치지 마세요.
- 비어있는 설명/하이라이트/리스크/액션/스토리는 템플릿 스키마에 맞춰 생성하세요.
- 한국어로 간결하고 전문적으로 작성하세요.
"""

PROMPT_ENV = ChatPromptTemplate.from_messages([
    ("system", SYS),
    ("user", """다음 환경(E) 원시 지표로 보고서용 보조 텍스트를 구조화하세요.
원시지표(JSON):
{raw}

요구사항:
- executive_summary: 2~4문장
- highlights: 4개 이상
- risks: 3개 이상 (각각 mitigation 포함)
- actions: 6개 이상 (구체적이며 측정가능한 표현)
- trends: 원시 trends가 비어있다면 최근 3년 Placeholder 구성 (year만 채워도 됨)
""")
])

PROMPT_SOC = ChatPromptTemplate.from_messages([
    ("system", SYS),
    ("user", """다음 사회(S) 원시 지표로 보고서용 보조 텍스트를 구조화하세요.
원시지표(JSON):
{raw}

요구사항:
- executive_summary: 2~4문장
- programs: 4개 이상 (title/desc)
- actions: 6개 이상
- stories: 0~3개 (선택), 있으면 2~3문장 짧은 사례
""")
])

PROMPT_GOV = ChatPromptTemplate.from_messages([
    ("system", SYS),
    ("user", """다음 거버넌스(G) 원시 지표로 보고서용 보조 텍스트를 구조화하세요.
원시지표(JSON):
{raw}

요구사항:
- executive_summary: 2~4문장
- policies_notes: 2~4개 (정책 운영상 유의점/권고)
- risks: 4개 이상 (mitigation 필수)
- actions: 6개 이상
- disclosures: 0~5개 (선택)
""")
])

def _to_dict(x):
    # pydantic v2 / v1 호환
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return x  # 이미 dict라면 그대로

class ESGEnricher:
    def __init__(self, llm: ChatOpenAI):
        # 구조화 출력(스키마 강제)
        self.llm_env: Runnable = PROMPT_ENV | llm.with_structured_output(EnvEnrichment)
        self.llm_soc: Runnable = PROMPT_SOC | llm.with_structured_output(SocEnrichment)
        self.llm_gov: Runnable = PROMPT_GOV | llm.with_structured_output(GovEnrichment)
        self._enrich_cache = {}

    async def _with_timeout(self, coro, seconds: float, fallback: dict):
        try:
            res = await asyncio.wait_for(coro, timeout=seconds)
            return _to_dict(res)
        except asyncio.TimeoutError:
            logger.warning("AI 보강 타임아웃: %s", getattr(coro, "__name__", "section"))
            return fallback
        except Exception as e:
            logger.error("AI 보강 중 오류: %s", e, exc_info=True)
            return fallback

    async def _enrich_with_guard(self, esg_metrics: Dict[str, Any]) -> Dict[str, Any]:
        # 캐시 키 (회사/기간 단위로 키를 더 줄여도 됨)
        key = (json.dumps(esg_metrics, sort_keys=True, ensure_ascii=False))[:20000]
        if key in self._enrich_cache:
            return self._enrich_cache[key]

        env_raw = esg_metrics.get("environment") or {}
        soc_raw = esg_metrics.get("social") or {}
        gov_raw = esg_metrics.get("governance") or {}

        # 섹션별 코루틴 (네이티브 async: ainvoke 사용)
        env_coro = self.llm_env.ainvoke({"raw": env_raw})
        soc_coro = self.llm_soc.ainvoke({"raw": soc_raw})
        gov_coro = self.llm_gov.ainvoke({"raw": gov_raw})

        # 섹션별 개별 타임아웃 및 부분 성공 허용 (예: 각 30초)
        # 섹션이 실패해도 최소한 ai: {}는 보장
        env_en, soc_en, gov_en = await asyncio.gather(
            self._with_timeout(env_coro, 30, {}),
            self._with_timeout(soc_coro, 30, {}),
            self._with_timeout(gov_coro, 30, {}),
        )

        # 항상 ai 키가 존재하도록 구성
        enriched = {
            "environment": {**env_raw, "ai": env_en if isinstance(env_en, dict) else {}},
            "social":      {**soc_raw, "ai": soc_en if isinstance(soc_en, dict) else {}},
            "governance":  {**gov_raw, "ai": gov_en if isinstance(gov_en, dict) else {}},
            "summary": {
                "E_summary": (env_en or {}).get("executive_summary"),
                "S_summary": (soc_en or {}).get("executive_summary"),
                "G_summary": (gov_en or {}).get("executive_summary"),
            },
        }

        self._enrich_cache[key] = enriched
        return enriched