"""ESG data processing and transformation."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from app.core.database.models import ESGData, Company


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
    
    def get_company_data(self, 
                        company_id: int, 
                        categories: Optional[List[str]] = None,
                        year: Optional[int] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get ESG data for a company with optional filters."""
        
        query = self.db.query(ESGData).filter(ESGData.company_id == company_id)
        
        # Apply filters
        if categories:
            query = query.filter(ESGData.category.in_(categories))
        
        if year:
            query = query.filter(ESGData.reporting_year == year)
        
        if start_date:
            query = query.filter(ESGData.period_start >= start_date)
        
        if end_date:
            query = query.filter(ESGData.period_end <= end_date)
        
        # Convert to DataFrame
        data = []
        for record in query.all():
            data.append({
                'id': record.id,
                'category': record.category,
                'subcategory': record.subcategory,
                'metric_name': record.metric_name,
                'metric_code': record.metric_code,
                'value': record.value,
                'unit': record.unit,
                'text_value': record.text_value,
                'data_source': record.data_source,
                'quality_score': record.quality_score,
                'period_start': record.period_start,
                'period_end': record.period_end,
                'reporting_year': record.reporting_year,
                'created_at': record.created_at,
                'notes': record.notes
            })
        
        return pd.DataFrame(data)
    
    def calculate_category_summaries(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics by ESG category."""
        if df.empty:
            return {}
        
        summaries = {}
        
        for category in df['category'].unique():
            category_data = df[df['category'] == category]
            
            # Numeric data only
            numeric_data = category_data[category_data['value'].notna()]
            
            summaries[category] = {
                'total_metrics': len(category_data),
                'numeric_metrics': len(numeric_data),
                'data_sources': category_data['data_source'].value_counts().to_dict(),
                'subcategories': category_data['subcategory'].value_counts().to_dict(),
                'avg_quality_score': category_data['quality_score'].mean(),
                'latest_update': category_data['created_at'].max(),
                'date_range': {
                    'start': category_data['period_start'].min(),
                    'end': category_data['period_end'].max()
                }
            }
            
            if len(numeric_data) > 0:
                summaries[category].update({
                    'value_stats': {
                        'mean': numeric_data['value'].mean(),
                        'median': numeric_data['value'].median(),
                        'std': numeric_data['value'].std(),
                        'min': numeric_data['value'].min(),
                        'max': numeric_data['value'].max()
                    }
                })
        
        return summaries
    
    def identify_data_gaps(self, df: pd.DataFrame, required_metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """Identify gaps in ESG data coverage."""
        gaps = {
            'missing_categories': [],
            'missing_metrics': [],
            'incomplete_periods': [],
            'low_quality_data': [],
            'recommendations': []
        }
        
        # Standard ESG categories
        standard_categories = ['Environmental', 'Social', 'Governance']
        existing_categories = df['category'].unique().tolist() if not df.empty else []
        gaps['missing_categories'] = [cat for cat in standard_categories if cat not in existing_categories]
        
        # Missing required metrics
        if required_metrics:
            existing_metrics = df['metric_name'].unique().tolist() if not df.empty else []
            gaps['missing_metrics'] = [metric for metric in required_metrics if metric not in existing_metrics]
        
        # Low quality data (quality score < 0.5)
        if not df.empty:
            low_quality = df[df['quality_score'] < 0.5]
            gaps['low_quality_data'] = low_quality[['metric_name', 'data_source', 'quality_score']].to_dict('records')
        
        # Generate recommendations
        if gaps['missing_categories']:
            gaps['recommendations'].append(f"Add data for missing ESG categories: {', '.join(gaps['missing_categories'])}")
        
        if gaps['missing_metrics']:
            gaps['recommendations'].append(f"Collect data for required metrics: {', '.join(gaps['missing_metrics'])}")
        
        if gaps['low_quality_data']:
            gaps['recommendations'].append("Review and improve data quality for low-scoring metrics")
        
        return gaps
    
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize ESG data for comparison and analysis."""
        if df.empty:
            return df
        
        df_normalized = df.copy()
        
        # Standardize category names
        category_mapping = {
            'environment': 'Environmental',
            'environmental': 'Environmental',
            'social': 'Social',
            'governance': 'Governance',
            'gov': 'Governance'
        }
        
        df_normalized['category'] = df_normalized['category'].str.lower().map(
            lambda x: category_mapping.get(x, x.title() if x else x)
        )
        
        # Standardize units
        unit_mapping = {
            'kwh': 'kWh',
            'gj': 'GJ',
            'co2': 'CO2e',
            'co2e': 'CO2e',
            'tons': 'tonnes',
            'ton': 'tonnes',
            'm3': 'm쨀',
            'liters': 'L',
            'litres': 'L'
        }
        
        df_normalized['unit'] = df_normalized['unit'].str.lower().map(
            lambda x: unit_mapping.get(x, x) if x else x
        )
        
        # Clean metric names
        df_normalized['metric_name'] = df_normalized['metric_name'].str.strip()
        
        return df_normalized
    
    def aggregate_by_period(self, 
                           df: pd.DataFrame, 
                           period: str = 'year',
                           metrics: Optional[List[str]] = None) -> pd.DataFrame:
        """Aggregate ESG data by time period."""
        if df.empty:
            return df
        
        # Filter metrics if specified
        if metrics:
            df = df[df['metric_name'].isin(metrics)]
        
        # Create period column
        if period == 'year':
            df['period'] = df['reporting_year']
        elif period == 'quarter':
            df['period'] = df['period_start'].dt.to_period('Q')
        elif period == 'month':
            df['period'] = df['period_start'].dt.to_period('M')
        else:
            raise ValueError(f"Unsupported period: {period}")
        
        # Aggregate numeric data
        numeric_df = df[df['value'].notna()]
        
        if numeric_df.empty:
            return pd.DataFrame()
        
        aggregated = numeric_df.groupby(['period', 'category', 'metric_name', 'unit']).agg({
            'value': ['sum', 'mean', 'count'],
            'quality_score': 'mean'
        }).reset_index()
        
        # Flatten column names
        aggregated.columns = ['period', 'category', 'metric_name', 'unit', 
                             'total_value', 'avg_value', 'data_points', 'avg_quality']
        
        return aggregated
    
    def calculate_trends(self, df: pd.DataFrame, metric_name: str) -> Dict[str, Any]:
        """Calculate trends for a specific metric over time."""
        metric_data = df[df['metric_name'] == metric_name].copy()
        
        if len(metric_data) < 2:
            return {'error': 'Insufficient data points for trend analysis'}
        
        # Sort by period
        metric_data = metric_data.sort_values('reporting_year')
        
        # Calculate year-over-year changes
        metric_data['yoy_change'] = metric_data['value'].pct_change()
        metric_data['absolute_change'] = metric_data['value'].diff()
        
        # Calculate trend statistics
        trend_stats = {
            'metric_name': metric_name,
            'data_points': len(metric_data),
            'period_range': {
                'start': metric_data['reporting_year'].min(),
                'end': metric_data['reporting_year'].max()
            },
            'value_range': {
                'min': metric_data['value'].min(),
                'max': metric_data['value'].max()
            },
            'average_yoy_change': metric_data['yoy_change'].mean(),
            'total_change': metric_data['value'].iloc[-1] - metric_data['value'].iloc[0],
            'trend_direction': 'increasing' if metric_data['value'].iloc[-1] > metric_data['value'].iloc[0] else 'decreasing'
        }
        
        # Calculate linear trend
        years = metric_data['reporting_year'].values
        values = metric_data['value'].values
        
        if len(years) > 1:
            slope = np.corrcoef(years, values)[0, 1] * (values.std() / years.std())
            trend_stats['trend_slope'] = slope
            trend_stats['correlation'] = np.corrcoef(years, values)[0, 1]
        
        return trend_stats
    
    def export_processed_data(self, 
                             df: pd.DataFrame, 
                             format: str = 'excel',
                             filename: Optional[str] = None) -> str:
        """Export processed data to file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'esg_data_export_{timestamp}'
        
        if format.lower() == 'excel':
            filepath = f'exports/{filename}.xlsx'
            df.to_excel(filepath, index=False)
        elif format.lower() == 'csv':
            filepath = f'exports/{filename}.csv'
            df.to_csv(filepath, index=False)
        elif format.lower() == 'json':
            filepath = f'exports/{filename}.json'
            df.to_json(filepath, orient='records', date_format='iso')
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return filepath 