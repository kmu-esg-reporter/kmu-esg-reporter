"""Chatbot page for ESG AI assistant."""

from nicegui import ui
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from .base_page import BasePage
from app.services.chatbot.esg_chatbot import ESGChatbot


class ChatbotPage(BasePage):
    """Chatbot page for ESG AI assistant."""
    
    def __init__(self):
        super().__init__()
        self.chatbot = None
        self.session_id = None
        self.messages = []
    
    async def render(self, db_session: Session, company_id: Optional[int] = None) -> None:
        """Render chatbot page."""
        await super().render(db_session, company_id)
        
        ui.label('ESG AI Assistant').classes('text-h3 font-weight-bold mb-4')
        
        # Initialize chatbot
        self.chatbot = ESGChatbot(db_session, company_id)
        if not self.session_id:
            self.session_id = self.chatbot.create_session()
        
        # Chat interface
        with ui.column().classes('w-full h-96'):
            # Messages area
            with ui.scroll_area().classes('flex-grow w-full border rounded p-4') as self.messages_area:
                if not self.messages:
                    with ui.row().classes('items-start gap-3 mb-4'):
                        ui.avatar(icon='smart_toy', color='primary')
                        with ui.column():
                            ui.label('AI Assistant').classes('font-weight-bold text-sm')
                            ui.label('Hello! I\'m your ESG reporting assistant. I can help you analyze your ESG data, generate reports, and provide insights. How can I assist you today?').classes('text-body2')
            
            # Input area
            with ui.row().classes('w-full gap-2 mt-4'):
                self.message_input = ui.input(
                    placeholder='Ask me about your ESG data, request a report, or get insights...'
                ).classes('flex-grow').on('keydown.enter', self._send_message)
                
                ui.button('Send', icon='send', on_click=self._send_message).props('color=primary')
    
    async def _send_message(self) -> None:
        """Send message to chatbot."""
        if not self.message_input.value.strip():
            return
        
        user_message = self.message_input.value.strip()
        self.message_input.value = ''
        
        # Add user message to UI
        with self.messages_area:
            with ui.row().classes('items-start gap-3 mb-4 justify-end'):
                with ui.column().classes('text-right'):
                    ui.label('You').classes('font-weight-bold text-sm')
                    ui.label(user_message).classes('text-body2 bg-primary text-white rounded px-3 py-2')
                ui.avatar(icon='person', color='secondary')
        
        # Get AI response (simplified)
        if self.chatbot and self.chatbot.langchain_handler.chat_model:
            try:
                response = await self._get_ai_response(user_message)
            except Exception as e:
                response = f"I apologize, but I encountered an error: {str(e)}. Please try again."
        else:
            response = self._get_fallback_response(user_message)
        
        # Add AI response to UI
        with self.messages_area:
            with ui.row().classes('items-start gap-3 mb-4'):
                ui.avatar(icon='smart_toy', color='primary')
                with ui.column():
                    ui.label('AI Assistant').classes('font-weight-bold text-sm')
                    ui.label(response).classes('text-body2')
        
        # Scroll to bottom
        self.messages_area.scroll_to(percent=1)
    
    async def _get_ai_response(self, message: str) -> str:
        """Get AI response using chatbot."""
        result = self.chatbot.chat(message, self.session_id)
        return result.get('response', 'I apologize, but I could not process your request.')
    
    def _get_fallback_response(self, message: str) -> str:
        """Get fallback response when AI is not available."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['report', 'generate']):
            return "I'd be happy to help you generate an ESG report. However, I need access to your company's ESG data first. Please upload your data through the Data Input section."
        
        elif any(word in message_lower for word in ['data', 'show', 'display']):
            return "To show you ESG data insights, please make sure you have uploaded your ESG data first through the Data Input section."
        
        elif any(word in message_lower for word in ['help', 'what can you do']):
            return """I'm your ESG reporting assistant! I can help you with:

• Analyzing your ESG data and identifying trends
• Generating comprehensive ESG reports
• Providing insights on Environmental, Social, and Governance metrics
• Suggesting improvements for your ESG performance
• Answering questions about ESG best practices

To get started, please upload your ESG data, then ask me specific questions about your performance."""
        
        else:
            return "I'm here to help with your ESG reporting needs. Please upload your ESG data first, then ask me about your environmental, social, or governance performance!"