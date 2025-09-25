"""ESG Report Generation Chatbot using LangGraph - Updated for new schema."""

import uuid
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
import logging

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing_extensions import TypedDict
from typing import Annotated

from sqlalchemy.orm import Session
from app.core.database.models import CmpInfo, EmpInfo, Env, ChatSession, Report, DataImportLog  # 새로운 모델 import
from app.data.processors.data_processor import ESGDataProcessor
from app.services.report.ai_enrich import ESGEnricher
from app.services.report.generator import build_report_html
from app.services.report.renderer import html_to_pdf
from config.settings import settings

logger = logging.getLogger(__name__)

class ESGAgentState(TypedDict):
    """ESG 챗봇의 상태를 정의하는 TypedDict"""
    messages: Annotated[List, add_messages]
    query: str
    intent: str  # data_query, report_generation, analysis_request, general_query
    cmp_num: Optional[str]  # company_id -> cmp_num으로 변경
    company_context: Dict[str, Any]
    esg_data_summary: Dict[str, Any]
    tool_results: Dict[str, Any]
    response_content: str
    needs_data_collection: bool
    report_generated: bool
    session_id: str
    iteration_count: int

class ESGReportChatbot:
    """ESG 보고서 생성을 위한 LangGraph 기반 챗봇"""
    
    def __init__(self, db: Session, cmp_num: Optional[str] = None, log_element=None):
        self.db = db
        self.cmp_num = cmp_num or "6182618882"  # 더미 데이터 회사코드 (기본값)
        self.log_element = log_element
        self.data_processor = ESGDataProcessor(db)
        self.max_iterations = 3
        api_key = settings.openai.OPENAI_API_KEY if settings.openai else None
        self._last_outcomes: Dict[str, dict] = {}  # session_id -> outcome dict
        
        # OpenAI LLM 설정
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            openai_api_key=api_key,
            streaming=True,
            temperature=0.7
        )
        self.llm_nostream = ChatOpenAI(
            model=self.llm.model_name, 
            temperature=0.7, 
            streaming=False, 
            openai_api_key=api_key
        )
        
        # ESG 시스템 프롬프트
        self.system_prompt = """
        당신은 ESG(환경, 사회, 지배구조) 보고서 생성 전문 AI 어시스턴트입니다.
        중소기업을 위한 ESG 데이터 분석과 보고서 작성을 지원합니다.

        주요 기능:
        1. ESG 데이터 분석 및 시각화
        2. 종합적인 ESG 보고서 생성
        3. 데이터 품질 평가 및 개선 제안
        4. 업계 벤치마킹 및 모범 사례 제시
        5. 규제 준수 가이드라인 제공

        항상 다음을 포함하여 답변하세요:
        - 현재 성과 수준
        - 시간에 따른 트렌드
        - 개선이 필요한 영역
        - 구체적인 실행 방안
        """
        
        self._setup_tools()
        self._build_workflow()
    
    def _setup_tools(self):
        """ESG 전용 도구들 설정"""
        
        # @tool # 202509251600 임시백업
        # def get_company_esg_data(cmp_num: str, category: str = None) -> str:
        #     """회사의 ESG 데이터를 조회합니다."""
        #     try:
        #         # 새로운 데이터 처리기 사용
        #         comprehensive_report = self.data_processor.generate_comprehensive_report(cmp_num)
        #         if 'error' in comprehensive_report:
        #             return comprehensive_report['error']
                
        #         return json.dumps(comprehensive_report['esg_metrics'], ensure_ascii=False, indent=2)
        #     except Exception as e:
        #         return f"데이터 조회 중 오류 발생: {str(e)}"
        
        @tool
        def get_company_esg_data(cmp_num: str, category: str = None) -> str:
            """회사의 실제 ESG 원본 데이터와 메트릭을 모두 제공"""
            try:
                # 1. 원본 데이터 수집
                emp_df = self.dataprocessor.get_employee_data()
                env_df = self.dataprocessor.get_environmental_data() 
                
                # 2. 메트릭 계산
                comprehensive_report = self.dataprocessor.generate_comprehensive_report(cmp_num)
                
                # 3. 원본 + 메트릭 모두 반환
                result = {
                    "raw_data": {
                        "employee_count": len(emp_df),
                        "employee_sample": emp_df.head(5).to_dict('records') if not emp_df.empty else [],
                        "environmental_years": env_df['year'].unique().tolist() if not env_df.empty else [],
                        "environmental_sample": env_df.head(5).to_dict('records') if not env_df.empty else []
                    },
                    "calculated_metrics": comprehensive_report.get("esg_metrics", {}),
                    "company_info": comprehensive_report.get("company_info", {})
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            except Exception as e:
                return f"데이터 조회 중 오류 발생: {str(e)}"

                

        
        @tool
        def analyze_esg_trends(cmp_num: str, category: str = "all") -> str:
            """특정 ESG 지표의 트렌드를 분석합니다."""
            try:
                # 환경 데이터 트렌드 분석
                env_df = self.data_processor.get_environmental_data()
                if env_df.empty:
                    return "환경 데이터가 없어 트렌드 분석을 수행할 수 없습니다."
                
                env_metrics = self.data_processor.calculate_environmental_metrics(env_df)
                return json.dumps(env_metrics, ensure_ascii=False, indent=2)
            except Exception as e:
                return f"트렌드 분석 중 오류 발생: {str(e)}"
        
        @tool
        def identify_data_gaps(cmp_num: str) -> str:
            """ESG 데이터의 누락 영역을 식별합니다."""
            try:
                gaps = self.data_processor.identify_data_gaps(cmp_num)
                return json.dumps(gaps, ensure_ascii=False, indent=2)
            except Exception as e:
                return f"데이터 갭 분석 중 오류 발생: {str(e)}"
        
        @tool
        async def generate_esg_report(cmp_num: str, report_type: str = "comprehensive") -> str:
            """ESG 보고서를 HTML 형식으로 생성하고 ID를 포함한 결과를 반환합니다."""
            logger.info(f"'{cmp_num}'에 대한 보고서 생성 도구를 시작합니다.")
            try:
                company = self.db.query(CmpInfo).filter_by(cmp_num=cmp_num).first()
                if not company:
                    raise ValueError("회사 정보를 찾을 수 없습니다.")

                report_data = self.data_processor.generate_comprehensive_report(cmp_num)
                if 'error' in report_data:
                    raise ValueError(f"보고서 데이터 생성 실패 - {report_data['error']}")
                
                company_info = report_data.get("company_info", {})
                esg_metrics = report_data.get("esg_metrics", {})
                
                 # LLM으로 텍스트/권고 보강 (구조화)
                enricher = ESGEnricher(self.llm_nostream)  # self.llm은 __init__에서 ChatOpenAI(...)
                enriched = await enricher._enrich_with_guard(esg_metrics)

                # 템플릿 입력은 우리가 만든 정규화 루틴이 처리
                # build_report_html에 전달할 때, 'ai' 블럭을 함께 넘겨 템플릿에서 사용
                period_label = f"{datetime.now().year - 1}년도 기준"
                final_html = build_report_html(
                    company_info=company_info,
                    period_label=period_label,
                    summary_metrics=enriched.get("summary", {}),     # 상단 Executive Summary 카드에 활용
                    env_metrics={**esg_metrics.get("environment", {}), "ai": enriched["environment"]["ai"]},
                    soc_metrics={**esg_metrics.get("social", {}), "ai": enriched["social"]["ai"]},
                    gov_metrics={**esg_metrics.get("governance", {}), "ai": enriched["governance"]["ai"]},
                )

                report_title = f"{company.cmp_nm} ESG 보고서 ({datetime.now().strftime('%Y-%m-%d')})"
                report = Report(
                    company_id=cmp_num, 
                    title=report_title,
                    report_type=report_type,
                    content=final_html,
                    generated_by="langgraph_chatbot",
                    format="html"
                )
                self.db.add(report)
                self.db.commit()
                self.db.refresh(report)
                
                logger.info(f"성공: 보고서를 DB에 저장했습니다. (ID: {report.id})")
                
                result = {
                    "status": "success",
                    "message": f"'{report.title}' 보고서가 생성되었습니다.",
                    "report_id": report.id 
                }
                return json.dumps(result)

            except Exception as e:
                logger.error(f"보고서 생성 도중 오류 발생: {e}", exc_info=True)
                return json.dumps({"status": "error", "message": str(e)})
        
        self.tools = [get_company_esg_data, analyze_esg_trends, identify_data_gaps, generate_esg_report]
    
    def _build_workflow(self):
        """ESG 챗봇 워크플로우 구성"""
        workflow_builder = StateGraph(ESGAgentState)
        
        # 노드 정의 (동일)
        workflow_builder.add_node("analyze_intent", self._analyze_intent)
        workflow_builder.add_node("load_company_context", self._load_company_context)
        workflow_builder.add_node("check_data_availability", self._check_data_availability)
        workflow_builder.add_node("execute_esg_tools", self._execute_esg_tools)
        workflow_builder.add_node("generate_response", self._generate_response)
        workflow_builder.add_node("save_conversation", self._save_conversation)
        workflow_builder.add_node("handle_no_data", self._handle_no_data)
        workflow_builder.add_node("handle_no_company", self._handle_no_company)
        
        # 워크플로우 구축 (동일)
        workflow_builder.add_edge(START, "analyze_intent")
        
        workflow_builder.add_conditional_edges(
            "analyze_intent",
            self._decide_company_check,
            {
                "has_company": "load_company_context",
                "no_company": "handle_no_company"
            }
        )
        
        workflow_builder.add_edge("handle_no_company", END)
        workflow_builder.add_edge("load_company_context", "check_data_availability")
        
        workflow_builder.add_conditional_edges(
            "check_data_availability",
            self._decide_data_availability,
            {
                "has_data": "execute_esg_tools",
                "no_data": "handle_no_data"
            }
        )
        
        workflow_builder.add_edge("handle_no_data", "save_conversation")
        workflow_builder.add_edge("execute_esg_tools", "generate_response")
        workflow_builder.add_edge("generate_response", "save_conversation")
        workflow_builder.add_edge("save_conversation", END)
        
        # 그래프 컴파일
        self.agent_workflow = workflow_builder.compile()
    
    def _analyze_intent(self, state: ESGAgentState) -> ESGAgentState:
        """사용자 의도 분석 - UI 컨텍스트 포함"""
        query = state.get("query", "").lower()
        ui_context = state.get("ui_context") or {}
        
        # UI에서 선택된 intent가 있으면 우선 사용
        if ui_context and ui_context.get("selected_intent"):
            intent = ui_context["selected_intent"]
        else:
            # 기존 텍스트 분석 로직
            if any(keyword in query for keyword in ["보고서", "리포트", "생성", "작성"]):
                intent = "report_generation"
            elif any(keyword in query for keyword in ["데이터", "수치", "현황", "보여줘"]):
                intent = "data_query"
            elif any(keyword in query for keyword in ["분석", "트렌드", "비교", "개선"]):
                intent = "analysis_request"
            else:
                intent = "general_query"
        
        return {
            "intent": intent,
            "ui_context": ui_context or {},
            "iteration_count": 0,
            "messages": [SystemMessage(content="ESG 챗봇이 질문을 분석중입니다...")]
        }
    
    def _decide_company_check(self, state: ESGAgentState) -> Literal["has_company", "no_company"]:
        """회사 선택 여부 확인"""
        return "has_company" if state.get("cmp_num") else "no_company"
    
    def _load_company_context(self, state: ESGAgentState) -> ESGAgentState:
        """회사 컨텍스트 로드"""
        cmp_num = state.get("cmp_num")
        if not cmp_num:
            return {"company_context": {}}
        
        try:
            company_info = self.data_processor.get_company_info(cmp_num)
            if company_info:
                context = {
                    "cmp_nm": company_info["cmp_nm"],
                    "cmp_industry": company_info["cmp_industry"],
                    "cmp_sector": company_info["cmp_sector"],
                    "cmp_addr": company_info["cmp_addr"]
                }
                return {"company_context": context}
            else:
                return {"company_context": {}}
        except Exception as e:
            logger.error(f"회사 컨텍스트 로드 오류: {str(e)}")
            return {"company_context": {}}
    
    def _check_data_availability(self, state: ESGAgentState) -> ESGAgentState:
        """ESG 데이터 가용성 확인"""
        cmp_num = state.get("cmp_num")
        if not cmp_num:
            return {"needs_data_collection": True}
        
        try:
            # 직원 및 환경 데이터 확인
            emp_df = self.data_processor.get_employee_data()
            env_df = self.data_processor.get_environmental_data()
            
            has_data = not emp_df.empty or not env_df.empty
            
            esg_summary = {}
            if has_data:
                # 간단한 요약 정보 생성
                esg_summary = {
                    "employee_count": len(emp_df),
                    "environmental_years": len(env_df),
                    "latest_env_year": int(env_df['year'].max()) if not env_df.empty else None
                }
            
            return {
                "needs_data_collection": not has_data,
                "esg_data_summary": esg_summary
            }
        except Exception as e:
            logger.error(f"데이터 가용성 확인 오류: {str(e)}")
            return {"needs_data_collection": True}
    
    def _decide_data_availability(self, state: ESGAgentState) -> Literal["has_data", "no_data"]:
        """데이터 가용성에 따른 분기"""
        return "no_data" if state.get("needs_data_collection", True) else "has_data"
    
    async def _execute_esg_tools(self, state: ESGAgentState) -> ESGAgentState:
        """ESG 도구 실행 - UI 컨텍스트 반영"""
        intent = state.get("intent", "")
        cmp_num = state.get("cmp_num")
        ui_context = state.get("ui_context", {})
        
        # UI에서 선택된 카테고리 정보 활용
        selected_category = ui_context.get("selected_category", "all")
        selected_period = ui_context.get("selected_period", "current_year")
        
        tool_results = {}
        logger.info(f"분석된 의도: {intent}, 선택된 카테고리: {selected_category}, 선택된 기간: {selected_period}")
        
        try:
            if intent == "data_query":
                # 데이터 조회 도구 실행
                result = self.tools[0].invoke({"cmp_num": cmp_num, "category": selected_category})
                tool_results["esg_data"] = result
                tool_results["requested_category"] = selected_category
                tool_results["requested_period"] = selected_period
                
            elif intent == "analysis_request":
                # 트렌드 분석 도구 실행
                result = self.tools[1].invoke({"cmp_num": cmp_num, "category": selected_category})
                tool_results["trend_analysis"] = result
                
                # 데이터 갭 분석
                gap_result = self.tools[2].invoke({"cmp_num": cmp_num})
                tool_results["data_gaps"] = gap_result
                tool_results["analysis_category"] = selected_category
                tool_results["analysis_period"] = selected_period
                
            elif intent == "report_generation":
                # 보고서 생성 도구 실행
                report_type = "comprehensive" if selected_category == "all" else "category_specific"
                result = await self.tools[3].ainvoke({"cmp_num": cmp_num, "report_type": report_type})
                tool_results["generated_report"] = result
                tool_results["report_category"] = selected_category
                tool_results["report_period"] = selected_period
                
        except Exception as e:
            logger.error(f"도구 실행 오류: {str(e)}")
            tool_results["error"] = str(e)
        
        return {"tool_results": tool_results}
    
    def _generate_response(self, state: ESGAgentState) -> ESGAgentState:
        """응답 생성"""
        query = state.get("query", "")
        intent = state.get("intent", "")
        company_context = state.get("company_context", {})
        tool_results = state.get("tool_results", {})
        
        # 프롬프트 구성
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            사용자 질문: {query}
            의도: {intent}
            회사 정보: {json.dumps(company_context, ensure_ascii=False)}
            도구 실행 결과: {json.dumps(tool_results, ensure_ascii=False)}

            위 정보를 바탕으로 사용자의 질문에 대한 전문적이고 유용한 답변을 제공해주세요.
            """)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content
        except Exception as e:
            content = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        
        return {
            "response_content": content,
            "report_generated": intent == "report_generation" and "generated_report" in tool_results
        }
    
    def _handle_no_data(self, state: ESGAgentState) -> ESGAgentState:
        """데이터 없음 처리"""
        company_name = state.get("company_context", {}).get("cmp_nm", "선택된 회사")
        
        response = f"""
{company_name}의 ESG 데이터가 아직 등록되지 않았습니다.

ESG 보고서를 생성하기 위해서는 다음 데이터가 필요합니다:

**환경(Environmental) 데이터:**
- 에너지 사용량
- 온실가스 배출량
- 재생에너지 사용 비율

**사회(Social) 데이터:**
- 직원 정보 (성별, 이사회 참여, 산재 발생 등)
- 직원 다양성 지표
- 안전사고 현황

**지배구조(Governance) 데이터:**
- 사외이사 수
- 윤리경영 정책
- 컴플라이언스 현황

데이터 입력 페이지에서 ESG 데이터를 먼저 등록해 주시기 바랍니다.
        """
        
        return {"response_content": response.strip()}
    
    def _handle_no_company(self, state: ESGAgentState) -> ESGAgentState:
        """회사 미선택 처리"""
        response = """
ESG 분석과 보고서 생성을 위해 먼저 회사를 선택해 주세요.

상단의 회사 선택 드롭다운에서 분석하고자 하는 회사를 선택하신 후 다시 질문해 주시기 바랍니다.

새로운 회사를 등록하시려면 '회사 관리' 페이지를 이용해 주세요.
        """
        
        return {"response_content": response.strip()}
    
    def _save_conversation(self, state: ESGAgentState) -> ESGAgentState:
        """대화 저장"""
        session_id = state.get("session_id")
        query = state.get("query", "")
        response = state.get("response_content", "")
        
        if not session_id:
            return state
        
        try:
            session = self.db.query(ChatSession).filter_by(session_id=session_id).first()
            if session:
                messages = session.messages or []
                messages.extend([
                    {
                        "type": "human",
                        "content": query,
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "type": "ai", 
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    }
                ])
                
                session.messages = messages
                session.message_count = len(messages)
                session.last_activity = datetime.now()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"대화 저장 오류: {str(e)}")
        
        return state
    
    # 공개 메서드들
    def create_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """새 채팅 세션 생성"""
        session_id = str(uuid.uuid4())
        chat_session = ChatSession(
            session_id=session_id,
            company_id=self.cmp_num,  # company_id -> cmp_num으로 변경
            user_id=user_id,
            title=title or "ESG 채팅 세션",
            messages=[],
            context={}
        )
        
        self.db.add(chat_session)
        self.db.commit()
        return session_id
    
    async def stream_response(self, query: str, session_id: str, context: Dict[str, Any] = None) -> str: # type: ignore
        """스트리밍 응답 처리 - 추가 컨텍스트 지원"""
        try:
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "intent": "",
                "cmp_num": self.cmp_num,  # company_id -> cmp_num으로 변경
                "company_context": {},
                "esg_data_summary": {},
                "tool_results": {},
                "response_content": "",
                "needs_data_collection": False,
                "report_generated": False,
                "session_id": session_id,
                "iteration_count": 0,
                "ui_context": context or {}  # UI 컨텍스트 추가
            }
            
            # 워크플로우 실행
            complete_response = ""
            last_tool_results, last_report_generated = {}, False
            async for chunk in self.agent_workflow.astream(initial_state, stream_mode="values"):
                if "response_content" in chunk and chunk["response_content"]:
                    current_content = chunk["response_content"]
                    if len(current_content) > len(complete_response):
                        new_tokens = current_content[len(complete_response):]
                        complete_response = current_content
                        
                        # 토큰 단위 스트리밍
                        for char in new_tokens:
                            yield char
                            await asyncio.sleep(0.01)
                
                if "tool_results" in chunk:
                    last_tool_results = chunk["tool_results"] or last_tool_results
                if "report_generated" in chunk:
                    last_report_generated = bool(chunk["report_generated"])
            
            report_id = None
            try:
                # 도구가 JSON 문자열을 반환했다면 파싱
                gen = last_tool_results.get("generated_report")
                if isinstance(gen, str):
                    parsed = json.loads(gen)
                    report_id = parsed.get("report_id")
                elif isinstance(gen, dict):
                    report_id = gen.get("report_id")
            except Exception:
                pass

            self._last_outcomes[session_id] = {
                "report_generated": last_report_generated or bool(report_id),
                "report_id": report_id,
                "tool_results": last_tool_results,
                "full_text": complete_response,
            }

            if not complete_response.strip():
                complete_response = "죄송합니다. 응답을 생성할 수 없습니다."
                for char in complete_response:
                    yield char
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            error_message = f"오류가 발생했습니다: {str(e)}"
            for char in error_message:
                yield char
                await asyncio.sleep(0.01)

    def get_last_outcome(self, session_id: str) -> Dict[str, Any]:
        """마지막 대화 결과 가져오기"""
        return self._last_outcomes.get(session_id, {})

# --- PDF Export Helpers -------------------------------------------------

    def get_latest_report(self, cmp_num: str) -> Optional[Report]:
        """해당 회사의 최신 보고서(HTML)를 반환."""
        try:
            return (
                self.db.query(Report)
                .filter(Report.company_id == cmp_num)
                .order_by(Report.created_at.desc())
                .first()
            )
        except Exception as e:
            logger.error(f"get_latest_report error: {e}")
            return None


    def export_report_to_pdf(self, report_id: Optional[int] = None, out_dir: str = "generated_reports") -> Optional[str]:
        """
        최신(또는 지정) 보고서의 HTML을 PDF로 변환해 파일 경로를 반환.
        기존에 만든 html_to_pdf 렌더러 사용.
        """
        try:
            os.makedirs(out_dir, exist_ok=True)
            report = None
            if report_id:
                report = self.db.query(Report).filter(Report.id == report_id).first()
            else:
                report = self.db.query(Report).filter(Report.company_id == self.cmp_num).order_by(Report.created_at.desc()).first()

            if not report:
                logger.warning(f"{self.cmp_num}에 대해 내보낼 보고서가 없습니다.")
                return None
            if (report.format or "").lower() != "html" or not report.content:
                logger.warning("보고서 포맷이 HTML이 아니거나 내용이 비어있습니다.")
                return None

            # 파일명 생성
            company = self.db.query(CmpInfo).filter_by(cmp_num=report.company_id).first()
            company_name = company.cmp_nm if company else "Unknown_Company"
            safe_title = f"ESG_Report_{company_name}".replace("/", "_")
            pdf_path = os.path.join(out_dir, f"{safe_title}.pdf")

            # ✅ WeasyPrint 대신 우리가 만든 PDF 변환 함수 사용
            html_to_pdf(report.content, pdf_path)

            # DB에 파일 경로 업데이트
            report.file_path = pdf_path
            report.file_size = os.path.getsize(pdf_path)
            self.db.commit()

            return pdf_path
        except Exception as e:
            logger.error(f"export_report_to_pdf 오류: {e}", exc_info=True)
            return None