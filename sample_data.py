"""Sample data creation for ESG Reporter (new schema: CmpInfo/EmpInfo/Env)."""

from datetime import datetime
from decimal import Decimal
import random

from sqlalchemy.orm import Session

# DB 세션/초기화 유틸 (init_db는 Base.metadata.create_all(...)을 호출해야 함)
from app.core.database import get_db, init_db

# 새 스키마 모델
from app.core.database.models import CmpInfo, EmpInfo, Env, Report, ChatSession


def create_sample_companies(db: Session, cmp_num: str = "6182618882") -> CmpInfo:
    """CMP_INFO 샘플 회사 4개 지점 생성."""
    branches_info = [
        ("서울지점", "서울시 강남구 테헤란로 123"),
        ("부산지점", "부산시 해운대구 센텀남대로 35"), 
        ("대전지점", "대전시 유성구 대학로 291"),
        ("광주지점", "광주시 서구 상무중앙로 61")
    ]
    
    first_company = None
    for branch, addr in branches_info:
        company = CmpInfo(
            cmp_num=cmp_num,
            cmp_branch=branch,
            cmp_nm="그린테크 주식회사",
            cmp_industry="제조업",
            cmp_sector="산업재",
            cmp_addr=addr,
            cmp_extemp=2,
            cmp_ethics_yn="Y",
            cmp_comp_yn="Y",
        )
        db.add(company)
        if first_company is None:
            first_company = company
    
    db.commit()
    db.refresh(first_company)
    return first_company


def create_sample_employees(db: Session, n: int = 20) -> None:
    """EMP_INFO 샘플 직원 n명 생성 (실제 한국인 이름, 지점별 배치)."""
    korean_names = [
        "김민준", "이서준", "박도현", "정하준", "최시우",
        "강지호", "윤준서", "장지후", "임준우", "한도윤",
        "김서연", "이채원", "박지유", "정하윤", "최서현",
        "강예원", "윤지민", "장소율", "임다은", "한하은"
    ]
    
    # branches = ["서울지점", "부산지점", "대전지점", "광주지점"]
    base_id = random.randint(10000, 20000)
    
    
    accident_indices = {4, 7, 11}  # 산업재해 발생값 고정

    for i in range(n):
        accident_count = 1 if i in accident_indices else 0  # 추가

        emp = EmpInfo(
            EMP_ID=base_id + i,
            EMP_NM=korean_names[i],
            EMP_BIRTH=f"{random.randint(1980, 1998):04d}{random.randint(1,12):02d}{random.randint(1,28):02d}",
            EMP_TEL=f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            EMP_EMAIL=f"{korean_names[i].replace(' ', '').lower()}{i+1}@greentech.co.kr",
            EMP_JOIN=f"{random.randint(2015, 2024):04d}{random.randint(1,12):02d}{random.randint(1,28):02d}",
            EMP_ACIDENT_CNT=accident_count,  # (구) random.choice([0, 0, 0, 1])
            EMP_BOARD_YN="Y" if i < 3 else "N",
            EMP_GENDER="1" if i < 10 else "2",  # 남성 10명, 여성 10명
            EMP_COMP="6182618882",
            # EMP_BRANCH=branches[i % 4],  # 지점별 순환 배치
        )
        db.add(emp)
    db.commit()

def create_sample_env(db: Session, years=(2021, 2022, 2023, 2024)) -> None:
    """ENV 샘플: 연도별 에너지/온실가스/재생에너지 비율."""
    energy = 110000.0
    green = 1200.0
    ratio = Decimal("0.120")
    for y in years:
        # 연도 진행에 따라 약간 변화를 주자
        energy *= random.uniform(0.95, 1.05)
        green *= random.uniform(0.92, 1.08)
        ratio = (ratio + Decimal(str(random.uniform(-0.01, 0.02)))).quantize(Decimal("0.001"))
        # 0~1 범위로 클램프
        ratio = max(Decimal("0.000"), min(Decimal("1.000"), ratio))

        env = Env(
            year=y,
            energy_use=round(energy, 2),
            green_use=round(green, 2),
            renewable_yn="Y" if ratio > Decimal("0.000") else "N",
            renewable_ratio=ratio,  # Numeric(5,3) -> Decimal 권장
        )
        db.add(env)
    db.commit()


def create_sample_report(db: Session, cmp_num: str) -> None:
    """샘플 Report 1건(간단 내용) 생성."""
    rpt = Report(
        company_id=cmp_num,  # FK to cmp_info.cmp_num
        title="그린테크 ESG 샘플 보고서 (자동 생성)",
        report_type="annual",
        content="{'summary': '샘플 ESG 보고서 내용입니다.'}",
        summary="샘플 요약",
        generated_by="script",
        format="json",
        status="draft",
        file_path=None,
        file_size=None,
        created_at=datetime.utcnow(),
    )
    db.add(rpt)
    db.commit()


def create_sample_session(db: Session, cmp_num: str) -> None:
    """샘플 ChatSession 1건 생성(선택)."""
    sess = ChatSession(
        session_id="demo-session-0001",
        company_id=cmp_num,
        user_id="demo-user",
        title="데모 ESG 채팅 세션",
        messages=[],
        context={},
        message_count=0,
        last_activity=datetime.utcnow(),
    )
    db.add(sess)
    db.commit()


def create_sample_data():
    """모든 샘플 데이터 생성."""
    print("Initializing database...")
    init_db()  # Base.metadata.create_all(bind=engine) 수행되어야 함

    db = next(get_db())
    try:
        print("Creating sample company (CmpInfo)...")
        company = create_sample_companies(db, cmp_num="6182618882")  # 함수명 변경
        print(f"Created company: {company.cmp_nm} (CMP_NUM: {company.cmp_num})")

        print("Creating sample employees (EmpInfo)...")
        create_sample_employees(db, n=20)

        print("Creating sample environmental data (Env)...")
        create_sample_env(db, years=(2021, 2022, 2023, 2024))

        print("Creating a sample report (Report)...")
        create_sample_report(db, cmp_num=company.cmp_num)

        print("Creating a sample chat session (ChatSession)...")
        create_sample_session(db, cmp_num=company.cmp_num)

        print(
            f"""
Sample data created successfully!

Company: {company.cmp_nm} (CMP_NUM: {company.cmp_num})
- Employees: 15
- Environmental years: 2021~2024
- 1 draft report
- 1 demo chat session

You can now run the application and explore the data.
            """
        )

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
