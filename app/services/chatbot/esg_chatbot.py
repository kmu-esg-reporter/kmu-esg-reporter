"""ESG Chatbot using LangChain and LangGraph."""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from sqlalchemy.orm import Session

from app.core.database.models import ChatSession, Company, ESGData
from app.data.processors.data_processor import ESGDataProcessor
from .langchain_handler import LangChainHandler

logger = logging.getLogger(__name__)


class ESGChatbot:
    """Main ESG Chatbot class with LangChain integration."""
    
    def __init__(self, db: Session, company_id: Optional[int] = None):
        self.db = db
        self.company_id = company_id
        self.langchain_handler = LangChainHandler()
        self.data_processor = ESGDataProcessor(db)
        self.memory = ConversationBufferWindowMemory(k=10, return_messages=True)
        
        # ESG-specific system prompt
        self.system_prompt = """
        You are an ESG (Environmental, Social, and Governance) reporting assistant for small and medium enterprises (SMEs).
        Your role is to help companies understand their ESG data, generate reports, and provide insights.
        
        Key capabilities:
        1. Analyze ESG data across Environmental, Social, and Governance categories
        2. Generate comprehensive ESG reports
        3. Identify data gaps and improvement opportunities
        4. Provide benchmarking insights
        5. Suggest best practices for ESG improvement
        
        Always provide factual, data-driven responses based on the company's actual ESG data.
        If data is missing or incomplete, clearly state this and suggest ways to improve data collection.
        
        When discussing ESG metrics, always include:
        - Current performance
        - Trends over time
        - Areas for improvement
        - Industry best practices where relevant
        """
    
    def create_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        
        chat_session = ChatSession(
            session_id=session_id,
            company_id=self.company_id,
            user_id=user_id,
            title=title or "ESG Chat Session",
            messages=[],
            context={}
        )
        
        self.db.add(chat_session)
        self.db.commit()
        
        logger.info(f"Created new chat session: {session_id}")
        return session_id
    
    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load existing chat session."""
        session = self.db.query(ChatSession).filter_by(session_id=session_id).first()
        
        if session:
            # Restore conversation history
            self.memory.clear()
            for msg in session.messages or []:
                if msg['type'] == 'human':
                    self.memory.chat_memory.add_message(HumanMessage(content=msg['content']))
                elif msg['type'] == 'ai':
                    self.memory.chat_memory.add_message(AIMessage(content=msg['content']))
        
        return session
    
    def chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """Process chat message and generate response."""
        try:
            # Load session
            session = self.load_session(session_id)
            if not session:
                return {
                    'error': 'Session not found',
                    'session_id': session_id
                }
            
            # Get company context if available
            company_context = self._get_company_context()
            
            # Analyze user intent
            intent = self._analyze_intent(message)
            
            # Generate response based on intent
            if intent['type'] == 'data_query':
                response = self._handle_data_query(message, intent, company_context)
            elif intent['type'] == 'report_generation':
                response = self._handle_report_generation(message, intent, company_context)
            elif intent['type'] == 'analysis_request':
                response = self._handle_analysis_request(message, intent, company_context)
            else:
                response = self._handle_general_query(message, company_context)
            
            # Save conversation
            self._save_conversation(session, message, response['content'])
            
            return {
                'response': response['content'],
                'intent': intent,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}")
            return {
                'error': str(e),
                'session_id': session_id
            }
    
    def _get_company_context(self) -> Dict[str, Any]:
        """Get company and ESG data context."""
        context = {}
        
        if self.company_id:
            # Get company information
            company = self.db.query(Company).filter_by(id=self.company_id).first()
            if company:
                context['company'] = {
                    'name': company.name,
                    'industry': company.industry,
                    'size': company.size
                }
            
            # Get ESG data summary
            esg_data = self.data_processor.get_company_data(self.company_id)
            if not esg_data.empty:
                context['esg_summary'] = self.data_processor.calculate_category_summaries(esg_data)
                context['data_gaps'] = self.data_processor.identify_data_gaps(esg_data)
        
        return context
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user message intent."""
        message_lower = message.lower()
        
        # Data query patterns
        data_keywords = ['show', 'display', 'what is', 'how much', 'data', 'metrics', 'values']
        if any(keyword in message_lower for keyword in data_keywords):
            return {
                'type': 'data_query',
                'confidence': 0.8,
                'entities': self._extract_entities(message)
            }
        
        # Report generation patterns
        report_keywords = ['report', 'generate', 'create', 'summary', 'analysis']
        if any(keyword in message_lower for keyword in report_keywords):
            return {
                'type': 'report_generation',
                'confidence': 0.9,
                'entities': self._extract_entities(message)
            }
        
        # Analysis request patterns
        analysis_keywords = ['analyze', 'trend', 'compare', 'benchmark', 'performance']
        if any(keyword in message_lower for keyword in analysis_keywords):
            return {
                'type': 'analysis_request',
                'confidence': 0.7,
                'entities': self._extract_entities(message)
            }
        
        return {
            'type': 'general_query',
            'confidence': 0.5,
            'entities': []
        }
    
    def _extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """Extract ESG-related entities from message."""
        entities = []
        message_lower = message.lower()
        
        # ESG categories
        categories = ['environmental', 'social', 'governance']
        for category in categories:
            if category in message_lower:
                entities.append({
                    'type': 'category',
                    'value': category.title(),
                    'confidence': 0.9
                })
        
        # Time periods
        time_keywords = ['2023', '2024', 'last year', 'this year', 'quarterly', 'annual']
        for keyword in time_keywords:
            if keyword in message_lower:
                entities.append({
                    'type': 'time_period',
                    'value': keyword,
                    'confidence': 0.8
                })
        
        # Common ESG metrics
        metrics = ['energy', 'water', 'emissions', 'waste', 'carbon', 'diversity', 'safety']
        for metric in metrics:
            if metric in message_lower:
                entities.append({
                    'type': 'metric',
                    'value': metric,
                    'confidence': 0.7
                })
        
        return entities
    
    def _handle_data_query(self, message: str, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data query requests."""
        if not self.company_id:
            return {
                'content': "I need to know which company you're asking about. Please select a company first."
            }
        
        # Extract requested data based on entities
        entities = intent.get('entities', [])
        categories = [e['value'] for e in entities if e['type'] == 'category']
        
        # Get data
        df = self.data_processor.get_company_data(
            self.company_id,
            categories=categories if categories else None
        )
        
        if df.empty:
            return {
                'content': "I don't have any ESG data for your company yet. Would you like me to help you get started with data collection?"
            }
        
        # Generate response using LangChain
        data_summary = self.data_processor.calculate_category_summaries(df)
        
        prompt = f"""
        Based on the user's question: "{message}"
        
        Here's the company's ESG data summary:
        {json.dumps(data_summary, indent=2, default=str)}
        
        Provide a clear, informative response about the company's ESG data.
        """
        
        response = self.langchain_handler.generate_response(prompt, self.system_prompt)
        
        return {
            'content': response,
            'data_included': True
        }
    
    def _handle_report_generation(self, message: str, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation requests."""
        if not self.company_id:
            return {
                'content': "I need to know which company to generate a report for. Please select a company first."
            }
        
        # Get comprehensive data
        df = self.data_processor.get_company_data(self.company_id)
        
        if df.empty:
            return {
                'content': "I cannot generate a report without ESG data. Please upload some data first, then I can create a comprehensive report for you."
            }
        
        # Generate report using LangChain
        data_summary = self.data_processor.calculate_category_summaries(df)
        data_gaps = self.data_processor.identify_data_gaps(df)
        
        prompt = f"""
        Generate a comprehensive ESG report for the company based on this data:
        
        Data Summary:
        {json.dumps(data_summary, indent=2, default=str)}
        
        Data Gaps:
        {json.dumps(data_gaps, indent=2, default=str)}
        
        Company Context:
        {json.dumps(context.get('company', {}), indent=2)}
        
        Create a structured report with:
        1. Executive Summary
        2. Environmental Performance
        3. Social Performance  
        4. Governance Performance
        5. Key Findings and Recommendations
        6. Data Quality Assessment
        """
        
        response = self.langchain_handler.generate_response(prompt, self.system_prompt)
        
        return {
            'content': response,
            'report_generated': True
        }
    
    def _handle_analysis_request(self, message: str, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis and insights requests."""
        if not self.company_id:
            return {
                'content': "I need company data to perform analysis. Please select a company first."
            }
        
        df = self.data_processor.get_company_data(self.company_id)
        
        if df.empty:
            return {
                'content': "I need ESG data to perform analysis. Please upload some data first."
            }
        
        # Perform analysis
        data_summary = self.data_processor.calculate_category_summaries(df)
        
        # Get trends for key metrics
        key_metrics = df['metric_name'].value_counts().head(5).index.tolist()
        trends = {}
        for metric in key_metrics:
            trend_data = self.data_processor.calculate_trends(df, metric)
            if 'error' not in trend_data:
                trends[metric] = trend_data
        
        prompt = f"""
        Analyze the ESG performance based on this request: "{message}"
        
        Data Summary:
        {json.dumps(data_summary, indent=2, default=str)}
        
        Trend Analysis:
        {json.dumps(trends, indent=2, default=str)}
        
        Provide detailed insights, identify patterns, and suggest improvements.
        """
        
        response = self.langchain_handler.generate_response(prompt, self.system_prompt)
        
        return {
            'content': response,
            'analysis_performed': True
        }
    
    def _handle_general_query(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general ESG-related queries."""
        prompt = f"""
        User question: "{message}"
        
        Company context: {json.dumps(context, indent=2, default=str)}
        
        Provide helpful information about ESG reporting, best practices, or answer their question.
        """
        
        response = self.langchain_handler.generate_response(prompt, self.system_prompt)
        
        return {
            'content': response
        }
    
    def _save_conversation(self, session: ChatSession, user_message: str, ai_response: str) -> None:
        """Save conversation to database."""
        # Update messages
        messages = session.messages or []
        messages.extend([
            {
                'type': 'human',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            },
            {
                'type': 'ai', 
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            }
        ])
        
        session.messages = messages
        session.message_count = len(messages)
        session.last_activity = datetime.now()
        
        self.db.commit()
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get chat session history."""
        session = self.db.query(ChatSession).filter_by(session_id=session_id).first()
        
        if not session:
            return {'error': 'Session not found'}
        
        return {
            'session_id': session_id,
            'title': session.title,
            'messages': session.messages or [],
            'message_count': session.message_count,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat()
        }
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        sessions = self.db.query(ChatSession).filter_by(user_id=user_id).order_by(ChatSession.last_activity.desc()).all()
        
        return [
            {
                'session_id': session.session_id,
                'title': session.title,
                'message_count': session.message_count,
                'last_activity': session.last_activity.isoformat(),
                'company_id': session.company_id
            }
            for session in sessions
        ]