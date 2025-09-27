"""Manual data input handler for ESG data."""

from typing import Dict, List, Any
import logging

from .base_importer import BaseImporter

logger = logging.getLogger(__name__)


class ManualInputHandler(BaseImporter):
    """Handle manual ESG data input."""
    
    def import_data(self, data_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import manually entered ESG data."""
        try:
            # Start import log
            import_log = self.start_import_log("manual")
            
            results = {
                'imported': 0,
                'rejected': 0,
                'errors': []
            }
            
            for i, data in enumerate(data_records):
                try:
                    # Validate data
                    validation_errors = self.validate_data(data)
                    if validation_errors:
                        results['rejected'] += 1
                        results['errors'].extend([f"Record {i + 1}: {error}" for error in validation_errors])
                        continue
                    
                    # Create ESG data record
                    esg_data = self.create_esg_data(data, "manual")
                    self.db.add(esg_data)
                    results['imported'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing manual record {i + 1}: {str(e)}")
                    results['rejected'] += 1
                    results['errors'].append(f"Record {i + 1}: {str(e)}")
            
            # Commit changes
            try:
                self.db.commit()
                self.update_import_log(
                    processed=len(data_records),
                    imported=results['imported'],
                    rejected=results['rejected'],
                    errors=results['errors']
                )
                self.finish_import_log("success" if results['imported'] > 0 else "partial")
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error committing manual data: {str(e)}")
                self.finish_import_log("error")
                raise
            
            return results
            
        except Exception as e:
            logger.error(f"Error importing manual data: {str(e)}")
            self.finish_import_log("error")
            raise
    
    def create_single_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single ESG data record."""
        try:
            # Validate data
            validation_errors = self.validate_data(data)
            if validation_errors:
                return {
                    'success': False,
                    'errors': validation_errors
                }
            
            # Create ESG data record
            esg_data = self.create_esg_data(data, "manual")
            self.db.add(esg_data)
            self.db.commit()
            
            return {
                'success': True,
                'record_id': esg_data.id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating single record: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def update_record(self, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing ESG data record."""
        try:
            # Get existing record
            esg_data = self.db.query(self.db_model).filter_by(id=record_id, company_id=self.company_id).first()
            if not esg_data:
                return {
                    'success': False,
                    'errors': ['Record not found']
                }
            
            # Validate updated data
            validation_errors = self.validate_data(data)
            if validation_errors:
                return {
                    'success': False,
                    'errors': validation_errors
                }
            
            # Update fields
            for key, value in data.items():
                if hasattr(esg_data, key) and key not in ['id', 'company_id', 'created_at']:
                    setattr(esg_data, key, value)
            
            # Update raw_data
            esg_data.raw_data = data
            
            self.db.commit()
            
            return {
                'success': True,
                'record_id': esg_data.id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating record {record_id}: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def get_form_template(self) -> Dict[str, Any]:
        """Get template for manual data entry form."""
        return {
            'categories': ['Environmental', 'Social', 'Governance'],
            'environmental_subcategories': [
                'Energy Consumption',
                'Water Usage',
                'Waste Management',
                'Carbon Emissions',
                'Renewable Energy',
                'Environmental Compliance'
            ],
            'social_subcategories': [
                'Employee Safety',
                'Diversity & Inclusion',
                'Training & Development',
                'Community Investment',
                'Customer Satisfaction',
                'Human Rights'
            ],
            'governance_subcategories': [
                'Board Composition',
                'Executive Compensation',
                'Risk Management',
                'Ethics & Compliance',
                'Data Security',
                'Stakeholder Engagement'
            ],
            'common_units': [
                'kWh', 'GJ', 'L', 'm³', 'kg', 'tonnes', 
                'CO2e', '%', 'count', 'hours', 'days', 'USD'
            ],
            'required_fields': ['category', 'metric_name'],
            'optional_fields': [
                'subcategory', 'metric_code', 'value', 'unit', 
                'text_value', 'period_start', 'period_end', 
                'reporting_year', 'notes'
            ]
        }