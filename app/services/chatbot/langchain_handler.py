"""LangChain and LangGraph integration for ESG chatbot."""

from typing import Dict, List, Any, Optional
import logging
from functools import lru_cache

try:
    from langchain_community.llms import OpenAI
    from langchain_community.chat_models import ChatOpenAI
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferWindowMemory
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from typing_extensions import TypedDict, Annotated
except ImportError:
    # Fallback if LangChain/LangGraph not available
    logging.warning("LangChain/LangGraph not available. Using fallback implementation.")
    OpenAI = None
    ChatOpenAI = None

from config.settings import settings

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State for LangGraph conversation flow."""
    messages: Annotated[list, add_messages]
    user_input: str
    intent: str
    context: Dict[str, Any]
    response: str


class LangChainHandler:
    """Handler for LangChain and LangGraph operations."""
    
    def __init__(self):
        self.llm = None
        self.chat_model = None
        self.workflow = None
        self._initialize_models()
        self._setup_langgraph()
    
    def _initialize_models(self) -> None:
        """Initialize LangChain models."""
        if not settings.openai or not settings.openai.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured. Chatbot will use fallback responses.")
            return
        
        try:
            # Initialize OpenAI models
            self.chat_model = ChatOpenAI(
                openai_api_key=settings.openai.OPENAI_API_KEY,
                model=settings.openai.OPENAI_MODEL,
                temperature=settings.openai.OPENAI_TEMPERATURE
            )
            
            self.llm = OpenAI(
                openai_api_key=settings.openai.OPENAI_API_KEY,
                temperature=settings.openai.OPENAI_TEMPERATURE
            )
            
            logger.info("LangChain models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LangChain models: {str(e)}")
            self.chat_model = None
            self.llm = None
    
    def _setup_langgraph(self) -> None:
        """Setup LangGraph workflow for conversation flow."""
        if not self.chat_model:
            return
        
        try:
            # Create workflow graph
            workflow = StateGraph(GraphState)
            
            # Add nodes
            workflow.add_node("analyze_intent", self._analyze_intent_node)
            workflow.add_node("process_esg_query", self._process_esg_query_node)
            workflow.add_node("generate_response", self._generate_response_node)
            workflow.add_node("format_output", self._format_output_node)
            
            # Define edges
            workflow.set_entry_point("analyze_intent")
            workflow.add_edge("analyze_intent", "process_esg_query")
            workflow.add_edge("process_esg_query", "generate_response")
            workflow.add_edge("generate_response", "format_output")
            workflow.add_edge("format_output", END)
            
            # Compile workflow
            self.workflow = workflow.compile()
            
            logger.info("LangGraph workflow initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up LangGraph workflow: {str(e)}")
            self.workflow = None
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using LangChain."""
        if not self.chat_model:
            return self._fallback_response(prompt)
        
        try:
            messages = []
            
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            messages.append(HumanMessage(content=prompt))
            
            response = self.chat_model(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._fallback_response(prompt)
    
    def process_conversation(self, 
                           user_input: str, 
                           context: Dict[str, Any],
                           conversation_history: List[BaseMessage] = None) -> Dict[str, Any]:
        """Process conversation using LangGraph workflow."""
        if not self.workflow:
            return {
                'response': self._fallback_response(user_input),
                'intent': 'general',
                'confidence': 0.5
            }
        
        try:
            # Initial state
            initial_state = GraphState(
                messages=conversation_history or [],
                user_input=user_input,
                intent="",
                context=context,
                response=""
            )
            
            # Run workflow
            result = self.workflow.invoke(initial_state)
            
            return {
                'response': result['response'],
                'intent': result['intent'],
                'confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}")
            return {
                'response': self._fallback_response(user_input),
                'intent': 'general',
                'confidence': 0.5
            }
    
    def _analyze_intent_node(self, state: GraphState) -> GraphState:
        """Analyze user intent node for LangGraph."""
        user_input = state['user_input'].lower()
        
        # ESG-specific intent analysis
        if any(word in user_input for word in ['report', 'generate', 'create']):
            intent = 'report_generation'
        elif any(word in user_input for word in ['show', 'display', 'what', 'data']):
            intent = 'data_query'
        elif any(word in user_input for word in ['analyze', 'trend', 'compare']):
            intent = 'analysis'
        elif any(word in user_input for word in ['help', 'how', 'what is']):
            intent = 'help'
        else:
            intent = 'general'
        
        state['intent'] = intent
        return state
    
    def _process_esg_query_node(self, state: GraphState) -> GraphState:
        """Process ESG-specific query node."""
        intent = state['intent']
        context = state['context']
        
        # Add ESG-specific context processing
        if 'esg_summary' in context:
            # Process ESG data summary
            esg_data = context['esg_summary']
            state['context']['processed_data'] = self._summarize_esg_data(esg_data)
        
        return state
    
    def _generate_response_node(self, state: GraphState) -> GraphState:
        """Generate response node using chat model."""
        if not self.chat_model:
            state['response'] = self._fallback_response(state['user_input'])
            return state
        
        try:
            # Create prompt based on intent and context
            prompt = self._create_contextual_prompt(state)
            
            messages = [
                SystemMessage(content=self._get_esg_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            response = self.chat_model(messages)
            state['response'] = response.content
            
        except Exception as e:
            logger.error(f"Error in generate_response_node: {str(e)}")
            state['response'] = self._fallback_response(state['user_input'])
        
        return state
    
    def _format_output_node(self, state: GraphState) -> GraphState:
        """Format final output node."""
        # Add any final formatting or post-processing
        response = state['response']
        
        # Ensure response is properly formatted
        if not response.endswith('.'):
            response += '.'
        
        state['response'] = response
        return state
    
    def _create_contextual_prompt(self, state: GraphState) -> str:
        """Create contextual prompt based on state."""
        user_input = state['user_input']
        intent = state['intent']
        context = state['context']
        
        prompt_parts = [f"User question: {user_input}"]
        
        if intent == 'report_generation':
            prompt_parts.append("The user wants to generate an ESG report.")
        elif intent == 'data_query':
            prompt_parts.append("The user is asking about specific ESG data.")
        elif intent == 'analysis':
            prompt_parts.append("The user wants ESG data analysis.")
        
        # Add context information
        if 'company' in context:
            company_info = context['company']
            prompt_parts.append(f"Company: {company_info.get('name', 'Unknown')}")
            prompt_parts.append(f"Industry: {company_info.get('industry', 'Unknown')}")
        
        if 'processed_data' in context:
            prompt_parts.append(f"ESG Data Summary: {context['processed_data']}")
        
        return "\n\n".join(prompt_parts)
    
    def _summarize_esg_data(self, esg_data: Dict[str, Any]) -> str:
        """Summarize ESG data for context."""
        summary_parts = []
        
        for category, data in esg_data.items():
            summary_parts.append(f"{category}: {data.get('total_metrics', 0)} metrics")
            
            if 'value_stats' in data:
                stats = data['value_stats']
                summary_parts.append(f"  - Average value: {stats.get('mean', 0):.2f}")
                summary_parts.append(f"  - Range: {stats.get('min', 0):.2f} - {stats.get('max', 0):.2f}")
        
        return "\n".join(summary_parts)
    
    def _get_esg_system_prompt(self) -> str:
        """Get ESG-specific system prompt."""
        return """
        You are an ESG (Environmental, Social, and Governance) reporting assistant for small and medium enterprises.
        
        Key responsibilities:
        1. Help companies understand their ESG performance
        2. Generate comprehensive ESG reports
        3. Identify improvement opportunities
        4. Provide industry benchmarking insights
        5. Suggest ESG best practices
        
        Always provide:
        - Data-driven insights based on actual company data
        - Clear explanations of ESG concepts
        - Actionable recommendations
        - Industry context when relevant
        
        If data is missing or incomplete, clearly explain what's needed and how to improve data collection.
        """
    
    def _fallback_response(self, user_input: str) -> str:
        """Provide fallback response when AI models are not available."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['report', 'generate']):
            return """I'd be happy to help you generate an ESG report. However, I need access to your company's ESG data first. 
            Please upload your ESG data through the data input section, and then I can create a comprehensive report for you."""
        
        elif any(word in user_input_lower for word in ['data', 'show', 'display']):
            return """To show you ESG data, I need to access your company's data first. 
            Please make sure you have uploaded your ESG data through the data management section."""
        
        elif any(word in user_input_lower for word in ['help', 'how']):
            return """I'm here to help with your ESG reporting needs! I can:
            
            1. Generate comprehensive ESG reports
            2. Analyze your ESG data and identify trends
            3. Help you understand ESG metrics and benchmarks
            4. Suggest improvements for your ESG performance
            5. Answer questions about ESG best practices
            
            To get started, please upload your ESG data, and then ask me specific questions about your performance."""
        
        else:
            return """I'm an ESG reporting assistant. I can help you with ESG data analysis, report generation, 
            and performance insights. Please upload your ESG data first, then ask me about your environmental, 
            social, or governance performance."""
    
    @lru_cache(maxsize=100)
    def get_esg_definitions(self, term: str) -> str:
        """Get cached ESG term definitions."""
        definitions = {
            'esg': 'Environmental, Social, and Governance - a framework for assessing company sustainability and ethical practices.',
            'environmental': 'Factors relating to climate change, resource depletion, waste, pollution, and other environmental impacts.',
            'social': 'Factors relating to employee relations, diversity, human rights, community impact, and customer satisfaction.',
            'governance': 'Factors relating to board composition, executive compensation, shareholder rights, and business ethics.',
            'carbon footprint': 'The total amount of greenhouse gases produced directly and indirectly by an organization.',
            'scope 1': 'Direct greenhouse gas emissions from sources owned or controlled by the company.',
            'scope 2': 'Indirect greenhouse gas emissions from purchased electricity, steam, heating, and cooling.',
            'scope 3': 'All other indirect greenhouse gas emissions in the value chain.',
            'materiality': 'ESG issues that have significant impact on business performance or stakeholder decisions.',
            'sustainability': 'Meeting present needs without compromising the ability of future generations to meet their needs.'
        }
        
        return definitions.get(term.lower(), f"I don't have a definition for '{term}'. Please ask about specific ESG concepts.")
    
    def validate_response_quality(self, response: str, user_input: str) -> Dict[str, Any]:
        """Validate the quality of generated response."""
        quality_metrics = {
            'length_appropriate': 50 <= len(response) <= 2000,
            'contains_esg_terms': any(term in response.lower() for term in ['esg', 'environmental', 'social', 'governance']),
            'actionable': any(word in response.lower() for word in ['should', 'recommend', 'suggest', 'consider']),
            'data_driven': any(word in response.lower() for word in ['data', 'metric', 'performance', 'trend']),
            'score': 0.0
        }
        
        # Calculate overall quality score
        score = sum(1 for criterion in quality_metrics.values() if isinstance(criterion, bool) and criterion)
        quality_metrics['score'] = score / 4.0  # 4 boolean criteria
        
        return quality_metrics