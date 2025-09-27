"""Dashboard page for ESG overview."""

from nicegui import ui
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from .base_page import BasePage
from app.core.database.models import CmpInfo, EmpInfo, Env


class DashboardPage(BasePage):
    """Modern ESG dashboard with comprehensive metrics and insights."""
    
    async def render(self, db_session: Session, cmp_num: Optional[str] = None) -> None:
        """Render enhanced dashboard page."""
        await super().render(db_session, cmp_num)
        
        # Header section with gradient background
        with ui.row().classes('w-full mb-3'):
            with ui.card().classes('w-full bg-gradient-to-r from-blue-50 to-green-50 border-0 shadow-lg'):
                with ui.card_section().classes('p-8'):
                    ui.icon('dashboard', size='3rem').classes('text-blue-600 mb-4')
                    ui.label('ESG Dashboard').classes('text-4xl font-bold text-gray-800 mb-2')
                    ui.label('Environmental, Social & Governance Insights').classes('text-lg text-gray-600')
        
        if not cmp_num:
            cmp_num = "6182618882"

            # self._render_empty_state()
            # return
        
        # Get company information
        company = db_session.query(CmpInfo).filter_by(cmp_num=cmp_num).first()
        if not company:
            self._render_company_not_found()
            return
        
        # Company header card
        await self._render_company_header(company)
        
        # Key metrics overview cards
        await self._render_metrics_overview(db_session, cmp_num)
        
        # ESG category sections
        await self._render_esg_categories(db_session, cmp_num)
        
        # Recent activity and alerts
        await self._render_activity_section(db_session, cmp_num)
    
    def _render_empty_state(self) -> None:
        """Render empty state when no company is selected."""
        with ui.card().classes('w-full p-12 text-center bg-gray-50 border-2 border-dashed border-gray-300'):
            ui.icon('business_center', size='5rem').classes('text-gray-400 mb-6')
            ui.label('회사를 선택해주세요').classes('text-2xl font-semibold text-gray-700 mb-3')
            ui.label('상단 드롭다운에서 분석할 회사를 선택하여 ESG 대시보드를 확인하세요.').classes('text-base text-gray-500')
    
    def _render_company_not_found(self) -> None:
        """Render error state when company is not found."""
        with ui.card().classes('w-full p-8 text-center bg-red-50 border border-red-200'):
            ui.icon('error_outline', size='3rem').classes('text-red-500 mb-4')
            ui.label('회사 정보를 찾을 수 없습니다').classes('text-xl font-semibold text-red-700 mb-2')
            ui.label('선택한 회사의 데이터가 존재하지 않습니다.').classes('text-sm text-red-600')
    
    async def _render_company_header(self, company: CmpInfo) -> None:
        """Render company information header."""
        with ui.card().classes('w-full mb-6 bg-white shadow-md hover:shadow-lg transition-shadow'):
            with ui.card_section().classes('p-6'):
                with ui.row().classes('w-full items-center justify-between'):
                    with ui.column().classes('flex-grow'):
                        ui.label(company.cmp_nm).classes('text-2xl font-bold text-gray-800 mb-2')
                        with ui.row().classes('gap-6'):
                            if company.cmp_industry:
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('business', size='1.2rem').classes('text-blue-500')
                                    ui.label(f'업종: {company.cmp_industry}').classes('text-sm text-gray-600')
                            if company.cmp_sector:
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('category', size='1.2rem').classes('text-green-500')
                                    ui.label(f'산업: {company.cmp_sector}').classes('text-sm text-gray-600')
                    
                    # ESG Score badge (placeholder)
                    with ui.column().classes('items-end'):
                        ui.label('ESG 종합점수').classes('text-sm text-gray-500 mb-1')
                        with ui.badge().classes('bg-green-500 text-white px-4 py-2 text-lg font-bold'):
                            ui.label('A-')
    
    async def _render_metrics_overview(self, db_session: Session, cmp_num: str) -> None:
        """Render key metrics overview cards."""
        # Calculate key metrics
        total_employees = db_session.query(func.count(EmpInfo.EMP_ID)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y')
        ).scalar() or 0
        
        female_count = db_session.query(func.count(EmpInfo.EMP_ID)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y', EmpInfo.EMP_GENDER == '2')
        ).scalar() or 0
        
        board_members = db_session.query(func.count(EmpInfo.EMP_ID)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y', EmpInfo.EMP_BOARD_YN == 'Y')
        ).scalar() or 0
        
        accident_count = db_session.query(func.sum(EmpInfo.EMP_ACIDENT_CNT)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y')
        ).scalar() or 0
        
        # Latest environmental data
        latest_env = db_session.query(Env).order_by(Env.year.desc()).first()
        
        # Calculate percentages
        female_ratio = (female_count / total_employees * 100) if total_employees > 0 else 0
        accident_rate = (accident_count / total_employees * 100) if total_employees > 0 else 0
        
        with ui.row().classes('w-full gap-6 mb-8'):
            # Social metrics
            self._create_metric_card(
                icon='people',
                title='직원 현황',
                value=f'{total_employees:,}명',
                subtitle=f'여성 비율: {female_ratio:.1f}%',
                color='blue',
                trend='+5%'
            )
            
            self._create_metric_card(
                icon='account_balance',
                title='이사회 구성',
                value=f'{board_members}명',
                subtitle='이사회 참여 임직원',
                color='purple',
                trend='신규 1명'
            )
            
            self._create_metric_card(
                icon='health_and_safety',
                title='안전 지표',
                value=f'{accident_rate:.2f}%',
                subtitle=f'총 {accident_count}건 발생',
                color='orange',
                trend='-15%' if accident_rate < 5 else '+8%'
            )
            
            self._create_metric_card(
                icon='eco',
                title='환경 성과',
                value=f'{latest_env.energy_use:,.0f}kWh' if latest_env and latest_env.energy_use else 'N/A',
                subtitle=f'{latest_env.year}년 기준' if latest_env else '데이터 없음',
                color='green',
                trend='-12%' if latest_env else 'N/A'
            )
    
    def _create_metric_card(self, icon: str, title: str, value: str, subtitle: str, color: str, trend: str) -> None:
        """Create a metric card with icon, value, and trend."""
        color_classes = {
            'blue': 'bg-blue-500 text-blue-500 bg-blue-50',
            'purple': 'bg-purple-500 text-purple-500 bg-purple-50', 
            'orange': 'bg-orange-500 text-orange-500 bg-orange-50',
            'green': 'bg-green-500 text-green-500 bg-green-50'
        }
        
        bg_color = color_classes[color].split()[0]
        icon_color = color_classes[color].split()[1]
        card_bg = color_classes[color].split()[2]
        
        with ui.card().classes(f'flex-1 {card_bg} border-0 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105'):
            with ui.card_section().classes('p-6'):
                with ui.row().classes('w-full items-start justify-between mb-4'):
                    ui.icon(icon, size='2.5rem').classes(f'{icon_color} {bg_color} p-2 rounded-lg')
                    if trend != 'N/A':
                        trend_color = 'text-green-600' if trend.startswith('-') or 'new' in trend.lower() else 'text-red-600'
                        ui.label(trend).classes(f'text-sm font-semibold {trend_color}')
                
                ui.label(title).classes('text-sm font-medium text-gray-600 mb-2')
                ui.label(value).classes('text-2xl font-bold text-gray-800 mb-1')
                ui.label(subtitle).classes('text-xs text-gray-500')
    
    async def _render_esg_categories(self, db_session: Session, cmp_num: str) -> None:
        """Render detailed ESG category sections."""
        with ui.row().classes('w-full gap-6 mb-8'):
            # Environmental section
            with ui.card().classes('flex-1 bg-gradient-to-br from-green-50 to-emerald-100 border-0 shadow-lg'):
                with ui.card_section().classes('p-6'):
                    with ui.row().classes('w-full items-center mb-4'):
                        ui.icon('eco', size='2rem').classes('text-green-600 mr-3')
                        ui.label('Environmental').classes('text-xl font-bold text-gray-800')
                        ui.badge('A-').classes('bg-green-500 text-white ml-auto')
                    
                    await self._render_environmental_details(db_session)
            
            # Social section  
            with ui.card().classes('flex-1 bg-gradient-to-br from-blue-50 to-sky-100 border-0 shadow-lg'):
                with ui.card_section().classes('p-6'):
                    with ui.row().classes('w-full items-center mb-4'):
                        ui.icon('people', size='2rem').classes('text-blue-600 mr-3')
                        ui.label('Social').classes('text-xl font-bold text-gray-800')
                        ui.badge('A').classes('bg-blue-500 text-white ml-auto')
                    
                    await self._render_social_details(db_session, cmp_num)
            
            # Governance section
            with ui.card().classes('flex-1 bg-gradient-to-br from-purple-50 to-violet-100 border-0 shadow-lg'):
                with ui.card_section().classes('p-6'):
                    with ui.row().classes('w-full items-center mb-4'):
                        ui.icon('account_balance', size='2rem').classes('text-purple-600 mr-3')
                        ui.label('Governance').classes('text-xl font-bold text-gray-800')
                        ui.badge('B').classes('bg-purple-500 text-white ml-auto')
                    
                    await self._render_governance_details(db_session, cmp_num)
    
    async def _render_environmental_details(self, db_session: Session) -> None:
        """Render environmental metrics details."""
        recent_env = db_session.query(Env).order_by(Env.year.desc()).limit(3).all()
        
        if recent_env:
            for env in recent_env:
                with ui.row().classes('w-full items-center justify-between py-2 border-b border-green-200 last:border-b-0'):
                    ui.label(f'{env.year}년').classes('text-sm font-medium text-gray-700')
                    if env.energy_use:
                        ui.label(f'{env.energy_use:,.0f} kWh').classes('text-sm text-gray-600')
                
            # Renewable energy status
            if recent_env[0].renewable_yn == 'Y':
                with ui.row().classes('w-full items-center mt-4 p-3 bg-green-100 rounded-lg'):
                    ui.icon('wb_sunny', size='1.2rem').classes('text-green-600 mr-2')
                    ui.label(f'재생에너지 {recent_env[0].renewable_ratio or 0:.1f}% 사용').classes('text-sm font-medium text-green-800')
        else:
            ui.label('환경 데이터가 없습니다').classes('text-sm text-gray-500 italic')
    
    async def _render_social_details(self, db_session: Session, cmp_num: str) -> None:
        """Render social metrics details."""
        # Gender diversity
        male_count = db_session.query(func.count(EmpInfo.EMP_ID)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y', EmpInfo.EMP_GENDER == '1')
        ).scalar() or 0
        
        female_count = db_session.query(func.count(EmpInfo.EMP_ID)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y', EmpInfo.EMP_GENDER == '2')
        ).scalar() or 0
        
        with ui.row().classes('w-full items-center justify-between py-2 border-b border-blue-200'):
            ui.label('남성 직원').classes('text-sm font-medium text-gray-700')
            ui.label(f'{male_count}명').classes('text-sm text-gray-600')
        
        with ui.row().classes('w-full items-center justify-between py-2 border-b border-blue-200'):
            ui.label('여성 직원').classes('text-sm font-medium text-gray-700')
            ui.label(f'{female_count}명').classes('text-sm text-gray-600')
        
        # Safety metrics
        total_accidents = db_session.query(func.sum(EmpInfo.EMP_ACIDENT_CNT)).filter(
            and_(EmpInfo.EMP_COMP == cmp_num, EmpInfo.EMP_ENDYN == 'Y')
        ).scalar() or 0
        
        if total_accidents == 0:
            with ui.row().classes('w-full items-center mt-4 p-3 bg-blue-100 rounded-lg'):
                ui.icon('verified', size='1.2rem').classes('text-blue-600 mr-2')
                ui.label('무재해 사업장').classes('text-sm font-medium text-blue-800')
    
    async def _render_governance_details(self, db_session: Session, cmp_num: str) -> None:
        """Render governance metrics details."""
        company = db_session.query(CmpInfo).filter_by(cmp_num=cmp_num).first()
        
        if company:
            # External directors
            if company.cmp_extemp:
                with ui.row().classes('w-full items-center justify-between py-2 border-b border-purple-200'):
                    ui.label('사외이사').classes('text-sm font-medium text-gray-700')
                    ui.label(f'{company.cmp_extemp}명').classes('text-sm text-gray-600')
            
            # Ethics and compliance
            policies = []
            if company.cmp_ethics_yn == 'Y':
                policies.append('윤리경영')
            if company.cmp_comp_yn == 'Y':  
                policies.append('컴플라이언스')
            
            if policies:
                with ui.row().classes('w-full items-center mt-4 p-3 bg-purple-100 rounded-lg'):
                    ui.icon('policy', size='1.2rem').classes('text-purple-600 mr-2')
                    ui.label(f'{", ".join(policies)} 정책 운영').classes('text-sm font-medium text-purple-800')
        
        ui.label('지배구조 체계 운영 중').classes('text-sm text-gray-500 italic mt-2')
    
    async def _render_activity_section(self, db_session: Session, cmp_num: str) -> None:
        """Render recent activity and recommendations."""
        with ui.row().classes('w-full gap-6'):
            # Recent activity
            with ui.card().classes('flex-1 bg-white shadow-md'):
                with ui.card_section().classes('p-6'):
                    with ui.row().classes('w-full items-center mb-4'):
                        ui.icon('notifications', size='1.5rem').classes('text-gray-600 mr-2')
                        ui.label('최근 활동').classes('text-lg font-semibold text-gray-800')
                    
                    activities = [
                        ('환경 데이터 업데이트', '2시간 전', 'eco', 'text-green-500'),
                        ('직원 안전교육 완료', '1일 전', 'school', 'text-blue-500'),
                        ('이사회 회의록 등록', '3일 전', 'description', 'text-purple-500')
                    ]
                    
                    for activity, time, icon, color in activities:
                        with ui.row().classes('w-full items-center py-3 border-b border-gray-100 last:border-b-0'):
                            ui.icon(icon, size='1.2rem').classes(f'{color} mr-3')
                            with ui.column().classes('flex-grow'):
                                ui.label(activity).classes('text-sm font-medium text-gray-700')
                                ui.label(time).classes('text-xs text-gray-500')
            
            # Recommendations
            with ui.card().classes('flex-1 bg-amber-50 border border-amber-200 shadow-md'):
                with ui.card_section().classes('p-6'):
                    with ui.row().classes('w-full items-center mb-4'):
                        ui.icon('lightbulb', size='1.5rem').classes('text-amber-600 mr-2')
                        ui.label('개선 제안').classes('text-lg font-semibold text-gray-800')
                    
                    recommendations = [
                        '재생에너지 사용 비율 확대 검토',
                        '여성 이사 선임 고려', 
                        '안전교육 프로그램 강화'
                    ]
                    
                    for i, rec in enumerate(recommendations, 1):
                        with ui.row().classes('w-full items-start py-2'):
                            ui.label(f'{i}.').classes('text-sm font-medium text-amber-700 mr-2 mt-1')
                            ui.label(rec).classes('text-sm text-gray-700 flex-grow')
