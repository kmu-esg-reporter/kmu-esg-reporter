# ESG Reporter

2025-2 국민대 소프트웨어융합대학원 AI 해커톤에서 만든 중소기업용 ESG 보고서 및 챗봇 서비스

## 🌱 프로젝트 개요

ESG Reporter는 중소기업을 위한 종합적인 ESG(Environmental, Social, Governance) 데이터 관리 및 보고서 생성 플랫폼입니다. NiceGUI를 기반으로 한 직관적인 웹 인터페이스와 LangChain/LangGraph를 활용한 AI 챗봇을 제공합니다.

## ✨ 주요 기능

### 📊 데이터 수집 및 관리
- **다양한 입력 방식**: 엑셀 파일 업로드, 수기 입력, ERP 연동, 외부 API 연결
- **확장 가능한 아키텍처**: 새로운 데이터 소스 쉽게 추가 가능
- **데이터 품질 관리**: 자동 검증 및 품질 점수 부여

### 📈 시각화 및 분석
- **대화형 차트**: Plotly 기반의 다양한 ESG 시각화
- **카테고리별 분석**: Environmental, Social, Governance 영역별 성과 분석
- **트렌드 분석**: 시간에 따른 ESG 성과 변화 추적

### 🤖 AI 챗봇
- **LangChain + LangGraph**: 고도화된 대화형 AI 시스템
- **ESG 전문 지식**: ESG 보고서 생성, 데이터 분석, 개선 제안
- **확장 가능**: 추후 자체 모델 및 추론 서버 연결 가능

### 📋 보고서 생성
- **자동 보고서**: AI 기반 종합 ESG 보고서 생성
- **다양한 포맷**: HTML, PDF, Excel 등 다중 포맷 지원
- **맞춤형 보고서**: 회사별, 기간별 맞춤 보고서

## 🏗️ 시스템 아키텍처

```
├── app/
│   ├── core/                    # 핵심 모듈
│   │   ├── database/           # 데이터베이스 모델 및 연결
│   │   ├── auth/               # 인증 및 권한 관리
│   │   └── logging/            # 로깅 설정
│   ├── data/                   # 데이터 처리
│   │   ├── input/              # 데이터 입력 (Excel, ERP, API)
│   │   ├── processors/         # 데이터 처리 및 분석
│   │   ├── visualization/      # 시각화 모듈
│   │   └── models/             # 데이터 모델
│   ├── services/               # 외부 서비스
│   │   ├── chatbot/            # LangChain 챗봇
│   │   └── external/           # 외부 API 연동
│   ├── ui/                     # NiceGUI 기반 UI
│   │   ├── pages/              # 페이지 컴포넌트
│   │   └── components/         # 재사용 가능 컴포넌트
│   └── utils/                  # 유틸리티 함수
├── config/                     # 설정 파일
├── static/                     # 정적 파일
├── uploads/                    # 업로드된 파일
└── tests/                      # 테스트 코드
```

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/kmu-esg-reporter/kmu-esg-reporter.git
cd kmu-esg-reporter

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (OpenAI API 키 등 설정)
```

### 3. 데이터베이스 설정

```bash
# SQLite (기본값) - 별도 설정 불요

# MySQL 설정 시
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/esg_reporter
DATABASE_TYPE=mysql

# PostgreSQL 설정 시
DATABASE_URL=postgresql://username:password@localhost:5432/esg_reporter
DATABASE_TYPE=postgresql
```

### 4. 애플리케이션 실행

```bash
python main.py
```

브라우저에서 `http://localhost:8080` 접속

## 📋 사용 방법

### 1. 회사 정보 등록
- Company Management 페이지에서 회사 정보 등록
- 업종, 규모 등 기본 정보 입력

### 2. ESG 데이터 입력
- **Excel 업로드**: 기존 ESG 데이터가 있는 Excel 파일 업로드
- **수기 입력**: 웹 폼을 통한 직접 데이터 입력
- **ERP 연동**: SAP, Oracle 등 ERP 시스템 연결
- **외부 API**: 공개 ESG 데이터 API 연동

### 3. 데이터 시각화
- Dashboard에서 ESG 카테고리별 현황 확인
- Visualization 페이지에서 상세 차트 분석
- 트렌드 분석 및 성과 추적

### 4. AI 챗봇 활용
- 자연어로 ESG 데이터 질의
- 자동 보고서 생성 요청
- 개선 방안 및 벤치마크 정보 제공

## 🔧 개발 가이드

### 새로운 데이터 소스 추가

```python
from app.data.input.base_importer import BaseImporter

class CustomImporter(BaseImporter):
    def import_data(self, source):
        # 커스텀 데이터 소스 처리 로직
        pass
```

### 새로운 시각화 추가

```python
from app.data.visualization.esg_charts import ESGChartGenerator

class CustomCharts(ESGChartGenerator):
    def create_custom_chart(self, df):
        # 커스텀 차트 생성 로직
        pass
```

### 챗봇 기능 확장

```python
from app.services.chatbot.esg_chatbot import ESGChatbot

# 새로운 의도(intent) 처리 추가
def _handle_custom_intent(self, message, intent, context):
    # 커스텀 의도 처리 로직
    pass
```

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 모듈 테스트
pytest tests/test_data_import.py

# 커버리지 포함 테스트
pytest --cov=app tests/
```

## 📦 배포

### Docker 배포
```bash
# Docker 이미지 빌드
docker build -t esg-reporter .

# 컨테이너 실행
docker run -p 8080:8080 esg-reporter
```

### 클라우드 배포
- **AWS**: ECS, Lambda, 또는 EC2
- **Google Cloud**: Cloud Run, App Engine
- **Azure**: Container Instances, App Service

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원 및 문의

- **Issues**: [GitHub Issues](https://github.com/kmu-esg-reporter/kmu-esg-reporter/issues)
- **Email**: ai@kmu.ac.kr
- **Documentation**: [프로젝트 위키](https://github.com/kmu-esg-reporter/kmu-esg-reporter/wiki)

## 🙏 감사의 말

이 프로젝트는 국민대학교 소프트웨어융합대학원 AI 해커톤에서 시작되었습니다. ESG 보고의 중요성이 증대되는 시점에서 중소기업의 ESG 경영을 지원하고자 합니다.

---

**Made with ❤️ by KMU AI Team**
