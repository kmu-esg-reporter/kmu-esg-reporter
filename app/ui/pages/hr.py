from nicegui import ui
import datetime
import pandas as pd
import io
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database.models import EmpInfo, CmpInfo

class HRPage:
    async def render(self, db_session: Session, cmp_num: Optional[str] = None):
        ui.label('👨‍💼 직원관리').classes('text-2xl font-bold text-blue-600 mb-4')

        # 현재 회사의 직원 데이터 조회
        employees = []
        current_company = None
        available_branches = ['서울지점']  # 기본값
        
        if db_session:
            try:
                # 회사 정보 조회 (표시용)
                if cmp_num:
                    current_company = db_session.query(CmpInfo).filter(CmpInfo.cmp_num == cmp_num).first()
                else:
                    # 기본적으로 첫 번째 회사 조회
                    current_company = db_session.query(CmpInfo).first()
                
                # CmpInfo에서 사용 가능한 지점 목록 조회
                branch_records = db_session.query(CmpInfo.cmp_branch).distinct().all()
                if branch_records:
                    available_branches = [branch[0] for branch in branch_records if branch[0]]
                if not available_branches:  # 빈 리스트인 경우 기본값 추가
                    available_branches = ['서울지점']
                
                # 모든 직원 조회 (새 스키마에는 company_id가 없음)
                db_employees = db_session.query(EmpInfo).all()
                
                # DB 데이터를 테이블 형식으로 변환
                for emp in db_employees:
                        # 생년월일 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
                        birth_formatted = ''
                        if emp.EMP_BIRTH and len(emp.EMP_BIRTH) == 8:
                            birth_formatted = f"{emp.EMP_BIRTH[:4]}-{emp.EMP_BIRTH[4:6]}-{emp.EMP_BIRTH[6:8]}"
                        
                        # 입사일 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
                        join_formatted = ''
                        if emp.EMP_JOIN and len(emp.EMP_JOIN) == 8:
                            join_formatted = f"{emp.EMP_JOIN[:4]}-{emp.EMP_JOIN[4:6]}-{emp.EMP_JOIN[6:8]}"
                        
                        # 성별 변환 (1->남자, 2->여자)
                        gender_text = ''
                        if emp.EMP_GENDER == '1':
                            gender_text = '남자'
                        elif emp.EMP_GENDER == '2':
                            gender_text = '여자'
                        
                        employees.append({
                            '지점': '서울지점' if emp.EMP_COMP == '6182618882' else emp.EMP_COMP or '서울지점',
                            '사번': str(emp.EMP_ID),
                            '이름': emp.EMP_NM,
                            '생년월일': birth_formatted,
                            '전화번호': emp.EMP_TEL or '',
                            '이메일': emp.EMP_EMAIL or '',
                            '입사년도': emp.EMP_JOIN[:4] if emp.EMP_JOIN and len(emp.EMP_JOIN) >= 4 else '',
                            '입사일': join_formatted,
                            '산재발생횟수': emp.EMP_ACIDENT_CNT or 0,
                            '이사회여부': emp.EMP_BOARD_YN or 'N',
                            '성별': gender_text,
                            '재직여부': emp.EMP_ENDYN or 'Y',
                            'db_id': emp.EMP_ID,  # 사번을 DB ID로 사용
                            'actions': '수정'  # 액션 컬럼 추가
                        })
            except Exception as e:
                # 테이블이 존재하지 않거나 다른 DB 오류 시 샘플 데이터 사용
                print(f"DB 오류로 샘플 데이터 사용: {str(e)}")
                current_company = None
                available_branches = ['서울지점']  # 기본값 설정
                employees = [
                    {
                        '지점': '서울지점',
                        '사번': '1001',
                        '이름': '김철수',
                        '생년월일': '1990-01-15',
                        '전화번호': '010-1234-5678',
                        '이메일': 'chulsoo@example.com',
                        '입사년도': '2015',
                        '입사일': '2015-03-01',
                        '산재발생횟수': 0,
                        '이사회여부': 'N',
                        '성별': '남자',
                        '재직여부': 'Y',
                        'db_id': None,
                        'actions': '수정'
                    }
                ]
        
       
        # # 현재 상태 표시
        # with ui.row().classes('w-full justify-between items-center mb-4'):
        #     if current_company:
        #         ui.label(f"📊 {current_company.cmp_nm} - 총 직원 수: {len(employees)}명").classes('text-lg font-medium text-gray-700')
        #         ui.label(f"✅ 자동 조회 완료").classes('text-sm text-green-600')
        #     else:
        #         ui.label(f"📊 샘플 데이터 - 총 {len(employees)}명").classes('text-lg font-medium text-gray-700')
        #         ui.label(f"⚠️ DB 연결 없음").classes('text-sm text-orange-600')

        # 테이블 컬럼 정의
        columns = [
            {'name': '지점', 'label': '지점', 'field': '지점', 'align': 'center'},
            {'name': '사번', 'label': '사번', 'field': '사번', 'align': 'center'},
            {'name': '이름', 'label': '이름', 'field': '이름', 'align': 'center'},
            {'name': '생년월일', 'label': '생년월일', 'field': '생년월일', 'align': 'center'},
            {'name': '전화번호', 'label': '전화번호', 'field': '전화번호', 'align': 'center'},
            {'name': '이메일', 'label': '이메일', 'field': '이메일', 'align': 'center'},
            {'name': '입사년도', 'label': '입사년도', 'field': '입사년도', 'align': 'center'},
            {'name': '입사일', 'label': '입사일', 'field': '입사일', 'align': 'center'},
            {'name': '산재발생횟수', 'label': '산재발생횟수', 'field': '산재발생횟수', 'align': 'center'},
            {'name': '이사회여부', 'label': '이사회여부', 'field': '이사회여부', 'align': 'center'},
            {'name': '성별', 'label': '성별', 'field': '성별', 'align': 'center'},
            {'name': '재직여부', 'label': '재직여부', 'field': '재직여부', 'align': 'center'},
            {'name': 'actions', 'label': '수정', 'field': 'actions', 'align': 'center'},
        ]

        # =======================
        # 검색 / 필터 UI
        # =======================
        original_employees = employees.copy()
        filtered_employees = employees.copy()

        def apply_filters():
            nonlocal filtered_employees
            filtered_employees = original_employees.copy()

            # 지점 검색 (SELECT BOX)
            if branch_input.value and branch_input.value != '전체':
                filtered_employees = [r for r in filtered_employees if r['지점'] == branch_input.value]
            
            # 사번 검색
            if empno_input.value:
                filtered_employees = [r for r in filtered_employees if empno_input.value in str(r['사번'])]
            
            # 이름 검색
            if name_input.value:
                filtered_employees = [r for r in filtered_employees if name_input.value.upper() in r['이름'].upper()]
            
            # 입사일 범위 검색 (년도 기준)
            if hire_year_from_input.value:
                filtered_employees = [r for r in filtered_employees if r['입사년도'] and int(r['입사년도']) >= hire_year_from_input.value]
            if hire_year_to_input.value:
                filtered_employees = [r for r in filtered_employees if r['입사년도'] and int(r['입사년도']) <= hire_year_to_input.value]
            
            # 성별 필터
            if gender_select.value and gender_select.value != '전체':
                filtered_employees = [r for r in filtered_employees if r['성별'] == gender_select.value]

            table.rows = filtered_employees
            table.update()
            result_count.text = f'검색 결과: {len(filtered_employees)}건'

        def reset_filters():
            branch_input.set_value('전체')
            empno_input.set_value('')
            name_input.set_value('')
            hire_year_from_input.set_value(None)
            hire_year_to_input.set_value(None)
            gender_select.set_value('전체')

            table.rows = original_employees
            table.update()
            result_count.text = f'검색 결과: {len(original_employees)}건'

        # =======================
        # 검색 UI 카드
        # =======================
        with ui.card().classes('w-full p-2 mb-4 rounded-xl shadow-sm bg-gray-50 text-xs'):
            with ui.row().classes('items-center justify-between mb-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.icon('tune', size='1rem').classes('text-blue-600')
                    ui.label('검색 필터').classes('text-sm font-semibold text-gray-700')
                result_count = ui.label(f'검색 결과: {len(employees)}건').classes('text-xs text-gray-500')

            uniform_width = 'w-24 h-7 text-xs'

            # row + wrap → 화면에 맞게 자동 줄바꿈
            with ui.row().classes('items-center gap-4 flex-wrap'):
                ui.label('지점').classes('text-xs font-medium text-gray-600')
                # 사용 가능한 지점 목록에서 선택 (전체 옵션 추가)
                branch_options = ['전체'] + available_branches
                branch_input = ui.select(branch_options, value='전체') \
                    .props('outlined dense clearable').classes('w-30 h-7 text-xs')

                ui.label('사번').classes('text-xs font-medium text-gray-600')
                empno_input = ui.input(placeholder='사번').props('outlined dense clearable').classes(uniform_width)

                ui.label('이름').classes('text-xs font-medium text-gray-600')
                name_input = ui.input(placeholder='이름').props('outlined dense clearable').classes(uniform_width)

                ui.label('입사년도').classes('text-xs font-medium text-gray-600')
                with ui.row().classes('items-center gap-1'):
                    hire_year_from_input = ui.number(placeholder='시작년도', precision=0, min=1980, max=2030) \
                        .props('outlined dense clearable').classes(uniform_width)
                    ui.label('~').classes('text-gray-400 text-xs')
                    hire_year_to_input = ui.number(placeholder='종료년도', precision=0, min=1980, max=2030) \
                        .props('outlined dense clearable').classes(uniform_width)

                ui.label('성별').classes('text-xs font-medium text-gray-600')
                gender_select = ui.select(['전체', '남자', '여자'], value='전체') \
                    .props('outlined dense clearable').classes('w-28 h-7 text-xs')

                # 버튼들을 오른쪽으로 밀어서 배치
                with ui.row().classes('items-center gap-2 ml-auto'):
                    ui.button('검색', color='primary', on_click=apply_filters) \
                        .classes('rounded-md shadow-sm px-4 py-2 text-sm font-medium')
                    ui.button('초기화', color='secondary', on_click=reset_filters) \
                        .classes('rounded-md shadow-sm px-4 py-2 text-sm font-medium')

        table = ui.table(columns=columns, rows=filtered_employees, row_key='사번').classes(
            'w-full text-center bordered dense flat rounded shadow-sm'
        ).props(
             'table-header-class=bg-blue-200 text-white'
        )

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

        # 직원 등록/수정 다이얼로그
        edit_mode = False
        current_employee = None
        dialog_title = ui.label()
        with ui.dialog() as dialog, ui.card().classes('p-4 w-[450px] max-h-[85vh] overflow-y-auto'):
            inputs = {}

            def setup_dialog(employee_data=None):
                nonlocal edit_mode, current_employee
                edit_mode = employee_data is not None
                current_employee = employee_data
               
                # 기존 데이터로 폼 채우기
                if employee_data:
                    # 날짜 파싱
                    birth_parts = employee_data.get('생년월일', '1990-01-01').split('-')
                    hire_parts = employee_data.get('입사일', '2025-01-01').split('-')
                    
                    # 기존 직원의 실제 지점 값을 사용 (수정 모드에서는 기존 값 유지)
                    current_branch = employee_data.get('지점', '서울지점')
                    
                    # 현재 지점이 available_branches에 없으면 추가
                    if current_branch not in available_branches:
                        available_branches.append(current_branch)
                        # 지점 select 옵션 업데이트
                        inputs['지점'].options = available_branches
                    
                    inputs['지점'].set_value(current_branch)
                    inputs['사번'].set_value(employee_data.get('사번', ''))
                    inputs['이름'].set_value(employee_data.get('이름', ''))
                    inputs['생년'].set_value(birth_parts[0] if len(birth_parts) > 0 else '1990')
                    inputs['생월'].set_value(birth_parts[1] if len(birth_parts) > 1 else '01')
                    inputs['생일'].set_value(birth_parts[2] if len(birth_parts) > 2 else '01')
                    inputs['전화번호'].set_value(employee_data.get('전화번호', ''))
                    inputs['이메일'].set_value(employee_data.get('이메일', ''))
                    inputs['입사년'].set_value(hire_parts[0] if len(hire_parts) > 0 else str(datetime.datetime.now().year))
                    inputs['입사월'].set_value(hire_parts[1] if len(hire_parts) > 1 else '01')
                    inputs['입사일'].set_value(hire_parts[2] if len(hire_parts) > 2 else '01')
                    inputs['산재발생횟수'].set_value(str(employee_data.get('산재발생횟수', 0)))
                    inputs['이사회여부'].set_value(employee_data.get('이사회여부', 'N'))
                    inputs['성별'].set_value(employee_data.get('성별', '남자'))
                    inputs['재직여부'].set_value(employee_data.get('재직여부', 'Y'))
                    
                    # 수정 모드에서는 사번 비활성화 (읽기 전용)
                    inputs['사번'].props('readonly disabled')
                else:
                    # 신규 등록 시 기본값 설정 - 서울지점 우선
                    user_default_branch = "서울지점"
                    if user_default_branch in available_branches:
                        default_branch = user_default_branch
                    else:
                        default_branch = available_branches[0] if available_branches else '서울지점'
                    
                    inputs['지점'].set_value(default_branch)
                    inputs['사번'].set_value('')
                    inputs['이름'].set_value('')
                    inputs['생년'].set_value('1990')
                    inputs['생월'].set_value('01')
                    inputs['생일'].set_value('01')
                    inputs['전화번호'].set_value('')
                    inputs['이메일'].set_value('')
                    inputs['입사년'].set_value(str(datetime.datetime.now().year))
                    inputs['입사월'].set_value('01')
                    inputs['입사일'].set_value('01')
                    inputs['산재발생횟수'].set_value('0')
                    inputs['이사회여부'].set_value('N')
                    inputs['성별'].set_value('남자')
                    inputs['재직여부'].set_value('Y')
                    
                    # 신규 등록 시 사번 활성화 (편집 가능)
                    inputs['사번'].props(remove='readonly disabled')

            inputs = {}

            # helper 함수
            def field(label, component):
                return component.props('outlined dense').classes('w-full mb-1').props(f'label={label}')

            # 지점 선택 (CmpInfo의 cmp_branch 값들을 사용)
            inputs['지점'] = ui.select(
                options=available_branches, 
                value=available_branches[0] if available_branches else '서울지점',
                label='지점'
            ).props('outlined dense').classes('w-full mb-1')
            inputs['사번'] = field('사번', ui.input())
            inputs['이름'] = field('이름', ui.input())

            # 생년월일 선택
            years = [str(y) for y in range(1950, datetime.date.today().year + 1)]
            months = [str(m).zfill(2) for m in range(1, 13)]
            days = [str(d).zfill(2) for d in range(1, 32)]
            with ui.column().classes('w-full mb-1'):
                ui.label('생년월일').classes('text-xs font-medium text-gray-700')
                with ui.row().classes('gap-1 w-full'):
                    year = ui.select(years, value='1990').props('outlined dense').classes('w-24')
                    month = ui.select(months, value='01').props('outlined dense').classes('w-16')
                    day = ui.select(days, value='01').props('outlined dense').classes('w-16')
            inputs['생년'] = year
            inputs['생월'] = month
            inputs['생일'] = day

            # 전화번호 입력 (마스크 사용)
            phone_input = ui.input(
                label='전화번호',
                placeholder='010-0000-0000'
            ).props('outlined dense mask="###-####-####" fill-mask').classes('w-full mb-1')
            
            inputs['전화번호'] = phone_input
            inputs['이메일'] = field('이메일', ui.input())
            
            # 입사일 선택 (년월일)
            hire_years = [str(y) for y in range(1980, datetime.date.today().year + 1)]
            hire_months = [str(m).zfill(2) for m in range(1, 13)]
            hire_days = [str(d).zfill(2) for d in range(1, 32)]
            with ui.column().classes('w-full mb-1'):
                ui.label('입사일').classes('text-xs font-medium text-gray-700')
                with ui.row().classes('gap-1 w-full'):
                    hire_year = ui.select(hire_years, value=str(datetime.date.today().year)).props('outlined dense').classes('w-24')
                    hire_month = ui.select(hire_months, value='01').props('outlined dense').classes('w-16')
                    hire_day = ui.select(hire_days, value='01').props('outlined dense').classes('w-16')
            inputs['입사년'] = hire_year
            inputs['입사월'] = hire_month
            inputs['입사일'] = hire_day
            
            inputs['산재발생횟수'] = field('산재발생횟수', ui.input().props('type=number'))
            inputs['이사회여부'] = field('이사회여부', ui.select(['Y', 'N'], value='N'))
            inputs['성별'] = field('성별', ui.select(['남자', '여자'], value='남자'))
            inputs['재직여부'] = field('재직여부', ui.select(['Y', 'N'], value='Y'))

            # 저장/수정 로직
            def add_employee():
                try:
                    # 필수 입력값 검증
                    if not inputs['사번'].value or not inputs['이름'].value:
                        ui.notify('사번과 이름은 필수 입력 항목입니다', type='warning')
                        return
                    
                    # 사번 중복 확인 (신규 등록 시에만)
                    emp_id = inputs['사번'].value
                    if not edit_mode and any(emp['사번'] == emp_id for emp in employees):
                        ui.notify('이미 존재하는 사번입니다', type='warning')
                        return
                    
                    # 입력값 검증 및 수집
                    workplace_value = inputs['지점'].value or '서울지점'  # 기본값 보장
                    birth_date_str = f"{inputs['생년'].value}-{inputs['생월'].value}-{inputs['생일'].value}"
                    
                    try:
                        birth_date = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        ui.notify('올바른 생년월일을 입력해주세요', type='warning')
                        return
                    
                    # 입사일 처리
                    hire_date_str = f"{inputs['입사년'].value}-{inputs['입사월'].value}-{inputs['입사일'].value}"
                    try:
                        hire_date = datetime.datetime.strptime(hire_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        ui.notify('올바른 입사일을 입력해주세요', type='warning')
                        return
                    
                    try:
                        # 산재발생횟수 검증
                        accident_count = int(inputs['산재발생횟수'].value or 0)
                        if accident_count < 0:
                            ui.notify('산재발생횟수는 0 이상이어야 합니다', type='warning')
                            return
                    except ValueError:
                        ui.notify('산재발생횟수는 숫자만 입력 가능합니다', type='warning')
                        return
                    
                    # 데이터 포맷 변환
                    birth_date_formatted = f"{inputs['생년'].value}{inputs['생월'].value}{inputs['생일'].value}"  # YYYYMMDD
                    hire_date_formatted = f"{inputs['입사년'].value}{inputs['입사월'].value}{inputs['입사일'].value}"  # YYYYMMDD
                    
                    # 성별 변환 (남자->1, 여자->2)
                    gender_code = '1' if inputs['성별'].value == '남자' else '2'
                    
                    new_row = {
                        '지점': workplace_value,
                        '사번': inputs['사번'].value,
                        '이름': inputs['이름'].value,
                        '생년월일': birth_date_str,
                        '전화번호': inputs['전화번호'].value or '',
                        '이메일': inputs['이메일'].value or '',
                        '입사년도': inputs['입사년'].value,  # 테이블 표시용으로는 년도만
                        '입사일': hire_date_str,  # 전체 입사일
                        '산재발생횟수': accident_count,
                        '이사회여부': inputs['이사회여부'].value,
                        '성별': inputs['성별'].value,
                        '재직여부': inputs['재직여부'].value,
                        'db_id': None
                    }
                    
                    # 데이터베이스에 저장 (새로운 스키마)
                    if db_session:
                        try:
                            if edit_mode and current_employee:
                                # 기존 직원 정보 수정
                                existing_employee = db_session.query(EmpInfo).filter_by(
                                    EMP_ID=int(current_employee.get('사번'))
                                ).first()
                                
                                if existing_employee:
                                    existing_employee.EMP_NM = inputs['이름'].value
                                    existing_employee.EMP_BIRTH = birth_date_formatted
                                    existing_employee.EMP_TEL = inputs['전화번호'].value or ''
                                    existing_employee.EMP_EMAIL = inputs['이메일'].value or ''
                                    existing_employee.EMP_JOIN = hire_date_formatted
                                    existing_employee.EMP_ACIDENT_CNT = accident_count
                                    existing_employee.EMP_BOARD_YN = inputs['이사회여부'].value
                                    existing_employee.EMP_GENDER = gender_code
                                    existing_employee.EMP_ENDYN = inputs['재직여부'].value
                                    existing_employee.EMP_COMP = workplace_value
                                    
                                    db_session.commit()
                                    
                                    # 테이블에서 해당 직원 데이터 업데이트
                                    for i, emp in enumerate(employees):
                                        if emp['사번'] == current_employee.get('사번'):
                                            employees[i] = new_row
                                            break
                                    
                                    ui.notify(f"{existing_employee.EMP_NM} 님의 정보가 수정되었습니다 ✅", type='positive')
                                else:
                                    ui.notify("수정할 직원을 찾을 수 없습니다", type='negative')
                                    return
                            else:
                                # 신규 직원 등록
                                new_employee = EmpInfo(
                                    EMP_ID=int(inputs['사번'].value),
                                    EMP_NM=inputs['이름'].value,
                                    EMP_BIRTH=birth_date_formatted,
                                    EMP_TEL=inputs['전화번호'].value or '',
                                    EMP_EMAIL=inputs['이메일'].value or '',
                                    EMP_JOIN=hire_date_formatted,
                                    EMP_ACIDENT_CNT=accident_count,
                                    EMP_BOARD_YN=inputs['이사회여부'].value,
                                    EMP_GENDER=gender_code,
                                    EMP_ENDYN=inputs['재직여부'].value,
                                    EMP_COMP=workplace_value
                                )
                                
                                db_session.add(new_employee)
                                db_session.commit()
                                new_row['db_id'] = new_employee.EMP_ID
                                
                                # 테이블에 새 직원 추가
                                employees.append(new_row)
                                
                                ui.notify(f"{new_row['이름']} 님이 데이터베이스에 저장되었습니다 ✅", type='positive')
                            
                            table.update()
                            dialog.close()
                            
                            # 폼 초기화
                            for key, input_field in inputs.items():
                                if hasattr(input_field, 'set_value'):
                                    if key == '지점':
                                        input_field.set_value('서울지점')
                                    elif key in ['이사회여부', '재직여부']:
                                        input_field.set_value('N' if key == '이사회여부' else 'Y')
                                    elif key == '성별':
                                        input_field.set_value('남자')
                                    elif key in ['생년', '입사년']:
                                        input_field.set_value('1990' if key == '생년' else str(datetime.datetime.now().year))
                                    elif key in ['생월', '생일', '입사월', '입사일']:
                                        input_field.set_value('01')
                                    else:
                                        input_field.set_value('')
                            
                        except Exception as db_error:
                            print(f"DB 저장 오류: {str(db_error)}")
                            ui.notify(f"데이터베이스 저장 중 오류 발생: {str(db_error)}", type='negative')
                            if db_session:
                                db_session.rollback()
                            return
                        
                    else:
                        ui.notify(f"{new_row['이름']} 님이 추가되었습니다 (임시) ⚠️", type='warning')
                        # 테이블 업데이트
                        employees.append(new_row)
                        table.update()
                        dialog.close()
                    
                except Exception as e:
                    ui.notify(f"저장 중 오류가 발생했습니다: {str(e)}", type='negative')
                    if db_session:
                        db_session.rollback()

            # 버튼들
            with ui.row().classes('justify-end mt-4 gap-3'):
                ui.button('저장', on_click=add_employee).props('color=primary text-color=white').classes('px-6 py-2 rounded-lg')
                ui.button('취소', on_click=dialog.close).props('color=negative text-color=white').classes('px-6 py-2 rounded-lg')

        # 수정 버튼 클릭 이벤트 처리
        def on_edit_row(e):
            row_data = e.args
            if row_data:
                setup_dialog(row_data)
                dialog.open()
        
        table.on('edit_row', on_edit_row)

        # 신규등록 버튼
        def open_new_dialog():
            setup_dialog()  # 신규 등록 모드로 다이얼로그 설정
            dialog.open()

        # 엑셀 일괄등록 버튼 추가
        def open_excel_dialog():
            excel_dialog.open()

        # 버튼들을 가로로 배치 (회사관리와 동일)
        with ui.row().classes('mt-4 gap-3'):
            ui.button('신규등록', on_click=open_new_dialog) \
                .props('color=blue-200 text-color=black').classes('rounded-lg shadow-md')
            
            ui.button('엑셀 일괄등록', on_click=open_excel_dialog) \
                .props('color=green-200 text-color=black').classes('rounded-lg shadow-md')

        # =======================
        # 엑셀 일괄등록 다이얼로그
        # =======================
        with ui.dialog() as excel_dialog, ui.card().classes('p-6 w-[700px]'):
            ui.label('📄 엑셀 일괄등록').classes('text-xl font-bold text-green-600 mb-4')
            
            # 엑셀 템플릿 안내
            with ui.card().classes('p-4 mb-4 bg-blue-50'):
                ui.label('📝 엑셀 파일 형식 안내').classes('text-lg font-bold text-blue-600')
                # ui.label('• 첫 번째 행은 헤더로 사용됩니다.').classes('text-sm mt-2')
                # ui.label('• 열 이름의 공백은 자동으로 제거됩니다. (예: "산재 발생 횟수" → "산재발생횟수")').classes('text-sm')
                
                # # 필수 열 안내
                # ui.label('📄 필수 열 목록:').classes('text-sm font-bold mt-3')
                # required_columns = [
                #     '지점', '사번', '이름', '생년월일', '전화번호', '이메일',
                #     '입사일', '산재발생횟수', '이사회여부', '성별', '재직여부'
                # ]
                # for i, col in enumerate(required_columns, 1):
                #     ui.label(f'{i}. {col}').classes('text-sm ml-4')
                
                ui.label('⚠️ 생년월일과 입사일은 YYYY-MM-DD 형식으로 입력해주세요.').classes('text-sm text-orange-600 mt-2')
                ui.label('⚠️ 성별은 "남자" 또는 "여자"로 입력해주세요.').classes('text-sm text-orange-600')
                ui.label('⚠️ 이사회여부, 재직여부는 Y 또는 N으로 입력해주세요.').classes('text-sm text-orange-600')
                ui.label('💡 열 이름에 공백이 있어도 자동으로 처리됩니다.').classes('text-sm text-blue-600 mt-1')
            
            # 엑셀 양식 다운로드 버튼
            def download_template():
                try:
                    # 엑셀 양식 데이터 생성
                    template_data = {
                        '지점': ['서울지점', '구미지사'],
                        '사번': ['1001', '1002'],
                        '이름': ['홍길동', '김철수'],
                        '생년월일': ['1990-01-15', '1985-05-20'],
                        '전화번호': ['010-1234-5678', '010-9876-5432'],
                        '이메일': ['hong@company.com', 'kim@company.com'],
                        '입사일': ['2020-03-01', '2018-07-15'],
                        '산재발생횟수': [0, 1],
                        '이사회여부': ['N', 'Y'],
                        '성별': ['남자', '남자'],
                        '재직여부': ['Y', 'Y']
                    }
                    
                    # DataFrame 생성
                    template_df = pd.DataFrame(template_data)
                    
                    # 메모리에 엑셀 파일 생성
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        template_df.to_excel(writer, sheet_name='직원정보양식', index=False)
                    
                    # 파일 다운로드
                    output.seek(0)
                    ui.download(output.getvalue(), filename='직원정보_업로드양식.xlsx')
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
                        required_cols = ['지점', '사번', '이름', '생년월일', '전화번호', '이메일', 
                                       '입사일', '산재발생횟수', '이사회여부', '성별', '재직여부']
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
                                # 기본 데이터 검증
                                emp_id = str(row['사번']).strip() if pd.notna(row['사번']) else ''
                                if not emp_id or emp_id == 'nan':
                                    error_messages.append(f'행 {idx + 2}: 사번이 비어있음')
                                    error_count += 1
                                    continue
                                
                                emp_name = str(row['이름']).strip() if pd.notna(row['이름']) else ''
                                if not emp_name or emp_name == 'nan':
                                    error_messages.append(f'행 {idx + 2}: 이름이 비어있음')
                                    error_count += 1
                                    continue
                                
                                # 지점 처리
                                branch = str(row['지점']).strip() if pd.notna(row['지점']) else '서울지점'
                                
                                # 생년월일 처리
                                birth_date = str(row['생년월일']).strip() if pd.notna(row['생년월일']) else ''
                                birth_formatted = ''
                                if birth_date and birth_date != 'nan':
                                    try:
                                        if len(birth_date) == 8 and birth_date.isdigit():
                                            birth_formatted = f"{birth_date[:4]}-{birth_date[4:6]}-{birth_date[6:8]}"
                                        else:
                                            birth_parsed = pd.to_datetime(birth_date)
                                            birth_formatted = birth_parsed.strftime('%Y-%m-%d')
                                    except:
                                        error_messages.append(f'행 {idx + 2}: 잘못된 생년월일 형식')
                                        error_count += 1
                                        continue
                                
                                # 입사일 처리
                                hire_date = str(row['입사일']).strip() if pd.notna(row['입사일']) else ''
                                hire_formatted = ''
                                if hire_date and hire_date != 'nan':
                                    try:
                                        if len(hire_date) == 8 and hire_date.isdigit():
                                            hire_formatted = f"{hire_date[:4]}-{hire_date[4:6]}-{hire_date[6:8]}"
                                        else:
                                            hire_parsed = pd.to_datetime(hire_date)
                                            hire_formatted = hire_parsed.strftime('%Y-%m-%d')
                                    except:
                                        error_messages.append(f'행 {idx + 2}: 잘못된 입사일 형식')
                                        error_count += 1
                                        continue
                                
                                # 성별 검증
                                gender = str(row['성별']).strip() if pd.notna(row['성별']) else '남자'
                                if gender not in ['남자', '여자']:
                                    error_messages.append(f'행 {idx + 2}: 성별은 남자/여자만 가능')
                                    error_count += 1
                                    continue
                                
                                # 산재발생횟수 처리
                                try:
                                    accident_count = int(float(row['산재발생횟수'])) if pd.notna(row['산재발생횟수']) else 0
                                    if accident_count < 0:
                                        accident_count = 0
                                except (ValueError, TypeError):
                                    accident_count = 0
                                
                                # Y/N 값 처리
                                board_yn = str(row['이사회여부']).strip().upper() if pd.notna(row['이사회여부']) else 'N'
                                employment_yn = str(row['재직여부']).strip().upper() if pd.notna(row['재직여부']) else 'Y'
                                
                                # Y/N 값 유효성 검사
                                if board_yn not in ['Y', 'N']:
                                    board_yn = 'N'
                                if employment_yn not in ['Y', 'N']:
                                    employment_yn = 'Y'
                                
                                # 유효한 데이터를 임시 저장
                                preview_data.append({
                                    '지점': branch,
                                    '사번': emp_id,
                                    '이름': emp_name,
                                    '생년월일': birth_formatted,
                                    '전화번호': str(row['전화번호']).strip() if pd.notna(row['전화번호']) else '',
                                    '이메일': str(row['이메일']).strip() if pd.notna(row['이메일']) else '',
                                    '입사년도': hire_formatted.split('-')[0] if hire_formatted else '',
                                    '입사일': hire_formatted,
                                    '산재발생횟수': accident_count,
                                    '이사회여부': board_yn,
                                    '성별': gender,
                                    '재직여부': employment_yn,
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
                                    {'name': '지점', 'label': '지점', 'field': '지점', 'align': 'center'},
                                    {'name': '사번', 'label': '사번', 'field': '사번', 'align': 'center'},
                                    {'name': '이름', 'label': '이름', 'field': '이름', 'align': 'center'},
                                    {'name': '생년월일', 'label': '생년월일', 'field': '생년월일', 'align': 'center'},
                                    {'name': '성별', 'label': '성별', 'field': '성별', 'align': 'center'},
                                    {'name': '입사일', 'label': '입사일', 'field': '입사일', 'align': 'center'},
                                    {'name': '이사회여부', 'label': '이사회여부', 'field': '이사회여부', 'align': 'center'},
                                    {'name': '재직여부', 'label': '재직여부', 'field': '재직여부', 'align': 'center'},
                                    {'name': '상태', 'label': '상태', 'field': '상태', 'align': 'center'}
                                ]
                                
                                ui.label('🔍 업로드 데이터 미리보기').classes('text-lg font-bold text-blue-600 mt-4 mb-2')
                                preview_table = ui.table(
                                    columns=preview_columns, 
                                    rows=preview_data,
                                    row_key='사번'
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
            
            # 일괄 저장 버튼
            def save_all_data():
                if not preview_data:
                    ui.notify('❌ 저장할 데이터가 없습니다', type='warning')
                    return
                
                if not db_session:
                    ui.notify('❌ 데이터베이스 연결이 없습니다', type='negative')
                    return
                
                try:
                    saved_count = 0
                    updated_count = 0
                    errors = []
                    
                    for emp_data in preview_data:
                        try:
                            emp_id = int(emp_data['사번'])
                            
                            # 기존 직원 확인
                            existing_emp = db_session.query(EmpInfo).filter_by(EMP_ID=emp_id).first()
                            
                            # 날짜 변환 (YYYY-MM-DD -> YYYYMMDD)
                            birth_db = emp_data['생년월일'].replace('-', '') if emp_data['생년월일'] else ''
                            hire_db = emp_data['입사일'].replace('-', '') if emp_data['입사일'] else ''
                            
                            # 성별 변환 (남자->1, 여자->2)
                            gender_code = '1' if emp_data['성별'] == '남자' else '2'
                            
                            if existing_emp:
                                # 기존 직원 업데이트
                                existing_emp.EMP_NM = emp_data['이름']
                                existing_emp.EMP_BIRTH = birth_db
                                existing_emp.EMP_TEL = emp_data['전화번호']
                                existing_emp.EMP_EMAIL = emp_data['이메일']
                                existing_emp.EMP_JOIN = hire_db
                                existing_emp.EMP_ACIDENT_CNT = emp_data['산재발생횟수']
                                existing_emp.EMP_BOARD_YN = emp_data['이사회여부']
                                existing_emp.EMP_GENDER = gender_code
                                existing_emp.EMP_ENDYN = emp_data['재직여부']
                                existing_emp.EMP_COMP = emp_data['지점']
                                updated_count += 1
                            else:
                                # 신규 직원 추가
                                new_emp = EmpInfo(
                                    EMP_ID=emp_id,
                                    EMP_NM=emp_data['이름'],
                                    EMP_BIRTH=birth_db,
                                    EMP_TEL=emp_data['전화번호'],
                                    EMP_EMAIL=emp_data['이메일'],
                                    EMP_JOIN=hire_db,
                                    EMP_ACIDENT_CNT=emp_data['산재발생횟수'],
                                    EMP_BOARD_YN=emp_data['이사회여부'],
                                    EMP_GENDER=gender_code,
                                    EMP_ENDYN=emp_data['재직여부'],
                                    EMP_COMP=emp_data['지점']
                                )
                                db_session.add(new_emp)
                                saved_count += 1
                                
                        except Exception as e:
                            errors.append(f"사번 {emp_data['사번']}: {str(e)}")
                    
                    if errors:
                        error_msg = f"❌ 일부 데이터 저장 실패:\n" + "\n".join(errors[:5])
                        if len(errors) > 5:
                            error_msg += f"\n... 외 {len(errors) - 5}개"
                        ui.notify(error_msg, type='negative')
                        db_session.rollback()
                        return
                    
                    # 데이터베이스 커밋
                    db_session.commit()
                    
                    # 메인 테이블 새로고침
                    refresh_table_data()
                    
                    # 다이얼로그 닫기 및 초기화
                    excel_dialog.close()
                    preview_data.clear()
                    if preview_table:
                        preview_table.rows = []
                        preview_table.update()
                    upload_result.text = ''
                    
                    ui.notify(f'✅ 저장 완료: 신규 {saved_count}명, 수정 {updated_count}명', type='positive')
                    
                except Exception as e:
                    ui.notify(f'❌ 저장 중 오류 발생: {str(e)}', type='negative')
                    if db_session:
                        db_session.rollback()
            
            # 다이얼로그 하단 버튼들
            with ui.row().classes('justify-end mt-4 gap-3'):
                ui.button('저장', on_click=save_all_data).props('color=primary text-color=white').classes('px-6 py-2 rounded-lg')
                ui.button('취소', on_click=excel_dialog.close).props('color=negative text-color=white').classes('px-6 py-2 rounded-lg')

        # 테이블 새로고침 함수 (엑셀 저장 후 사용)
        def refresh_table_data():
            """테이블 데이터만 새로고침"""
            nonlocal original_employees, filtered_employees
            updated_employees = []
            if db_session:
                try:
                    db_employees = db_session.query(EmpInfo).all()
                    for emp in db_employees:
                        # 생년월일 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
                        birth_formatted = ''
                        if emp.EMP_BIRTH and len(emp.EMP_BIRTH) == 8:
                            birth_formatted = f"{emp.EMP_BIRTH[:4]}-{emp.EMP_BIRTH[4:6]}-{emp.EMP_BIRTH[6:8]}"
                        
                        # 입사일 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
                        join_formatted = ''
                        if emp.EMP_JOIN and len(emp.EMP_JOIN) == 8:
                            join_formatted = f"{emp.EMP_JOIN[:4]}-{emp.EMP_JOIN[4:6]}-{emp.EMP_JOIN[6:8]}"
                        
                        # 성별 변환 (1->남자, 2->여자)
                        gender_text = ''
                        if emp.EMP_GENDER == '1':
                            gender_text = '남자'
                        elif emp.EMP_GENDER == '2':
                            gender_text = '여자'
                        
                        updated_employees.append({
                            '지점': emp.EMP_COMP or '서울지점',
                            '사번': str(emp.EMP_ID),
                            '이름': emp.EMP_NM,
                            '생년월일': birth_formatted,
                            '전화번호': emp.EMP_TEL or '',
                            '이메일': emp.EMP_EMAIL or '',
                            '입사년도': emp.EMP_JOIN[:4] if emp.EMP_JOIN and len(emp.EMP_JOIN) >= 4 else '',
                            '입사일': join_formatted,
                            '산재발생횟수': emp.EMP_ACIDENT_CNT or 0,
                            '이사회여부': emp.EMP_BOARD_YN or 'N',
                            '성별': gender_text,
                            '재직여부': emp.EMP_ENDYN or 'Y',
                            'db_id': emp.EMP_ID,
                            'actions': '수정'
                        })
                except Exception as e:
                    print(f"테이블 새로고침 오류: {str(e)}")
            
            # 전역 employees 업데이트
            employees.clear()
            employees.extend(updated_employees)
            original_employees = updated_employees
            # 필터 재적용
            apply_filters()
       