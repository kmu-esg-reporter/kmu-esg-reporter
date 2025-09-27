"""Data input page for ESG data."""

from nicegui import ui
from typing import Optional
from sqlalchemy.orm import Session

from .base_page import BasePage


class DataInputPage(BasePage):
    """Data input page for various ESG data sources."""
    
    async def render(self, db_session: Session, company_id: Optional[int] = None) -> None:
        """Render data input page."""
        await super().render(db_session, company_id)
        
        ui.label('Data Input').classes('text-h3 font-weight-bold mb-4')
        
        if not company_id:
            ui.label('Please select a company first').classes('text-negative')
            return
        
        # Input methods
        with ui.row().classes('w-full gap-4 mb-6'):
            # Excel upload
            with ui.card().classes('flex-1'):
                with ui.card_section():
                    ui.icon('upload_file', size='3rem').classes('text-primary mb-3')
                    ui.label('Excel Upload').classes('text-h6 font-weight-bold mb-2')
                    ui.label('Upload ESG data from Excel files').classes('text-body2 text-grey-7 mb-4')
                    ui.button('Upload File', icon='upload').props('color=primary')
            
            # Manual entry
            with ui.card().classes('flex-1'):
                with ui.card_section():
                    ui.icon('edit', size='3rem').classes('text-secondary mb-3')
                    ui.label('Manual Entry').classes('text-h6 font-weight-bold mb-2')
                    ui.label('Enter ESG data manually').classes('text-body2 text-grey-7 mb-4')
                    ui.button('Add Data', icon='add').props('color=secondary')
            
            # ERP Connection
            with ui.card().classes('flex-1'):
                with ui.card_section():
                    ui.icon('link', size='3rem').classes('text-accent mb-3')
                    ui.label('ERP Connection').classes('text-h6 font-weight-bold mb-2')
                    ui.label('Connect to ERP systems').classes('text-body2 text-grey-7 mb-4')
                    ui.button('Configure', icon='settings').props('color=accent')
        
        # Recent imports
        with ui.card().classes('w-full'):
            with ui.card_section():
                ui.label('Recent Imports').classes('text-h6 font-weight-bold mb-3')
                ui.label('No recent imports').classes('text-grey-6 text-center py-4')