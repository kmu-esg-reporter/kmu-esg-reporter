"""Base class for data importers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database.models import Company, ESGData, DataImportLog


class BaseImporter(ABC):
    """Base class for all data importers."""
    
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        self.import_log = None
        
    def start_import_log(self, import_type: str, source_file: Optional[str] = None) -> DataImportLog:
        """Start a new import log entry."""
        self.import_log = DataImportLog(
            company_id=self.company_id,
            import_type=import_type,
            source_file=source_file,
            status="in_progress"
        )
        self.db.add(self.import_log)
        self.db.commit()
        return self.import_log
    
    def update_import_log(self, 
                         processed: int = 0, 
                         imported: int = 0, 
                         rejected: int = 0,
                         errors: Optional[List[str]] = None) -> None:
        """Update import log with statistics."""
        if self.import_log:
            self.import_log.records_processed += processed
            self.import_log.records_imported += imported
            self.import_log.records_rejected += rejected
            
            if errors:
                current_errors = self.import_log.error_log or []
                current_errors.extend(errors)
                self.import_log.error_log = current_errors
            
            self.db.commit()
    
    def finish_import_log(self, status: str = "success") -> None:
        """Finish the import log."""
        if self.import_log:
            self.import_log.status = status
            self.db.commit()
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate data before import."""
        errors = []
        
        # Required fields validation
        required_fields = ['category', 'metric_name']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Category validation
        valid_categories = ['Environmental', 'Social', 'Governance']
        if data.get('category') and data['category'] not in valid_categories:
            errors.append(f"Invalid category: {data['category']}. Must be one of {valid_categories}")
        
        # Value validation
        if data.get('value') is not None:
            try:
                float(data['value'])
            except (ValueError, TypeError):
                errors.append(f"Invalid numeric value: {data.get('value')}")
        
        return errors
    
    def create_esg_data(self, data: Dict[str, Any], source: str) -> ESGData:
        """Create ESG data record."""
        esg_data = ESGData(
            company_id=self.company_id,
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            metric_name=data.get('metric_name'),
            metric_code=data.get('metric_code'),
            value=data.get('value'),
            unit=data.get('unit'),
            text_value=data.get('text_value'),
            data_source=source,
            source_file=data.get('source_file'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            reporting_year=data.get('reporting_year', datetime.now().year),
            raw_data=data,
            notes=data.get('notes')
        )
        return esg_data
    
    @abstractmethod
    def import_data(self, source: Any) -> Dict[str, Any]:
        """Import data from source. Must be implemented by subclasses."""
        pass