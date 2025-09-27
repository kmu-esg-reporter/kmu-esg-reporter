"""Environment management page with compact search filter UI + 신규등록 + 엑셀 업로드."""

from nicegui import ui
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import io

from .base_page import BasePage
from app.core.database.models import Env


class EnvironmentPage(BasePage):
    async def render(self, db_session: Session, company_num: Optional[str] = None) -> None:
        ui.label('🌱 환경관리').classes('text-xl font-bold text-blue-600 mb-4')

        # =======================
        # DB 데이터 조회
        # =======================
        env_data = []
        if db_session:
            db_envs = db_session.query(Env).order_by(Env.year.desc()).all()
            for env in db_envs:
                env_data.append({
                    '년도': str(env.year),
                    '에너지 사용량': f"{env.energy_use:,.2f}" if env.energy_use else '0.00',
                    '온실가스 배출량': f"{env.green_use:,.2f}" if env.green_use else '0.00',
                    '재생에너지 사용여부': env.renewable_yn or 'N',
                    '재생에너지 비율': f"{(env.renewable_ratio * 100):,.1f}" if env.renewable_ratio else '0.0',
                    'year_pk': env.year,
                    'actions': '수정/삭제'
                })

        # =======================
        # 테이블 컬럼 정의
        # =======================
        columns = [
            {'name': '년도', 'label': '년도', 'field': '년도', 'align': 'center'},
            {'name': '에너지 사용량', 'label': '에너지 사용량(MWh)', 'field': '에너지 사용량', 'align': 'center'},
            {'name': '온실가스 배출량', 'label': '온실가스 배출량(tCO2e)', 'field': '온실가스 배출량', 'align': 'center'},
            {'name': '재생에너지 사용여부', 'label': '재생에너지 사용여부', 'field': '재생에너지 사용여부', 'align': 'center'},
            {'name': '재생에너지 비율', 'label': '재생에너지 비율(%)', 'field': '재생에너지 비율', 'align': 'center'},
            {'name': 'actions', 'label': '수정/삭제', 'field': 'actions', 'align': 'center'},
        ]

        # =======================
        # 검색 / 필터 UI
        # =======================
        original_env_data = env_data.copy()
        filtered_env_data = env_data.copy()

        def apply_filters():
            nonlocal filtered_env_data
            filtered_env_data = original_env_data.copy()

            if year_from_input.value:
                filtered_env_data = [r for r in filtered_env_data if int(r['년도']) >= year_from_input.value]
            if year_to_input.value:
                filtered_env_data = [r for r in filtered_env_data if int(r['년도']) <= year_to_input.value]

            if renewable_select.value and renewable_select.value != '전체':
                filtered_env_data = [r for r in filtered_env_data if r['재생에너지 사용여부'] == renewable_select.value]

            if energy_min_input.value:
                filtered_env_data = [r for r in filtered_env_data if float(r['에너지 사용량'].replace(',', '')) >= energy_min_input.value]
            if energy_max_input.value:
                filtered_env_data = [r for r in filtered_env_data if float(r['에너지 사용량'].replace(',', '')) <= energy_max_input.value]

            if green_min_input.value:
                filtered_env_data = [r for r in filtered_env_data if float(r['온실가스 배출량'].replace(',', '')) >= green_min_input.value]
            if green_max_input.value:
                filtered_env_data = [r for r in filtered_env_data if float(r['온실가스 배출량'].replace(',', '')) <= green_max_input.value]

            if ratio_min_input.value:
                filtered_env_data = [r for r in filtered_env_data if float(r['재생에너지 비율']) >= ratio_min_input.value]
            if ratio_max_input.value:
                filtered_env_data = [r for r in filtered_env_data if float(r['재생에너지 비율']) <= ratio_max_input.value]

            table.rows = filtered_env_data
            table.update()
            result_count.text = f'검색 결과: {len(filtered_env_data)}건'

        def reset_filters():
            year_from_input.set_value(None)
            year_to_input.set_value(None)
            renewable_select.set_value('전체')
            energy_min_input.set_value(None)
            energy_max_input.set_value(None)
            green_min_input.set_value(None)
            green_max_input.set_value(None)
            ratio_min_input.set_value(None)
            ratio_max_input.set_value(None)

            table.rows = original_env_data
            table.update()
            result_count.text = f'검색 결과: {len(original_env_data)}건'

        # =======================
        # 검색 UI 카드
        # =======================
        with ui.card().classes('w-full p-2 mb-4 rounded-xl shadow-sm bg-gray-50 text-xs'):
            with ui.row().classes('items-center justify-between mb-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.icon('tune', size='1rem').classes('text-blue-600')
                    ui.label('검색 필터').classes('text-sm font-semibold text-gray-700')
                result_count = ui.label(f'검색 결과: {len(env_data)}건').classes('text-xs text-gray-500')

            uniform_width = 'w-24 h-7 text-xs'

            with ui.row().classes('items-center gap-4 flex-wrap'):
                ui.label('년도').classes('text-xs font-medium text-gray-600')
                with ui.row().classes('items-center gap-1'):
                    year_from_input = ui.number(placeholder='시작', precision=0, min=2000, max=2100) \
                        .props('outlined dense clearable').classes(uniform_width)
                    ui.label('~').classes('text-gray-400 text-xs')
                    year_to_input = ui.number(placeholder='끝', precision=0, min=2000, max=2100) \
                        .props('outlined dense clearable').classes(uniform_width)

                ui.label('재생에너지').classes('text-xs font-medium text-gray-600')
                renewable_select = ui.select(['전체', 'Y', 'N'], value='전체') \
                    .props('outlined dense clearable').classes('w-28 h-7 text-xs')

                ui.label('에너지(MWh)').classes('text-xs font-medium text-gray-600')
                with ui.row().classes('items-center gap-1'):
                    energy_min_input = ui.number(placeholder='최소', precision=0, min=0) \
                        .props('outlined dense clearable').classes(uniform_width)
                    ui.label('~').classes('text-gray-400 text-xs')
                    energy_max_input = ui.number(placeholder='최대', precision=0, min=0) \
                        .props('outlined dense clearable').classes(uniform_width)

                ui.label('온실가스(tCO2e)').classes('text-xs font-medium text-gray-600')
                with ui.row().classes('items-center gap-1'):
                    green_min_input = ui.number(placeholder='최소', precision=0, min=0) \
                        .props('outlined dense clearable').classes(uniform_width)
                    ui.label('~').classes('text-gray-400 text-xs')
                    green_max_input = ui.number(placeholder='최대', precision=0, min=0) \
                        .props('outlined dense clearable').classes(uniform_width)

                ui.label('재생비율(%)').classes('text-xs font-medium text-gray-600')
                with ui.row().classes('items-center gap-1'):
                    ratio_min_input = ui.number(placeholder='최소', precision=1, min=0, max=100) \
                        .props('outlined dense clearable').classes(uniform_width)
                    ui.label('~').classes('text-gray-400 text-xs')
                    ratio_max_input = ui.number(placeholder='최대', precision=1, min=0, max=100) \
                        .props('outlined dense clearable').classes(uniform_width)

                # 버튼들을 오른쪽으로 밀어서 배치
                with ui.row().classes('items-center gap-2 ml-auto'):
                    ui.button('검색', color='primary', on_click=apply_filters) \
                        .classes('rounded-md shadow-sm px-4 py-2 text-sm font-medium')
                    ui.button('초기화', color='secondary', on_click=reset_filters) \
                        .classes('rounded-md shadow-sm px-4 py-2 text-sm font-medium')

        # =======================
        # (아래 생략: 신규등록 다이얼로그, 엑셀 업로드 다이얼로그, 테이블, 버튼)
        # =======================


        # =======================
        # 신규등록 다이얼로그
        # =======================
        with ui.dialog() as dialog, ui.card().classes('p-4 w-[400px]'):
            dialog_title = ui.label('📝 신규 환경 데이터 추가').classes('text-base font-semibold text-gray-700 mb-3')

            inputs = {}
            inputs['년도'] = ui.number(label='년도', precision=0, min=2000, max=2100).classes('w-full mb-2')
            inputs['에너지 사용량'] = ui.number(label='에너지 사용량(MWh)', precision=2, min=0).classes('w-full mb-2')
            inputs['온실가스 배출량'] = ui.number(label='온실가스 배출량(tCO2e)', precision=2, min=0).classes('w-full mb-2')
            inputs['재생에너지 사용여부'] = ui.select(['Y', 'N'], value='N', label='재생에너지 사용여부').classes('w-full mb-2')
            inputs['재생에너지 비율'] = ui.number(label='재생에너지 비율(%)', precision=1, min=0, max=100).classes('w-full mb-2')

            def save_env():
                try:
                    new_env = Env(
                        year=int(inputs['년도'].value),
                        energy_use=float(inputs['에너지 사용량'].value),
                        green_use=float(inputs['온실가스 배출량'].value),
                        renewable_yn=inputs['재생에너지 사용여부'].value,
                        renewable_ratio=float(inputs['재생에너지 비율'].value) / 100,
                    )
                    db_session.add(new_env)
                    db_session.commit()
                    ui.notify(f"{new_env.year}년 데이터가 저장되었습니다 ✅", type='positive')
                    dialog.close()
                except Exception as e:
                    db_session.rollback()
                    ui.notify(f"저장 실패: {str(e)}", type='negative')

            with ui.row().classes('justify-end gap-2 mt-3'):
                ui.button('저장', on_click=save_env, color='primary').classes('px-4 py-1 text-sm')
                ui.button('취소', on_click=dialog.close, color='secondary').classes('px-4 py-1 text-sm')

        def open_new_dialog():
            dialog_title.text = '📝 신규 환경 데이터 추가'
            for key, comp in inputs.items():
                if hasattr(comp, "set_value"):
                    comp.set_value(None)
            dialog.open()

        # =======================
        # 엑셀 업로드 다이얼로그
        # =======================
        with ui.dialog() as excel_dialog, ui.card().classes('p-4 w-[600px]'):
            ui.label('📥 환경 데이터 엑셀 업로드').classes('text-base font-bold text-green-700 mb-3')
            upload_result = ui.label().classes('text-sm mb-2')
            preview_data = []

            def handle_upload(e):
                nonlocal preview_data
                try:
                    content = e.content.read()
                    df = pd.read_excel(io.BytesIO(content))
                    df.columns = df.columns.str.strip()
                    preview_data = df.to_dict(orient='records')
                    ui.notify(f'✅ {len(preview_data)}건 로드됨', type='positive')
                except Exception as err:
                    ui.notify(f'엑셀 오류: {str(err)}', type='negative')

            ui.upload(label='엑셀 파일 선택', auto_upload=True, on_upload=handle_upload) \
                .props('accept=".xlsx,.xls"').classes('w-full mb-3')

            def save_all():
                try:
                    for row in preview_data:
                        new_env = Env(
                            year=int(row['년도']),
                            energy_use=float(row['에너지 사용량']),
                            green_use=float(row['온실가스 배출량']),
                            renewable_yn=row['재생에너지 사용여부'],
                            renewable_ratio=float(row['재생에너지 비율']) / 100,
                        )
                        db_session.merge(new_env)
                    db_session.commit()
                    ui.notify('엑셀 데이터 저장 완료 ✅', type='positive')
                    excel_dialog.close()
                except Exception as err:
                    db_session.rollback()
                    ui.notify(f'엑셀 저장 오류: {str(err)}', type='negative')

            with ui.row().classes('justify-end gap-2 mt-3'):
                ui.button('저장', on_click=save_all, color='primary').classes('px-4 py-1 text-sm')
                ui.button('취소', on_click=excel_dialog.close, color='secondary').classes('px-4 py-1 text-sm')

        def open_excel_dialog():
            excel_dialog.open()

        # =======================
        # 테이블
        # =======================
        table = ui.table(columns=columns, rows=filtered_env_data, row_key='year_pk').classes(
            'w-full text-center bordered dense flat rounded shadow-sm'
        ).props('table-header-class=bg-blue-200 text-black')

        table.add_slot('body-cell-actions', '''
            <q-td key="actions" :props="props">
                <q-btn @click="$parent.$emit('edit_row', props.row)" 
                    dense round flat color="primary" icon="edit" size="sm" class="q-mr-xs">
                    <q-tooltip>수정</q-tooltip>
                </q-btn>
                <q-btn @click="$parent.$emit('delete_row', props.row)" 
                    dense round flat color="negative" icon="delete" size="sm">
                    <q-tooltip>삭제</q-tooltip>
                </q-btn>
            </q-td>
        ''')

        # =======================
        # 액션 버튼 (테이블 아래)
        # =======================
        with ui.row().classes('mt-3 gap-3'):
            ui.button('신규등록', color='blue', on_click=open_new_dialog) \
                .props('color=blue-200 text-color=black').classes('rounded-lg shadow-md')
            ui.button('엑셀 일괄등록', color='green', on_click=open_excel_dialog) \
                .props('color=green-200 text-color=black').classes('rounded-lg shadow-md')
