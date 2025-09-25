"""ESG data processing and transformation."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from app.core.database.models import ESGData, Company
from app.core.database.models import CmpInfo, EmpInfo, Env, ChatSession, Report, DataImportLog  # 새로운 모델 import


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


logger = logging.getLogger(__name__)


class ESGDataProcessor:
    """Process and transform ESG data for analysis and reporting."""
    
    def __init__(self, db: Session):
        self.db = db

    def get_company_info(self, cmp_num: str, cmp_branch: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        cmp_branch가 주어지면 정확히 매칭, 없으면 cmp_num에 해당하는 첫 번째 지점(또는 최신 업데이트)을 대표로 사용.
        """
        q = self.db.query(CmpInfo).filter(CmpInfo.cmp_num == cmp_num)
        if cmp_branch:
            q = q.filter(CmpInfo.cmp_branch == cmp_branch)

        # 최신 업데이트 순으로 하나 선택
        company = q.order_by(CmpInfo.cmp_branch.asc()).first()
        if not company:
            return None

        return {
            "cmp_num": company.cmp_num,
            "cmp_branch": company.cmp_branch,
            "cmp_nm": company.cmp_nm,
            "cmp_industry": company.cmp_industry,
            "cmp_sector": company.cmp_sector,
            "cmp_addr": company.cmp_addr,
            "cmp_extemp": company.cmp_extemp,
            "cmp_ethics_yn": company.cmp_ethics_yn,
            "cmp_comp_yn": company.cmp_comp_yn,
        }
    
    def get_employee_data(self, cmp_num: Optional[str] = None) -> pd.DataFrame:
        """
        EMP_INFO 컬럼 대문자 사용.
        cmp_num이 주어지면 EMP_COMP로 필터링.
        """
        q = self.db.query(EmpInfo)
        if cmp_num:
            q = q.filter(EmpInfo.EMP_COMP == cmp_num)

        rows = []
        for r in q.all():
            rows.append({
                "emp_id": r.EMP_ID,
                "emp_nm": r.EMP_NM,
                "emp_birth": r.EMP_BIRTH,
                "emp_tel": r.EMP_TEL,
                "emp_email": r.EMP_EMAIL,
                "emp_join": r.EMP_JOIN,
                "emp_acident_cnt": r.EMP_ACIDENT_CNT,
                "emp_board_yn": r.EMP_BOARD_YN,
                "emp_gender": r.EMP_GENDER,
                "emp_endyn": r.EMP_ENDYN,
                "emp_comp": r.EMP_COMP,
            })
        return pd.DataFrame(rows)

    def get_environmental_data(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> pd.DataFrame:
        q = self.db.query(Env)
        if start_year is not None:
            q = q.filter(Env.year >= start_year)
        if end_year is not None:
            q = q.filter(Env.year <= end_year)
        q = q.order_by(Env.year)

        rows = []
        for r in q.all():
            rows.append({
                "year": r.year,
                "energy_use": r.energy_use,
                "green_use": r.green_use,
                "renewable_yn": r.renewable_yn,
                "renewable_ratio": float(r.renewable_ratio) if r.renewable_ratio is not None else None,
            })
        return pd.DataFrame(rows)

    def calculate_social_metrics(self, emp_df: pd.DataFrame) -> Dict[str, Any]:
        if emp_df.empty:
            return {}

        metrics: Dict[str, Any] = {}

        gender_dist = emp_df["emp_gender"].value_counts(dropna=False)
        total_employees = len(emp_df)

        metrics["diversity"] = {
            "total_employees": int(total_employees),
            "male_count": int(gender_dist.get("1", 0)),
            "female_count": int(gender_dist.get("2", 0)),
            "female_ratio": (gender_dist.get("2", 0) / total_employees) if total_employees else 0.0,
        }

        board = emp_df[emp_df["emp_board_yn"] == "Y"]
        board_gender = board["emp_gender"].value_counts(dropna=False)
        metrics["board_composition"] = {
            "total_board_members": int(len(board)),
            "male_board_members": int(board_gender.get("1", 0)),
            "female_board_members": int(board_gender.get("2", 0)),
            "female_board_ratio": (board_gender.get("2", 0) / len(board)) if len(board) else 0.0,
        }

        total_acc = float(emp_df["emp_acident_cnt"].fillna(0).sum())
        metrics["safety"] = {
            "total_accidents": int(total_acc),
            "accident_rate": (total_acc / total_employees) if total_employees else 0.0,
            "zero_accident_employees": int((emp_df["emp_acident_cnt"].fillna(0) == 0).sum()),
        }
        return metrics

    # def calculate_environmental_metrics(self, env_df: pd.DataFrame) -> Dict[str, Any]:
    #     """환경(Environmental) 지표 계산"""
    #     if env_df.empty:
    #         return {}
            
    #     metrics = {}
        
    #     # 최신 데이터
    #     latest_year = env_df['year'].max()
    #     latest_data = env_df[env_df['year'] == latest_year].iloc[0]
        
    #     metrics['current_status'] = {
    #         'latest_year': int(latest_year),
    #         'energy_use': float(latest_data['energy_use']) if latest_data['energy_use'] else 0,
    #         'green_use': float(latest_data['green_use']) if latest_data['green_use'] else 0,
    #         'renewable_yn': latest_data['renewable_yn'],
    #         'renewable_ratio': latest_data['renewable_ratio'] if latest_data['renewable_ratio'] else 0
    #     }
        
    #     return metrics
    
    
    def calculate_environmental_metrics(self, env_df: pd.DataFrame, emp_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """환경(Environmental) 지표 계산"""
        if env_df.empty:
            return {}
        
        metrics = {}
        
        # 최신 데이터
        latest_year = env_df['year'].max()
        latest_data = env_df[env_df['year'] == latest_year].iloc[0]
        
        # 직원 수 계산 (집약도 계산용)
        total_employees = 0
        if emp_df is not None and not emp_df.empty:
            total_employees = len(emp_df[emp_df['emp_endyn'] == 'Y'])  # 재직 중인 직원만
        
        metrics['current_status'] = {
            'latest_year': int(latest_year),
            'energy_use': float(latest_data['energy_use']) if latest_data['energy_use'] else 0,
            'green_use': float(latest_data['green_use']) if latest_data['green_use'] else 0,
            'ghg_emissions': float(latest_data['green_use']) if latest_data['green_use'] else 0,  # green_use를 ghg_emissions로도 매핑
            'renewable_yn': latest_data['renewable_yn'],
            'renewable_ratio': latest_data['renewable_ratio'] if latest_data['renewable_ratio'] else 0,
            'total_employees': total_employees  # 집약도 계산용 직원 수 추가
        }
        
        # 트렌드 분석 추가 (generator.py에서 기대하는 형태)
        trends = []
        for _, row in env_df.iterrows():
            trends.append({
                'year': int(row['year']),
                'energy_use': float(row['energy_use']) if row['energy_use'] else 0,
                'green_use': float(row['green_use']) if row['green_use'] else 0,
                'ghg_emissions': float(row['green_use']) if row['green_use'] else 0,  # green_use를 ghg_emissions로도 매핑
                'renewable_ratio': float(row['renewable_ratio']) if row['renewable_ratio'] else 0  # 재생에너지 비율 추가
            })
        
        metrics['trends'] = trends
        
        return metrics

    def calculate_governance_metrics(self, company_info: Dict[str, Any], emp_df: pd.DataFrame) -> Dict[str, Any]:
        """지배구조(Governance) 지표 계산"""
        metrics = {}
        
        # 전체 사업장의 사외이사 수 합산
        cmp_num = company_info.get('cmp_num')
        total_external_directors = 0
        if cmp_num:
            all_branches = self.db.query(CmpInfo).filter(CmpInfo.cmp_num == cmp_num).all()
            total_external_directors = sum(branch.cmp_extemp or 0 for branch in all_branches)
        
        # 회사 기본 지배구조 정보
        metrics['basic_governance'] = {
            'external_directors': total_external_directors,
            'ethics_policy': company_info.get('cmp_ethics_yn') == 'Y',
            'compliance_policy': company_info.get('cmp_comp_yn') == 'Y'
        }
        
        # 이사회 구성 (generator.py가 기대하는 형태)
        board_df = emp_df[emp_df['emp_board_yn'] == 'Y'] if not emp_df.empty else pd.DataFrame()
        
        metrics['board'] = {
            'inside': len(board_df),  # 사내이사 (직원 중 이사회 멤버)
            'outside': total_external_directors,  # 전체 사업장의 사외이사 합계
            'female': len(board_df[board_df['emp_gender'] == '2']) if not board_df.empty else 0,
            'independent': total_external_directors  # 사외이사 = 독립이사로 가정
        }
        
        return metrics


    # def calculate_governance_metrics(self, company_info: Dict[str, Any], emp_df: pd.DataFrame) -> Dict[str, Any]:
    #     """지배구조(Governance) 지표 계산"""
    #     metrics = {}
        
    #     # 회사 기본 지배구조 정보
    #     metrics['basic_governance'] = {
    #         'external_directors': company_info.get('cmp_extemp', 0),
    #         'ethics_policy': company_info.get('cmp_ethics_yn') == 'Y',
    #         'compliance_policy': company_info.get('cmp_comp_yn') == 'Y'
    #     }
        
    #     return metrics

    def generate_comprehensive_report(self, cmp_num: str, cmp_branch: Optional[str] = None) -> Dict[str, Any]:
        company_info = self.get_company_info(cmp_num, cmp_branch=cmp_branch)
        if not company_info:
            return {"error": f"회사 정보를 찾을 수 없습니다: {cmp_num} / {cmp_branch or '-'}"}

        emp_df = self.get_employee_data(cmp_num=cmp_num)
        env_df = self.get_environmental_data()

        social = self.calculate_social_metrics(emp_df)
        env = self.calculate_environmental_metrics(env_df, emp_df)  # emp_df 전달
        gov = self.calculate_governance_metrics(company_info, emp_df)

        data_summary = {
            "employee_count": int(len(emp_df)),
            "environmental_data_years": int(len(env_df)),
            "latest_env_year": int(env_df["year"].max()) if not env_df.empty else None,
        }

        # report_download.py가 summary 키를 기대하므로 alias도 제공
        return {
            "company_info": company_info,
            "report_generated_at": datetime.now().isoformat(),
            "data_summary": data_summary,
            "summary": data_summary,  # <--- alias
            "esg_metrics": {
                "environmental": env,
                "social": social,
                "governance": gov,
            },
        }

    # 하위 호환성을 위한 메서드
    def get_company_data(self, company_id: str, **kwargs) -> pd.DataFrame:
        """하위 호환성을 위한 메서드 - company_id를 cmp_num으로 처리"""
        env_df = self.get_environmental_data()
        emp_df = self.get_employee_data()
        
        # ESGData 형태로 변환
        esg_data = []
        
        # 환경 데이터 변환
        for _, row in env_df.iterrows():
            esg_data.extend([
                {
                    'category': 'Environmental',
                    'metric_name': 'Energy Use',
                    'value': row['energy_use'],
                    'unit': 'kWh',
                    'reporting_year': row['year']
                },
                {
                    'category': 'Environmental',
                    'metric_name': 'GHG Emissions',
                    'value': row['green_use'],
                    'unit': 'tCO2e',
                    'reporting_year': row['year']
                }
            ])
        
        # 사회 데이터 변환
        if not emp_df.empty:
            social_metrics = self.calculate_social_metrics(emp_df)
            current_year = datetime.now().year
            
            esg_data.append({
                'category': 'Social',
                'metric_name': 'Female Employee Ratio',
                'value': social_metrics.get('diversity', {}).get('female_ratio', 0),
                'unit': '%',
                'reporting_year': current_year
            })
        
        return pd.DataFrame(esg_data)

    def calculate_category_summaries(self, df: pd.DataFrame) -> Dict[str, Any]:
        """카테고리별 요약 통계 계산"""
        if df.empty:
            return {}
        
        summaries = {}
        for category in df['category'].unique():
            category_data = df[df['category'] == category]
            summaries[category] = {
                'total_metrics': len(category_data),
                'latest_year': category_data['reporting_year'].max() if 'reporting_year' in category_data else None
            }
        
        return summaries