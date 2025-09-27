"""Excel file importer for ESG data."""

import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from .base_importer import BaseImporter

logger = logging.getLogger(__name__)


class ExcelImporter(BaseImporter):
    """Import ESG data from Excel files."""
    
    def __init__(self, db, company_id: int):
        super().__init__(db, company_id)
        self.supported_formats = ['.xlsx', '.xls', '.csv']
    
    def import_data(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Import data from Excel file."""
        try:
            file_path = Path(file_path)
            
            # Validate file format
            if file_path.suffix.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            # Start import log
            import_log = self.start_import_log("excel", str(file_path))
            
            # Read file based on format
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            return self._process_dataframe(df, str(file_path))
            
        except Exception as e:
            logger.error(f"Error importing Excel file {file_path}: {str(e)}")
            self.finish_import_log("error")
            raise
    
    def _process_dataframe(self, df: pd.DataFrame, source_file: str) -> Dict[str, Any]:
        """Process pandas DataFrame and import ESG data."""
        results = {
            'imported': 0,
            'rejected': 0,
            'errors': []
        }
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Map common column variations
        column_mapping = {
            'esg_category': 'category',
            'esg_subcategory': 'subcategory',
            'metric': 'metric_name',
            'indicator': 'metric_name',
            'measure': 'metric_name',
            'data_value': 'value',
            'measurement': 'value',
            'amount': 'value',
            'year': 'reporting_year',
            'period': 'reporting_year'
        }
        
        df = df.rename(columns=column_mapping)
        
        for index, row in df.iterrows():
            try:
                # Convert row to dict and clean NaN values
                data = row.to_dict()
                data = {k: v for k, v in data.items() if pd.notna(v)}
                data['source_file'] = source_file
                
                # Validate data
                validation_errors = self.validate_data(data)
                if validation_errors:
                    results['rejected'] += 1
                    results['errors'].extend([f"Row {index + 2}: {error}" for error in validation_errors])
                    continue
                
                # Create ESG data record
                esg_data = self.create_esg_data(data, "excel")
                self.db.add(esg_data)
                results['imported'] += 1
                
            except Exception as e:
                logger.error(f"Error processing row {index + 2}: {str(e)}")
                results['rejected'] += 1
                results['errors'].append(f"Row {index + 2}: {str(e)}")
        
        # Commit changes
        try:
            self.db.commit()
            self.update_import_log(
                processed=len(df),
                imported=results['imported'],
                rejected=results['rejected'],
                errors=results['errors']
            )
            self.finish_import_log("success" if results['imported'] > 0 else "partial")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error committing data: {str(e)}")
            self.finish_import_log("error")
            raise
        
        return results
    
    def get_excel_preview(self, file_path: str, sheet_name: Optional[str] = None, rows: int = 5) -> Dict[str, Any]:
        """Get preview of Excel file data."""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, nrows=rows)
                sheets = None
            else:
                # Get sheet names
                excel_file = pd.ExcelFile(file_path)
                sheets = excel_file.sheet_names
                
                # Read specified sheet or first sheet
                sheet_to_read = sheet_name or sheets[0]
                df = pd.read_excel(file_path, sheet_name=sheet_to_read, nrows=rows)
            
            # Convert to preview format
            preview = {
                'sheets': sheets,
                'columns': df.columns.tolist(),
                'data': df.to_dict('records'),
                'total_rows': len(df)
            }
            
            return preview
            
        except Exception as e:
            logger.error(f"Error previewing Excel file {file_path}: {str(e)}")
            raise
    
    def validate_excel_structure(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Validate Excel file structure for ESG data import."""
        try:
            preview = self.get_excel_preview(file_path, sheet_name, rows=1)
            columns = [col.lower().replace(' ', '_') for col in preview['columns']]
            
            # Check for required columns
            required_columns = ['category', 'metric_name']
            missing_columns = []
            
            # Map common variations
            column_variations = {
                'category': ['category', 'esg_category', 'type'],
                'metric_name': ['metric_name', 'metric', 'indicator', 'measure']
            }
            
            for req_col in required_columns:
                found = False
                for variation in column_variations.get(req_col, [req_col]):
                    if variation in columns:
                        found = True
                        break
                if not found:
                    missing_columns.append(req_col)
            
            # Identify potential value columns
            value_columns = [col for col in columns if any(term in col for term in ['value', 'amount', 'measurement', 'data'])]
            
            validation_result = {
                'valid': len(missing_columns) == 0,
                'missing_columns': missing_columns,
                'detected_columns': columns,
                'value_columns': value_columns,
                'recommendations': []
            }
            
            if missing_columns:
                validation_result['recommendations'].append(f"Please ensure your file has columns for: {', '.join(missing_columns)}")
            
            if not value_columns:
                validation_result['recommendations'].append("No value columns detected. Please include columns with numeric ESG data.")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating Excel structure {file_path}: {str(e)}")
            raise