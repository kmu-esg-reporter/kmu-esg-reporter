"""Company management page with table and add dialog."""

from nicegui import ui
from sqlalchemy.orm import Session
from typing import Optional
import datetime
import pandas as pd
import io
import os
from pathlib import Path

from .base_page import BasePage
from app.core.database.models import CmpInfo


class CompanyManagementPage(BasePage):
    async def render(self, db_session: Session, company_num: Optional[str] = None) -> None:
        ui.label('🏢 회사관리').classes('text-2xl font-bold text-blue-600 mb-4')

        companies = []
        if db_session:
            db_companies = db_session.query(CmpInfo).all()
            for c in db_companies:
                companies.append({
                    '사업장번호': c.cmp_num or '',
                    '지점': c.cmp_branch or '',
                    '회사명': c.cmp_nm,
                    '업종': c.cmp_industry or '',
                    '산업': c.cmp_sector or '',
                    '주소': c.cmp_addr or '',
                    '사외 이사회 수': c.cmp_extemp or 0,
                    '윤리경영 여부': c.cmp_ethics_yn,
                    '컴플라이언스 정책 여부': c.cmp_comp_yn,
                    'unique_key': f"{c.cmp_num}_{c.cmp_branch}",  # 복합키용 유니크 키
                    'actions': '수정'  # 액션 컬럼 추가
                })

        # =======================
        # 테이블 정의
        # =======================
        columns = [
            {'name': '사업장번호', 'label': '사업장번호', 'field': '사업장번호', 'align': 'center'},
            {'name': '회사명', 'label': '회사명', 'field': '회사명', 'align': 'center'},
            {'name': '지점', 'label': '지점', 'field': '지점', 'align': 'center'},
            {'name': '업종', 'label': '업종', 'field': '업종', 'align': 'center'},
            {'name': '산업', 'label': '산업', 'field': '산업', 'align': 'center'},
            {'name': '주소', 'label': '주소', 'field': '주소', 'align': 'center'},
            {'name': '사외 이사회 수', 'label': '사외 이사회 수', 'field': '사외 이사회 수', 'align': 'center'},
            {'name': '윤리경영 여부', 'label': '윤리경영 여부', 'field': '윤리경영 여부', 'align': 'center'},
            {'name': '컴플라이언스 정책 여부', 'label': '컴플라이언스 정책 여부', 'field': '컴플라이언스 정책 여부', 'align': 'center'},
            {'name': 'actions', 'label': '수정', 'field': 'actions', 'align': 'center'},
        ]

        # =======================
        # 검색 / 필터 UI
        # =======================
        original_companies = companies.copy()
        filtered_companies = companies.copy()

        def apply_filters():
            nonlocal filtered_companies
            filtered_companies = original_companies.copy()

            # 지점 검색 (SELECT BOX)
            if branch_input.value and branch_input.value != '전체':
                filtered_companies = [r for r in filtered_companies if r['지점'] == branch_input.value]
            
            # 업종 검색
            if industry_input.value:
                filtered_companies = [r for r in filtered_companies if industry_input.value.upper() in str(r['업종']).upper()]
            
            # 산업 검색
            if sector_input.value:
                filtered_companies = [r for r in filtered_companies if sector_input.value.upper() in str(r['산업']).upper()]
            
            # 주소 검색
            if address_input.value:
                filtered_companies = [r for r in filtered_companies if address_input.value.upper() in str(r['주소']).upper()]

            # 사외 이사회 수 범위 검색
            if extemp_min_input.value is not None:
                filtered_companies = [r for r in filtered_companies if r['사외 이사회 수'] >= extemp_min_input.value]
            if extemp_max_input.value is not None:
                filtered_companies = [r for r in filtered_companies if r['사외 이사회 수'] <= extemp_max_input.value]

            # 윤리경영 여부 필터
            if ethics_select.value and ethics_select.value != '전체':
                filtered_companies = [r for r in filtered_companies if r['윤리경영 여부'] == ethics_select.value]

            # 컴플라이언스 정책 여부 필터
            if compliance_select.value and compliance_select.value != '전체':
                filtered_companies = [r for r in filtered_companies if r['컴플라이언스 정책 여부'] == compliance_select.value]

            table.rows = filtered_companies
            table.update()
            result_count.text = f'검색 결과: {len(filtered_companies)}건'

        def reset_filters():
            branch_input.set_value('전체')
            industry_input.set_value('')
            sector_input.set_value('')
            address_input.set_value('')
            extemp_min_input.set_value(None)
            extemp_max_input.set_value(None)
            ethics_select.set_value('전체')
            compliance_select.set_value('전체')

            table.rows = original_companies
            table.update()
            result_count.text = f'검색 결과: {len(original_companies)}건'

       # =======================
        # 검색 UI 카드 (사업자번호, 회사명 제거)
        # =======================
        with ui.card().classes('w-full p-2 mb-4 rounded-xl shadow-sm bg-gray-50 text-xs'):
            with ui.row().classes('items-center justify-between mb-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.icon('tune', size='1rem').classes('text-blue-600')
                    ui.label('검색 필터').classes('text-sm font-semibold text-gray-700')
                result_count = ui.label(f'검색 결과: {len(companies)}건').classes('text-xs text-gray-500')

            uniform_width = 'w-24 h-7 text-xs'

            # row + wrap → 화면에 맞게 자동 줄바꿈
            with ui.row().classes('items-center gap-4 flex-wrap'):
                ui.label('지점').classes('text-xs font-medium text-gray-600')
                # 현재 회사 데이터에서 지점 목록 추출
                available_branches = list(set([c['지점'] for c in companies if c['지점']]))
                available_branches.sort()  # 정렬
                branch_options = ['전체'] + available_branches
                branch_input = ui.select(branch_options, value='전체') \
                    .props('outlined dense clearable').classes('w-30 h-7 text-xs')

                ui.label('업종').classes('text-xs font-medium text-gray-600')
                industry_input = ui.input(placeholder='업종').props('outlined dense clearable').classes(uniform_width)

                ui.label('산업').classes('text-xs font-medium text-gray-600')
                sector_input = ui.input(placeholder='산업').props('outlined dense clearable').classes(uniform_width)

                ui.label('주소').classes('text-xs font-medium text-gray-600')
                address_input = ui.input(placeholder='주소').props('outlined dense clearable').classes(uniform_width)

                ui.label('이사회수').classes('text-xs font-medium text-gray-600')
                with ui.row().classes('items-center gap-1'):
                    extemp_min_input = ui.number(placeholder='최소', precision=0, min=0) \
                        .props('outlined dense clearable').classes(uniform_width)
                    ui.label('~').classes('text-gray-400 text-xs')
                    extemp_max_input = ui.number(placeholder='최대', precision=0, min=0) \
                        .props('outlined dense clearable').classes(uniform_width)

                ui.label('윤리경영').classes('text-xs font-medium text-gray-600')
                ethics_select = ui.select(['전체', 'Y', 'N'], value='전체') \
                    .props('outlined dense clearable').classes('w-28 h-7 text-xs')

                ui.label('컴플라이언스').classes('text-xs font-medium text-gray-600')
                compliance_select = ui.select(['전체', 'Y', 'N'], value='전체') \
                    .props('outlined dense clearable').classes('w-28 h-7 text-xs')

                # 버튼들을 오른쪽으로 밀어서 배치
                with ui.row().classes('items-center gap-2 ml-auto'):
                    ui.button('검색', color='primary', on_click=apply_filters) \
                        .classes('rounded-md shadow-sm px-4 py-2 text-sm font-medium')
                    ui.button('초기화', color='secondary', on_click=reset_filters) \
                        .classes('rounded-md shadow-sm px-4 py-2 text-sm font-medium')

        # =======================
        # 회사 등록/수정 다이얼로그
        # =======================
        edit_mode = False
        current_company = None
        dialog_title = ui.label()

        with ui.dialog() as dialog, ui.card().classes('p-6 w-[600px]'):
            inputs = {}

            def setup_dialog(company_data=None):
                nonlocal edit_mode, current_company
                edit_mode = company_data is not None
                current_company = company_data
                
                # if edit_mode:
                #     dialog_title.text = '📝 회사 수정'
                #     dialog_title.classes('text-xl font-bold text-blue-600 mb-4')
                # else:
                #     dialog_title.text = '📝 회사 등록'
                #     dialog_title.classes('text-xl font-bold text-blue-600 mb-4')

                # 기존 데이터로 폼 채우기
                if company_data:
                    inputs['cmp_num'].set_value(company_data.get('사업장번호', '6182618882'))
                    inputs['cmp_nm'].set_value(company_data.get('회사명', '국민AI 주식회사'))
                    inputs['cmp_branch'].set_value(company_data.get('지점', ''))
                    inputs['cmp_industry'].set_value(company_data.get('업종', ''))
                    inputs['cmp_sector'].set_value(company_data.get('산업', ''))
                    inputs['cmp_addr'].set_value(company_data.get('주소', ''))
                    inputs['cmp_extemp'].set_value(company_data.get('사외 이사회 수', 0))
                    inputs['cmp_ethics_yn'].set_value(company_data.get('윤리경영 여부', 'N'))
                    inputs['cmp_comp_yn'].set_value(company_data.get('컴플라이언스 정책 여부', 'N'))
                else:
                    # 신규 등록 시 기본값 설정
                    inputs['cmp_num'].set_value('6182618882')
                    inputs['cmp_nm'].set_value('국민AI 주식회사')
                    inputs['cmp_branch'].set_value('')
                    inputs['cmp_industry'].set_value('')
                    inputs['cmp_sector'].set_value('')
                    inputs['cmp_addr'].set_value('')
                    inputs['cmp_extemp'].set_value(0)
                    inputs['cmp_ethics_yn'].set_value('N')
                    inputs['cmp_comp_yn'].set_value('N')

            # 입력 필드 - 사업장번호와 회사명은 숨김 처리
            # 사업장번호는 고정값으로 설정 (6182618882)
            inputs['cmp_num'] = ui.input(value='6182618882').style('display: none')  # 숨김 처리
            # 회사명은 고정값으로 설정 (국민AI 주식회사)
            inputs['cmp_nm'] = ui.input(value='국민AI 주식회사').style('display: none')  # 숨김 처리
            inputs['cmp_branch'] = ui.input(label='지점', placeholder='지점명 입력 (예: 서울본사, 부산지사)').props('outlined dense').classes('w-full mb-3')
            inputs['cmp_industry'] = ui.input(label='업종', placeholder='업종 입력').props('outlined dense').classes('w-full mb-3')
            inputs['cmp_sector'] = ui.input(label='산업', placeholder='산업 입력').props('outlined dense').classes('w-full mb-3')
            inputs['cmp_addr'] = ui.input(label='주소', placeholder='주소 입력').props('outlined dense').classes('w-full mb-3')
            inputs['cmp_extemp'] = ui.number(label='사외 이사회 수', placeholder='숫자 입력', min=0).props('outlined dense').classes('w-full mb-3')

            # 토글 스위치
            with ui.row().classes('items-center gap-4 w-full mb-3'):
                ui.label('윤리경영 여부').classes('text-sm font-medium text-gray-700')
                inputs['cmp_ethics_yn'] = ui.toggle(['Y', 'N'], value='N').classes('ml-auto')

            with ui.row().classes('items-center gap-4 w-full mb-3'):
                ui.label('컴플라이언스 정책 여부').classes('text-sm font-medium text-gray-700')
                inputs['cmp_comp_yn'] = ui.toggle(['Y', 'N'], value='N').classes('ml-auto')

            # 저장/수정 로직
            def save_company():
                try:
                    if edit_mode and current_company:
                        # 기존 회사 정보 수정 - 복합키로 정확히 찾기
                        cmp_num = current_company.get('사업장번호')
                        cmp_branch = current_company.get('지점', '')  # 빈 값일 수도 있음
                        
                        existing_company = db_session.query(CmpInfo).filter(
                            CmpInfo.cmp_num == cmp_num,
                            CmpInfo.cmp_branch == cmp_branch
                        ).first()
                        
                        if existing_company:
                            # 업데이트할 필드들
                            existing_company.cmp_branch = inputs['cmp_branch'].value or ''  # 빈 값 허용
                            existing_company.cmp_industry = inputs['cmp_industry'].value or ''
                            existing_company.cmp_sector = inputs['cmp_sector'].value or ''
                            existing_company.cmp_addr = inputs['cmp_addr'].value or ''
                            existing_company.cmp_extemp = int(inputs['cmp_extemp'].value or 0)
                            existing_company.cmp_ethics_yn = inputs['cmp_ethics_yn'].value
                            existing_company.cmp_comp_yn = inputs['cmp_comp_yn'].value
                            
                            db_session.commit()
                            ui.notify(f"{existing_company.cmp_nm} 회사 정보가 수정되었습니다 ✅", type='positive')
                            
                            # 테이블 데이터만 새로고침
                            refresh_table_data()
                        else:
                            ui.notify("수정할 회사를 찾을 수 없습니다", type='negative')
                    else:
                        # 신규 회사 등록
                        new_company = CmpInfo(
                            cmp_num=inputs['cmp_num'].value,
                            cmp_branch=inputs['cmp_branch'].value or '',
                            cmp_nm=inputs['cmp_nm'].value,
                            cmp_industry=inputs['cmp_industry'].value or '',
                            cmp_sector=inputs['cmp_sector'].value or '',
                            cmp_addr=inputs['cmp_addr'].value or '',
                            cmp_extemp=int(inputs['cmp_extemp'].value or 0),
                            cmp_ethics_yn=inputs['cmp_ethics_yn'].value,
                            cmp_comp_yn=inputs['cmp_comp_yn'].value
                        )
                        db_session.add(new_company)
                        db_session.commit()
                        ui.notify(f"{new_company.cmp_nm} 회사가 등록되었습니다 ✅", type='positive')
                        
                        # 테이블 데이터만 새로고침
                        refresh_table_data()
                    
                    dialog.close()
                except Exception as e:
                    ui.notify(f"저장 중 오류: {str(e)}", type='negative')
                    if db_session:
                        db_session.rollback()

            # 버튼들
            with ui.row().classes('justify-end mt-4 gap-3'):
                ui.button('저장', on_click=save_company).props('color=primary text-color=white').classes('px-6 py-2 rounded-lg')
                ui.button('취소', on_click=dialog.close).props('color=negative text-color=white').classes('px-6 py-2 rounded-lg')

        # 테이블 새로고침 함수
        def refresh_table_data():
            """테이블 데이터만 새로고침"""
            nonlocal original_companies, filtered_companies
            updated_companies = []
            if db_session:
                db_companies = db_session.query(CmpInfo).all()
                for c in db_companies:
                    updated_companies.append({
                        '사업장번호': c.cmp_num or '',
                        '지점': c.cmp_branch or '',
                        '회사명': c.cmp_nm,
                        '업종': c.cmp_industry or '',
                        '산업': c.cmp_sector or '',
                        '주소': c.cmp_addr or '',
                        '사외 이사회 수': c.cmp_extemp or 0,
                        '윤리경영 여부': c.cmp_ethics_yn,
                        '컴플라이언스 정책 여부': c.cmp_comp_yn,
                        'unique_key': f"{c.cmp_num}_{c.cmp_branch}",
                        'actions': '수정'
                    })
            original_companies = updated_companies
            # 필터 재적용
            apply_filters()

        # 테이블 생성
        table = ui.table(columns=columns, rows=filtered_companies, row_key='unique_key').classes(
            'w-full text-center bordered dense flat rounded shadow-sm'
        ).props('table-header-class=bg-blue-200 text-black')
        
        # 각 행의 액션 컬럼에 수정 버튼 추가
        table.add_slot('body-cell-actions', '''
            <q-td key="actions" :props="props">
                <q-btn 
                    @click="$parent.$emit('edit_row', props.row)" 
                    dense 
                    round 
                    flat 
                    color="primary" 
                    icon="edit"
                    size="sm">
                    <q-tooltip>수정</q-tooltip>
                </q-btn>
            </q-td>
        ''')
        
        # 수정 버튼 클릭 이벤트 처리
        def on_edit_row(e):
            row_data = e.args
            if row_data:
                setup_dialog(row_data)
                dialog.open()
        
        table.on('edit_row', on_edit_row)

        # =======================
        # 엑셀 일괄등록 다이얼로그
        # =======================
        with ui.dialog() as excel_dialog, ui.card().classes('p-6 w-[700px]'):
            ui.label('📄 엑셀 일괄등록').classes('text-xl font-bold text-green-600 mb-4')
            
            # 엑셀 템플릿 안내
            with ui.card().classes('p-4 mb-4 bg-blue-50'):
                ui.label('📝 엑셀 파일 형식 안내').classes('text-lg font-bold text-blue-600')
                # ui.label('• 첫 번째 행은 헤더로 사용됩니다.').classes('text-sm mt-2')
                # ui.label('• 열 이름의 공백은 자동으로 제거됩니다. (예: "사외 이사회 수" → "사외이사회수")').classes('text-sm')
                # # ui.label('• 사업장번호와 회사명은 고정값으로 자동 설정됩니다.').classes('text-sm')
                
                # # 필수 열 안내
                # ui.label('📄 필수 열 목록:').classes('text-sm font-bold mt-3')
                # required_columns = [
                #     '지점', '업종', '산업', '주소', 
                #     '사외이사회수', '윤리경영여부', '컴플라이언스정책여부'
                # ]
                # for i, col in enumerate(required_columns, 1):
                #     ui.label(f'{i}. {col}').classes('text-sm ml-4')
                
                ui.label('⚠️ 윤리경영여부, 컴플라이언스정책여부는 Y 또는 N으로 입력해주세요.').classes('text-sm text-orange-600 mt-2')
                ui.label('💡 열 이름에 공백이 있어도 자동으로 처리됩니다.').classes('text-sm text-blue-600 mt-1')
            
            # 엑셀 양식 다운로드 버튼
            def download_template():
                try:
                    # 엑셀 양식 데이터 생성
                    template_data = {
                        '지점': ['서울지사', '구미지사'],
                        '업종': ['제조업', '서비스업'],
                        '산업': ['전자부품', 'IT서비스'],
                        '주소': ['서울시 강남구 테헤란로 123', '경북 구미시 산업로 456'],
                        '사외이사회수': [3, 2],
                        '윤리경영여부': ['Y', 'N'],
                        '컴플라이언스정책여부': ['Y', 'Y']
                    }
                    
                    # DataFrame 생성
                    template_df = pd.DataFrame(template_data)
                    
                    # 메모리에 엑셀 파일 생성
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        template_df.to_excel(writer, sheet_name='회사정보양식', index=False)
                    
                    # 파일 다운로드
                    output.seek(0)
                    ui.download(output.getvalue(), filename='회사정보_업로드양식.xlsx')
                    ui.notify('✅ 엑셀 양식이 다운로드되었습니다', type='positive')
                    
                except Exception as e:
                    ui.notify(f'❌ 양식 다운로드 오류: {str(e)}', type='negative')
            
            with ui.row().classes('w-full justify-center mb-4'):
                ui.button('📥 엑셀 양식 다운로드', on_click=download_template) \
                    .props('color=blue-200 text-color=black').classes('rounded-lg shadow-md px-4 py-2')
            
            # 파일 업로드
            upload_result = ui.label()
            preview_data = []
            preview_table = None
            
            def handle_upload(e):
                nonlocal preview_data, preview_table
                try:
                    upload_result.text = '파일 처리 중...'
                    upload_result.classes('text-blue-600')
                    
                    # 업로드된 파일 읽기
                    content = e.content.read()
                    
                    # 엑셀 파일 파싱
                    try:
                        # 엑셀 파일 읽기 (첫 번째 시트)
                        df = pd.read_excel(io.BytesIO(content), sheet_name=0)
                        
                        # 열 이름 정리 (모든 공백 제거)
                        df.columns = df.columns.str.replace(' ', '').str.strip()
                        
                        # 필수 열 확인 (공백 제거된 버전)
                        required_cols = ['지점', '업종', '산업', '주소', '사외이사회수', '윤리경영여부', '컴플라이언스정책여부']
                        missing_cols = [col for col in required_cols if col not in df.columns]
                        
                        if missing_cols:
                            upload_result.text = f'❌ 누락된 열: {", ".join(missing_cols)}'
                            upload_result.classes('text-red-600')
                            return
                        
                        # 데이터 검증 및 임시 저장
                        preview_data = []
                        valid_count = 0
                        error_count = 0
                        error_messages = []
                        
                        for idx, row in df.iterrows():
                            try:
                                # 데이터 검증
                                branch = str(row['지점']).strip() if pd.notna(row['지점']) else ''
                                industry = str(row['업종']).strip() if pd.notna(row['업종']) else ''
                                sector = str(row['산업']).strip() if pd.notna(row['산업']) else ''
                                addr = str(row['주소']).strip() if pd.notna(row['주소']) else ''
                                
                                # 사외이사회수 처리
                                try:
                                    extemp = int(float(row['사외이사회수'])) if pd.notna(row['사외이사회수']) else 0
                                except (ValueError, TypeError):
                                    extemp = 0
                                
                                # Y/N 값 처리
                                ethics_yn = str(row['윤리경영여부']).strip().upper() if pd.notna(row['윤리경영여부']) else 'N'
                                comp_yn = str(row['컴플라이언스정책여부']).strip().upper() if pd.notna(row['컴플라이언스정책여부']) else 'N'
                                
                                # Y/N 값 유효성 검사
                                if ethics_yn not in ['Y', 'N']:
                                    ethics_yn = 'N'
                                if comp_yn not in ['Y', 'N']:
                                    comp_yn = 'N'
                                
                                # 유효한 데이터를 임시 저장
                                preview_data.append({
                                    '사업장번호': '6182618882',
                                    '지점': branch,
                                    '회사명': '국민AI 주식회사',
                                    '업종': industry,
                                    '산업': sector,
                                    '주소': addr,
                                    '사외 이사회 수': extemp,
                                    '윤리경영 여부': ethics_yn,
                                    '컴플라이언스 정책 여부': comp_yn,
                                    '상태': '업로드 대기'
                                })
                                valid_count += 1
                                
                            except Exception as row_error:
                                error_count += 1
                                error_messages.append(f'행 {idx + 2}: {str(row_error)}')
                        
                        # 결과 메시지
                        if error_count == 0:
                            upload_result.text = f'✅ 검증 완료: {valid_count}건의 유효한 데이터가 준비되었습니다.'
                            upload_result.classes('text-green-600')
                        else:
                            upload_result.text = f'⚠️ 부분 성공: {valid_count}건 유효, {error_count}건 오류\n오류: {"; ".join(error_messages[:3])}'
                            upload_result.classes('text-orange-600')
                        
                        # 미리보기 테이블 업데이트
                        if preview_data:
                            if preview_table:
                                preview_table.rows = preview_data
                                preview_table.update()
                            else:
                                # 미리보기 테이블 생성
                                preview_columns = [
                                    {'name': '사업장번호', 'label': '사업장번호', 'field': '사업장번호', 'align': 'center'},
                                    {'name': '지점', 'label': '지점', 'field': '지점', 'align': 'center'},
                                    {'name': '회사명', 'label': '회사명', 'field': '회사명', 'align': 'center'},
                                    {'name': '업종', 'label': '업종', 'field': '업종', 'align': 'center'},
                                    {'name': '산업', 'label': '산업', 'field': '산업', 'align': 'center'},
                                    {'name': '주소', 'label': '주소', 'field': '주소', 'align': 'center'},
                                    {'name': '사외 이사회 수', 'label': '사외 이사회 수', 'field': '사외 이사회 수', 'align': 'center'},
                                    {'name': '윤리경영 여부', 'label': '윤리경영 여부', 'field': '윤리경영 여부', 'align': 'center'},
                                    {'name': '컴플라이언스 정책 여부', 'label': '컴플라이언스 정책 여부', 'field': '컴플라이언스 정책 여부', 'align': 'center'},
                                    {'name': '상태', 'label': '상태', 'field': '상태', 'align': 'center'}
                                ]
                                
                                ui.label('🔍 업로드 데이터 미리보기').classes('text-lg font-bold text-blue-600 mt-4 mb-2')
                                preview_table = ui.table(
                                    columns=preview_columns, 
                                    rows=preview_data,
                                    row_key='지점'
                                ).classes('w-full text-center bordered dense flat rounded shadow-sm max-h-60')
                        
                    except Exception as excel_error:
                        upload_result.text = f'❌ 엑셀 파일 처리 오류: {str(excel_error)}'
                        upload_result.classes('text-red-600')
                        
                except Exception as e:
                    upload_result.text = f'❌ 파일 업로드 오류: {str(e)}'
                    upload_result.classes('text-red-600')
            
            # 파일 업로드 컴포넌트
            ui.upload(
                label='엑셀 파일 선택 (.xlsx, .xls)',
                auto_upload=True,
                on_upload=handle_upload,
                multiple=False
            ).props('accept=".xlsx,.xls"').classes('w-full mb-4')
            
            # 저장 기능
            def save_excel_data():
                """Staged 데이터를 실제 데이터베이스에 저장"""
                nonlocal preview_data
                if not preview_data:
                    ui.notify('저장할 데이터가 없습니다.', type='warning')
                    return
                
                try:
                    success_count = 0
                    error_count = 0
                    error_messages = []
                    
                    for data in preview_data:
                        try:
                            # 기존 데이터 확인 (중복 방지)
                            existing = db_session.query(CmpInfo).filter(
                                CmpInfo.cmp_num == data['사업장번호'],
                                CmpInfo.cmp_branch == data['지점']
                            ).first()
                            
                            if existing:
                                # 기존 데이터 업데이트
                                existing.cmp_industry = data['업종']
                                existing.cmp_sector = data['산업']
                                existing.cmp_addr = data['주소']
                                existing.cmp_extemp = data['사외 이사회 수']
                                existing.cmp_ethics_yn = data['윤리경영 여부']
                                existing.cmp_comp_yn = data['컴플라이언스 정책 여부']
                            else:
                                # 신규 데이터 추가
                                new_company = CmpInfo(
                                    cmp_num=data['사업장번호'],
                                    cmp_branch=data['지점'],
                                    cmp_nm=data['회사명'],
                                    cmp_industry=data['업종'],
                                    cmp_sector=data['산업'],
                                    cmp_addr=data['주소'],
                                    cmp_extemp=data['사외 이사회 수'],
                                    cmp_ethics_yn=data['윤리경영 여부'],
                                    cmp_comp_yn=data['컴플라이언스 정책 여부']
                                )
                                db_session.add(new_company)
                            
                            success_count += 1
                            
                        except Exception as row_error:
                            error_count += 1
                            error_messages.append(f'{data["지점"]}: {str(row_error)}')
                    
                    # 데이터베이스 커밋
                    db_session.commit()
                    
                    # 결과 메시지
                    if error_count == 0:
                        ui.notify(f'✅ 성공: {success_count}건이 저장되었습니다.', type='positive')
                    else:
                        ui.notify(f'⚠️ 부분 성공: {success_count}건 성공, {error_count}건 실패', type='warning')
                    
                    # 테이블 새로고침
                    refresh_table_data()
                    
                    # 다이얼로그 닫기
                    excel_dialog.close()
                    
                    # 임시 데이터 초기화
                    preview_data = []
                    
                except Exception as e:
                    ui.notify(f'❌ 저장 오류: {str(e)}', type='negative')
                    db_session.rollback()
            
            # 취소 기능
            def cancel_upload():
                """Staged 데이터 취소"""
                nonlocal preview_data, preview_table
                preview_data = []
                if preview_table:
                    preview_table.rows = []
                    preview_table.update()
                upload_result.text = ''
                excel_dialog.close()
            
            # 버튼들
            with ui.row().classes('justify-end mt-4 gap-3'):
                ui.button('저장', on_click=save_excel_data).props('color=primary text-color=white').classes('px-6 py-2 rounded-lg')
                ui.button('취소', on_click=cancel_upload).props('color=negative text-color=white').classes('px-6 py-2 rounded-lg')

        # =======================
        # 신규등록 버튼
        # =======================
        def open_new_dialog():
            setup_dialog()  # 신규 등록 모드로 다이얼로그 설정
            dialog.open()

        # 버튼들을 가로로 배치
        with ui.row().classes('mt-4 gap-3'):
            ui.button('신규등록', on_click=open_new_dialog) \
                .props('color=blue-200 text-color=black').classes('rounded-lg shadow-md')
            
            ui.button('엑셀 일괄등록', on_click=excel_dialog.open) \
                .props('color=green-200 text-color=black').classes('rounded-lg shadow-md')
