"""ESG data visualization and chart generation."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ESGChartGenerator:
    """Generate various charts and visualizations for ESG data."""
    
    def __init__(self):
        self.colors = {
            'Environmental': '#2E8B57',  # Sea Green
            'Social': '#4169E1',         # Royal Blue
            'Governance': '#DC143C'      # Crimson
        }
    
    def create_category_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create overview charts for ESG categories."""
        if df.empty:
            return {'error': 'No data available'}
        
        charts = {}
        
        # 1. Category Distribution (Pie Chart)
        category_counts = df['category'].value_counts()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            marker_colors=[self.colors.get(cat, '#808080') for cat in category_counts.index],
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig_pie.update_layout(
            title='ESG Data Distribution by Category',
            font=dict(size=12),
            showlegend=True
        )
        
        charts['category_distribution'] = fig_pie.to_dict()
        
        # 2. Data Sources by Category (Stacked Bar Chart)
        source_by_category = df.groupby(['category', 'data_source']).size().unstack(fill_value=0)
        
        fig_sources = go.Figure()
        
        for source in source_by_category.columns:
            fig_sources.add_trace(go.Bar(
                name=source,
                x=source_by_category.index,
                y=source_by_category[source],
                hovertemplate=f'<b>{source}</b><br>Category: %{{x}}<br>Count: %{{y}}<extra></extra>'
            ))
        
        fig_sources.update_layout(
            title='Data Sources by ESG Category',
            xaxis_title='ESG Category',
            yaxis_title='Number of Data Points',
            barmode='stack',
            font=dict(size=12)
        )
        
        charts['data_sources'] = fig_sources.to_dict()
        
        # 3. Data Quality Score by Category (Box Plot)
        fig_quality = go.Figure()
        
        for category in df['category'].unique():
            category_data = df[df['category'] == category]
            fig_quality.add_trace(go.Box(
                y=category_data['quality_score'],
                name=category,
                marker_color=self.colors.get(category, '#808080'),
                boxpoints='outliers'
            ))
        
        fig_quality.update_layout(
            title='Data Quality Score Distribution by Category',
            xaxis_title='ESG Category',
            yaxis_title='Quality Score',
            font=dict(size=12)
        )
        
        charts['quality_distribution'] = fig_quality.to_dict()
        
        return charts
    
    def create_trend_analysis(self, df: pd.DataFrame, metric_name: str) -> Dict[str, Any]:
        """Create trend analysis charts for a specific metric."""
        metric_data = df[df['metric_name'] == metric_name].copy()
        
        if metric_data.empty:
            return {'error': f'No data available for metric: {metric_name}'}
        
        # Sort by year
        metric_data = metric_data.sort_values('reporting_year')
        
        charts = {}
        
        # 1. Time Series Line Chart
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Scatter(
            x=metric_data['reporting_year'],
            y=metric_data['value'],
            mode='lines+markers',
            name=metric_name,
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y}<br>Unit: ' + 
                         metric_data['unit'].iloc[0] if 'unit' in metric_data.columns else '' + '<extra></extra>'
        ))
        
        fig_trend.update_layout(
            title=f'Trend Analysis: {metric_name}',
            xaxis_title='Year',
            yaxis_title=f"Value ({metric_data['unit'].iloc[0] if 'unit' in metric_data.columns else ''})",
            font=dict(size=12),
            hovermode='x unified'
        )
        
        charts['trend_line'] = fig_trend.to_dict()
        
        # 2. Year-over-Year Change (Bar Chart)
        if len(metric_data) > 1:
            metric_data['yoy_change'] = metric_data['value'].pct_change() * 100
            yoy_data = metric_data.dropna(subset=['yoy_change'])
            
            colors = ['red' if x < 0 else 'green' for x in yoy_data['yoy_change']]
            
            fig_yoy = go.Figure(data=[go.Bar(
                x=yoy_data['reporting_year'],
                y=yoy_data['yoy_change'],
                marker_color=colors,
                hovertemplate='<b>Year: %{x}</b><br>YoY Change: %{y:.1f}%<extra></extra>'
            )])
            
            fig_yoy.update_layout(
                title=f'Year-over-Year Change: {metric_name}',
                xaxis_title='Year',
                yaxis_title='Change (%)',
                font=dict(size=12)
            )
            
            charts['yoy_change'] = fig_yoy.to_dict()
        
        return charts
    
    def create_comparison_chart(self, df: pd.DataFrame, metrics: List[str]) -> Dict[str, Any]:
        """Create comparison chart for multiple metrics."""
        if not metrics or df.empty:
            return {'error': 'No metrics specified or no data available'}
        
        # Filter data for specified metrics
        comparison_data = df[df['metric_name'].isin(metrics)]
        
        if comparison_data.empty:
            return {'error': 'No data available for specified metrics'}
        
        # Create subplot for each metric
        fig = make_subplots(
            rows=len(metrics),
            cols=1,
            subplot_titles=metrics,
            vertical_spacing=0.1
        )
        
        for i, metric in enumerate(metrics, 1):
            metric_data = comparison_data[comparison_data['metric_name'] == metric]
            
            if not metric_data.empty:
                metric_data = metric_data.sort_values('reporting_year')
                
                fig.add_trace(
                    go.Scatter(
                        x=metric_data['reporting_year'],
                        y=metric_data['value'],
                        mode='lines+markers',
                        name=metric,
                        line=dict(width=2),
                        marker=dict(size=6)
                    ),
                    row=i, col=1
                )
        
        fig.update_layout(
            title='ESG Metrics Comparison',
            height=300 * len(metrics),
            font=dict(size=10),
            showlegend=False
        )
        
        return {'comparison_chart': fig.to_dict()}
    
    def create_subcategory_breakdown(self, df: pd.DataFrame, category: str) -> Dict[str, Any]:
        """Create breakdown charts for subcategories within an ESG category."""
        category_data = df[df['category'] == category]
        
        if category_data.empty:
            return {'error': f'No data available for category: {category}'}
        
        charts = {}
        
        # 1. Subcategory Distribution (Horizontal Bar Chart)
        subcategory_counts = category_data['subcategory'].value_counts()
        
        fig_subcats = go.Figure(data=[go.Bar(
            x=subcategory_counts.values,
            y=subcategory_counts.index,
            orientation='h',
            marker_color=self.colors.get(category, '#808080'),
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        )])
        
        fig_subcats.update_layout(
            title=f'{category} - Subcategory Breakdown',
            xaxis_title='Number of Data Points',
            yaxis_title='Subcategory',
            font=dict(size=12)
        )
        
        charts['subcategory_distribution'] = fig_subcats.to_dict()
        
        # 2. Top Metrics in Category (Top 10)
        metric_counts = category_data['metric_name'].value_counts().head(10)
        
        fig_metrics = go.Figure(data=[go.Bar(
            x=metric_counts.index,
            y=metric_counts.values,
            marker_color=self.colors.get(category, '#808080'),
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )])
        
        fig_metrics.update_layout(
            title=f'{category} - Top 10 Metrics',
            xaxis_title='Metric Name',
            yaxis_title='Number of Data Points',
            font=dict(size=12),
            xaxis_tickangle=-45
        )
        
        charts['top_metrics'] = fig_metrics.to_dict()
        
        return charts
    
    def create_performance_dashboard(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create comprehensive performance dashboard."""
        if df.empty:
            return {'error': 'No data available'}
        
        # Create subplot with different chart types
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Category Distribution', 'Data Quality by Source', 
                          'Metrics Timeline', 'Data Completeness'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 1. Category Distribution (Pie)
        category_counts = df['category'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                marker_colors=[self.colors.get(cat, '#808080') for cat in category_counts.index]
            ),
            row=1, col=1
        )
        
        # 2. Data Quality by Source (Bar)
        quality_by_source = df.groupby('data_source')['quality_score'].mean()
        fig.add_trace(
            go.Bar(
                x=quality_by_source.index,
                y=quality_by_source.values,
                name='Avg Quality Score'
            ),
            row=1, col=2
        )
        
        # 3. Metrics Timeline (Scatter)
        yearly_counts = df.groupby('reporting_year').size()
        fig.add_trace(
            go.Scatter(
                x=yearly_counts.index,
                y=yearly_counts.values,
                mode='lines+markers',
                name='Data Points per Year'
            ),
            row=2, col=1
        )
        
        # 4. Data Completeness (Bar)
        completeness = df.groupby('category').apply(
            lambda x: (x['value'].notna().sum() / len(x)) * 100
        )
        fig.add_trace(
            go.Bar(
                x=completeness.index,
                y=completeness.values,
                name='Completeness %',
                marker_color=[self.colors.get(cat, '#808080') for cat in completeness.index]
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='ESG Performance Dashboard',
            height=800,
            font=dict(size=10),
            showlegend=False
        )
        
        return {'dashboard': fig.to_dict()}
    
    def export_chart(self, chart_dict: Dict[str, Any], filename: str, format: str = 'html') -> str:
        """Export chart to file."""
        fig = go.Figure(chart_dict)
        
        if format.lower() == 'html':
            filepath = f'exports/{filename}.html'
            fig.write_html(filepath)
        elif format.lower() == 'png':
            filepath = f'exports/{filename}.png'
            fig.write_image(filepath)
        elif format.lower() == 'pdf':
            filepath = f'exports/{filename}.pdf'
            fig.write_image(filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return filepath