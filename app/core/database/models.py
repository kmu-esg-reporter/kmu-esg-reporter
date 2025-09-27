"""Database models for ESG Reporter."""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Date,JSON, Numeric
from decimal import Decimal  # Python Decimal 타입

from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

"""
2025-09-21 14:00 기준
ESG 분석용 DB 구조 변경 및 리팩토링 요약

1. models.py 주요 변경 사항
---------------------------
- 새로운 모델 클래스:

  1) CmpInfo (CMP_INFO 테이블 매핑)
     - cmp_num: 사업장번호 (PK)
     - cmp_nm: 회사명
     - cmp_industry, cmp_sector: 업종, 산업
     - cmp_extemp: 사외 이사회 수
     - cmp_ethics_yn, cmp_comp_yn: 윤리경영, 컴플라이언스 여부

  2) EmpInfo (EMP_INFO 테이블 매핑)
     - emp_id: 사번 (PK)
     - emp_nm, emp_birth, emp_join: 이름, 생년월일, 입사일
     - emp_acident_cnt: 산재 발생 횟수
     - emp_board_yn, emp_gender: 이사회 여부, 성별

  3) Env (ENV 테이블 매핑)
     - year: 연도 (PK)
     - energy_use, green_use: 에너지 사용량, 온실가스 배출량
     - renewable_yn, renewable_ratio: 재생에너지 사용 여부, 비율

- 호환성 유지:
  - 기존 Report, ChatSession, DataImportLog는 cmp_num FK 사용
  - Company = CmpInfo 별칭으로 하위 호환성 보장

2. data_processor.py 주요 기능
-------------------------------
- 새로운 데이터 처리 메서드:
  - get_company_info(cmp_num: str) -> Dict      # 회사 기본 정보 조회
  - get_employee_data() -> DataFrame            # 직원 데이터 조회
  - get_environmental_data() -> DataFrame       # 환경 데이터 조회

- ESG 지표 계산:
  - calculate_social_metrics(): 성별 다양성, 이사회 구성, 안전 지표, 근속년수
  - calculate_environmental_metrics(): 에너지/온실가스 트렌드, 재생에너지 비율
  - calculate_governance_metrics(): 사외이사 비율, 윤리경영/컴플라이언스 정책

- 통합 분석 기능:
  - generate_comprehensive_report(cmp_num: str) -> Dict  # 종합 ESG 보고서
  - identify_data_gaps(cmp_num: str) -> Dict             # 데이터 갭 분석

3. 계산 지표 예시
-----------------
- Social:
  - 전체 직원 수, 성별 분포, 여성 비율
  - 이사회 구성원 수, 여성 이사 비율
  - 총 산재 발생 수, 산재율, 무재해 직원 수
  - 평균 근속년수, 신입/베테랑 직원 수

- Environmental:
  - 최신 연도 에너지 사용량, 온실가스 배출량
  - 재생에너지 사용 여부 및 비율
  - 최근 3년 트렌드 분석 (증가/감소율)
  - 연도별 에너지 집약도

- Governance:
  - 사외이사 수 및 비율
  - 윤리경영, 컴플라이언스 정책 존재 여부
  - 이사회 다양성 비율
  - 종합 지배구조 점수 및 등급 (A+~D)

4. 하위 호환성
---------------
- 기존 get_company_data(), calculate_category_summaries() 메서드 유지
- 새로운 테이블 데이터를 기존 ESGData 형태로 변환하여 반환
- 새로운 DB 구조 기반으로 더 정확하고 실용적인 ESG 분석 가능
"""
"""Database models for ESG Reporter - Updated to match new DB schema."""

# 하위 호환용 Dummy
class ESGData:
    """Dummy ESGData for backward compatibility."""
    pass

# 기존 테이블들 - cmp_num FK로 수정
class Report(Base):
    """Generated ESG reports."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(10), ForeignKey("cmp_info.cmp_num"), nullable=False)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50))
    content = Column(Text)
    summary = Column(Text)
    generated_by = Column(String(50))
    format = Column(String(20))
    status = Column(String(20), default="draft")
    file_path = Column(String(500))
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("CmpInfo", back_populates="reports")

class ChatSession(Base):
    """Chat sessions for the ESG chatbot."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    company_id = Column(String(10), ForeignKey("cmp_info.cmp_num"), nullable=True)
    user_id = Column(String(255))
    title = Column(String(255))
    messages = Column(JSON)
    context = Column(JSON)
    message_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("CmpInfo", back_populates="chat_sessions")

class CmpInfo(Base):
    """Company information model for company management."""
    
    __tablename__ = "cmp_info"
    
    cmp_num = Column(String(10), primary_key=True)  # 사업장번호 (복합 PK 1)
    cmp_branch = Column(String(10), primary_key=True)  # 지점 (복합 PK 2)
    cmp_nm = Column(String(100), nullable=False)  # 회사명
    cmp_industry = Column(String(20))  # 업종
    cmp_sector = Column(String(20))  # 산업
    cmp_addr = Column(String(200))  # 주소
    cmp_extemp = Column(Integer)  # 사외 이사회 수
    cmp_ethics_yn = Column(String(1))  # 윤리경영 여부
    cmp_comp_yn = Column(String(1))  # 컴플라이언스 정책 여부
    
    # Relationships
    reports = relationship("Report", back_populates="company")
    chat_sessions = relationship("ChatSession", back_populates="company")
    data_import_logs = relationship("DataImportLog", back_populates="company")


class EmpInfo(Base):
    """Employee model for HR management."""
    
    __tablename__ = "emp_info"
    
    EMP_ID = Column(Integer, primary_key=True, index=True)  # 사번 (Primary Key)
    EMP_NM = Column(String(10), nullable=False)  # 이름
    EMP_BIRTH = Column(String(8))  # 생년월일 (YYYYMMDD)
    EMP_TEL = Column(String(20))  # 전화번호
    EMP_EMAIL = Column(String(20))  # 이메일
    EMP_JOIN = Column(String(8))  # 입사년도 (YYYYMMDD)
    EMP_ACIDENT_CNT = Column(Integer, default=0)  # 산재발생횟수
    EMP_BOARD_YN = Column(String(1), default='N')  # 이사회여부
    EMP_GENDER = Column(String(1))  # 성별 (1:남자, 2:여자)
    EMP_ENDYN = Column(String(1), default='Y')  # 재직여부 (Y:재직, N:퇴직)
    EMP_COMP = Column(String(10))  # 사업장
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Env(Base):
    """환경현황 테이블"""
    
    __tablename__ = "env"
    
    year = Column(Integer, primary_key=True, index=True)  # 년도 (PK, YYYY)
    energy_use = Column(Float)  # 에너지 사용량
    green_use = Column(Float)  # 온실가스 배출량
    renewable_yn = Column(String(1))  # 재생에너지 사용여부 (Y/N)
    renewable_ratio = Column(Float)  # 재생에너지 비율
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataImportLog(Base):
    """Log for data import operations."""
    
    __tablename__ = "data_import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(10), ForeignKey("cmp_info.cmp_num"), nullable=False)
    import_type = Column(String(50))
    source_file = Column(String(500))
    status = Column(String(20))
    records_processed = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    error_log = Column(JSON)
    validation_errors = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("CmpInfo", back_populates="data_import_logs")

# 하위 호환성을 위한 별칭
Company = CmpInfo
