"""Database connection and session management."""
from .base import Base, get_db, engine, SessionLocal, init_db
from .models import (
    CmpInfo, 
    EmpInfo, 
    Env, 
    Report, 
    ChatSession, 
    DataImportLog,
    Company  # CmpInfo의 별칭
)

__all__ = [
    "Base", 
    "get_db", 
    "engine", 
    "SessionLocal", 
    "init_db",
    "CmpInfo",      # 새로운 회사 정보 모델
    "EmpInfo",      # 새로운 직원 정보 모델  
    "Env",          # 새로운 환경 현황 모델
    "Report", 
    "ChatSession", 
    "DataImportLog",
    "Company"       # 하위 호환성을 위한 별칭
]
