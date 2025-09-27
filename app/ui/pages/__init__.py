"""UI page components."""


from .dashboard import DashboardPage
from .data_input import DataInputPage
from .visualization import VisualizationPage
# from .chatbot import ChatbotPage
from .chatbot_langgraph import ChatbotPage
from .company_management import CompanyManagementPage
from .hr import HRPage
from .environment import EnvironmentPage

__all__ = [
    "DashboardPage", 
    "DataInputPage", 
    "VisualizationPage", 
    "ChatbotPage",
    "CompanyManagementPage",
    "HRPage",
    "EnvironmentPage"
]