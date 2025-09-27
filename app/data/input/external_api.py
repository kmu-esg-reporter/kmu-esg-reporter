"""External API connector for ESG data collection."""

import httpx
from typing import Dict, List, Any, Optional
import logging
import asyncio

from .base_importer import BaseImporter

logger = logging.getLogger(__name__)


class ExternalAPIConnector(BaseImporter):
    """Connector for external ESG data APIs."""
    
    def __init__(self, db, company_id: int):
        super().__init__(db, company_id)
        self.client = None
    
    def import_data(self, api_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import data from external APIs."""
        try:
            # Start import log
            import_log = self.start_import_log("external_api")
            
            results = {
                'imported': 0,
                'rejected': 0,
                'errors': [],
                'api_results': {}
            }
            
            # Process each API configuration
            for config in api_configs:
                try:
                    api_name = config.get('name', 'unknown')
                    logger.info(f"Fetching data from {api_name} API...")
                    
                    # Fetch data from API
                    api_data = asyncio.run(self._fetch_api_data(config))
                    
                    # Process API response
                    api_results = self._process_api_data(api_data, config)
                    
                    results['imported'] += api_results['imported']
                    results['rejected'] += api_results['rejected']
                    results['errors'].extend(api_results['errors'])
                    results['api_results'][api_name] = api_results
                    
                except Exception as e:
                    logger.error(f"Error processing API {config.get('name', 'unknown')}: {str(e)}")
                    results['errors'].append(f"API {config.get('name', 'unknown')}: {str(e)}")
            
            # Commit changes
            try:
                self.db.commit()
                self.update_import_log(
                    processed=sum(len(result.get('raw_data', [])) for result in results['api_results'].values()),
                    imported=results['imported'],
                    rejected=results['rejected'],
                    errors=results['errors']
                )
                self.finish_import_log("success" if results['imported'] > 0 else "partial")
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error committing API data: {str(e)}")
                self.finish_import_log("error")
                raise
            
            return results
            
        except Exception as e:
            logger.error(f"Error importing from external APIs: {str(e)}")
            self.finish_import_log("error")
            raise
    
    async def _fetch_api_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from a single API."""
        url = config['url']
        headers = config.get('headers', {})
        params = config.get('params', {})
        method = config.get('method', 'GET').upper()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == 'GET':
                response = await client.get(url, headers=headers, params=params)
            elif method == 'POST':
                data = config.get('data', {})
                response = await client.post(url, headers=headers, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
    
    def _process_api_data(self, api_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process data from API response."""
        results = {
            'imported': 0,
            'rejected': 0,
            'errors': [],
            'raw_data': api_data
        }
        
        try:
            # Extract relevant data based on configuration
            data_path = config.get('data_path', [])
            if data_path:
                # Navigate to nested data
                current_data = api_data
                for path_key in data_path:
                    current_data = current_data.get(path_key, {})
                records = current_data if isinstance(current_data, list) else [current_data]
            else:
                records = api_data if isinstance(api_data, list) else [api_data]
            
            # Transform and import each record
            transformer = config.get('transformer')
            for i, record in enumerate(records):
                try:
                    # Transform record based on configuration
                    if transformer:
                        esg_data = self._transform_record(record, transformer)
                    else:
                        esg_data = record
                    
                    # Add API source information
                    esg_data['data_source'] = 'external_api'
                    esg_data['source_file'] = config.get('name', 'external_api')
                    
                    # Validate data
                    validation_errors = self.validate_data(esg_data)
                    if validation_errors:
                        results['rejected'] += 1
                        results['errors'].extend([f"Record {i + 1}: {error}" for error in validation_errors])
                        continue
                    
                    # Create ESG data record
                    esg_record = self.create_esg_data(esg_data, "external_api")
                    self.db.add(esg_record)
                    results['imported'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing API record {i + 1}: {str(e)}")
                    results['rejected'] += 1
                    results['errors'].append(f"Record {i + 1}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error processing API data: {str(e)}")
            results['errors'].append(f"Data processing error: {str(e)}")
        
        return results
    
    def _transform_record(self, record: Dict[str, Any], transformer: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API record using transformer configuration."""
        transformed = {}
        
        # Field mapping
        field_mapping = transformer.get('field_mapping', {})
        for esg_field, api_field in field_mapping.items():
            if api_field in record:
                transformed[esg_field] = record[api_field]
        
        # Value transformations
        value_transforms = transformer.get('value_transforms', {})
        for field, transform in value_transforms.items():
            if field in transformed:
                transformed[field] = self._apply_transform(transformed[field], transform)
        
        # Default values
        defaults = transformer.get('defaults', {})
        for field, default_value in defaults.items():
            transformed.setdefault(field, default_value)
        
        return transformed
    
    def _apply_transform(self, value: Any, transform: Dict[str, Any]) -> Any:
        """Apply transformation to a value."""
        transform_type = transform.get('type')
        
        if transform_type == 'multiply':
            return float(value) * transform.get('factor', 1.0)
        elif transform_type == 'divide':
            return float(value) / transform.get('factor', 1.0)
        elif transform_type == 'map':
            mapping = transform.get('mapping', {})
            return mapping.get(value, value)
        elif transform_type == 'unit_conversion':
            # Implement unit conversions
            from_unit = transform.get('from_unit')
            to_unit = transform.get('to_unit')
            return self._convert_units(value, from_unit, to_unit)
        else:
            return value
    
    def _convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between units."""
        # Simple unit conversion examples
        conversions = {
            ('kg', 'tonnes'): 0.001,
            ('tonnes', 'kg'): 1000,
            ('kWh', 'GJ'): 0.0036,
            ('GJ', 'kWh'): 277.78,
            ('L', 'm³'): 0.001,
            ('m³', 'L'): 1000
        }
        
        conversion_factor = conversions.get((from_unit, to_unit))
        if conversion_factor:
            return value * conversion_factor
        else:
            logger.warning(f"No conversion available from {from_unit} to {to_unit}")
            return value
    
    def get_available_apis(self) -> List[Dict[str, Any]]:
        """Get list of available ESG data APIs."""
        return [
            {
                'name': 'EPA GHG Emissions',
                'description': 'US EPA Greenhouse Gas Emissions data',
                'url': 'https://api.epa.gov/easey/emissions',
                'data_types': ['Environmental'],
                'subcategories': ['Carbon Emissions'],
                'free': True
            },
            {
                'name': 'World Bank Climate Data',
                'description': 'World Bank Climate Change Knowledge Portal',
                'url': 'https://climateknowledgeportal.worldbank.org/api',
                'data_types': ['Environmental'],
                'subcategories': ['Climate Data'],
                'free': True
            },
            {
                'name': 'CDP Disclosure Data',
                'description': 'Carbon Disclosure Project data',
                'url': 'https://data.cdp.net/api',
                'data_types': ['Environmental', 'Social', 'Governance'],
                'subcategories': ['Carbon Emissions', 'Water Security', 'Forest Risk'],
                'free': False
            },
            {
                'name': 'S&P Global ESG Scores',
                'description': 'S&P Global ESG scoring data',
                'url': 'https://api.spglobal.com/esg',
                'data_types': ['Environmental', 'Social', 'Governance'],
                'subcategories': ['ESG Scores', 'Risk Assessment'],
                'free': False
            }
        ]
    
    def create_api_config_template(self, api_name: str) -> Dict[str, Any]:
        """Create configuration template for specific API."""
        templates = {
            'EPA GHG Emissions': {
                'name': 'EPA GHG Emissions',
                'url': 'https://api.epa.gov/easey/emissions',
                'method': 'GET',
                'headers': {'Accept': 'application/json'},
                'params': {
                    'facilityId': 'FACILITY_ID_HERE',
                    'year': 2023
                },
                'data_path': ['data'],
                'transformer': {
                    'field_mapping': {
                        'category': 'Environmental',
                        'subcategory': 'Carbon Emissions',
                        'metric_name': 'CO2 Emissions',
                        'value': 'co2MassEmissions',
                        'unit': 'tonnes',
                        'reporting_year': 'year'
                    },
                    'defaults': {
                        'quality_score': 0.9
                    }
                }
            },
            'Custom API': {
                'name': 'Custom API',
                'url': 'https://your-api-endpoint.com/data',
                'method': 'GET',
                'headers': {
                    'Authorization': 'Bearer YOUR_TOKEN',
                    'Accept': 'application/json'
                },
                'params': {},
                'data_path': [],
                'transformer': {
                    'field_mapping': {
                        'category': 'api_category_field',
                        'metric_name': 'api_metric_field',
                        'value': 'api_value_field',
                        'unit': 'api_unit_field'
                    },
                    'value_transforms': {
                        'value': {
                            'type': 'multiply',
                            'factor': 1.0
                        }
                    },
                    'defaults': {
                        'quality_score': 0.7
                    }
                }
            }
        }
        
        return templates.get(api_name, templates['Custom API'])