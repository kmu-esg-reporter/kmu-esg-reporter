# app/services/report/ai_schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field

class EHighlights(BaseModel):
    title: str
    desc: str
    source: str = "ai_generated"

class ERisk(BaseModel):
    risk: str
    mitigation: str
    source: str = "ai_generated"

class EAction(BaseModel):
    action: str
    impact: str
    source: str = "ai_generated"

class ETrendsRow(BaseModel):
    year: Optional[int]
    energy_use: Optional[float]
    ghg_emissions: Optional[float] = Field(None, alias="green_use")
    renewable_ratio: Optional[float]

class EnvEnrichment(BaseModel):
    executive_summary: str
    highlights: List[EHighlights]
    risks: List[ERisk]
    actions: List[EAction]
    trends: List[ETrendsRow] = []  # 비어있으면 원본 trends로 대체

class SItem(BaseModel):
    label: str
    value: Optional[float] | Optional[int] | Optional[str] = None
    note: Optional[str] = None
    source: str = "ai_generated"

class SAction(BaseModel):
    action: str
    impact: str
    source: str = "ai_generated"

class SocEnrichment(BaseModel):
    executive_summary: str
    programs: List[dict]  # {title, desc, source}
    actions: List[SAction]
    stories: List[str] = []

class GovAction(BaseModel):
    action: str
    impact: str
    source: str = "ai_generated"

class GovRisk(BaseModel):
    risk: str
    mitigation: str
    source: str = "ai_generated"

class GovEnrichment(BaseModel):
    executive_summary: str
    policies_notes: List[str] = []
    risks: List[GovRisk]
    actions: List[GovAction]
    disclosures: List[str] = []
