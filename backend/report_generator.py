"""
Unified Investment Report Generator
Consolidates the best features from all report generation files into a single, comprehensive solution.

Features:
- Institutional-grade PDF design and presentation
- Comprehensive investment analysis and house view
- Professional styling with enhanced typography
- Portfolio projections and risk management
- ESG integration and values-based investing
- Detailed implementation roadmap and monitoring framework
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
                               Image, PageBreak, KeepTogether, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import HexColor, black, white, blue, Color
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import numpy as np

logger = logging.getLogger(__name__)

class UnifiedReportGenerator:
    """Unified report generator with the best features from all previous versions"""
    
    def __init__(self):
        """Initialize the report generator with professional styling"""
        self.colors = {
            'primary': HexColor('#0f172a'),      # Slate 900
            'secondary': HexColor('#1e293b'),     # Slate 800
            'accent': HexColor('#2563eb'),        # Blue 600
            'success': HexColor('#059669'),       # Emerald 600
            'warning': HexColor('#d97706'),       # Amber 600
            'danger': HexColor('#dc2626'),        # Red 600
            'light': HexColor('#f8fafc'),         # Slate 50
            'medium': HexColor('#e2e8f0'),        # Slate 200
            'dark': HexColor('#64748b')           # Slate 500
        }
        
        # Define comprehensive styles
        self.styles = self._create_professional_styles()
        
    def _create_professional_styles(self) -> Dict[str, ParagraphStyle]:
        """Create comprehensive paragraph styles for professional design"""
        base_styles = getSampleStyleSheet()
        
        return {
            'title': ParagraphStyle(
                'ProfessionalTitle',
                parent=base_styles['Heading1'],
                fontSize=28,
                spaceAfter=24,
                spaceBefore=0,
                textColor=self.colors['primary'],
                alignment=1,
                fontName='Helvetica-Bold',
                borderWidth=2,
                borderColor=self.colors['accent'],
                borderPadding=12
            ),
            
            'subtitle': ParagraphStyle(
                'ProfessionalSubtitle',
                parent=base_styles['Normal'],
                fontSize=16,
                spaceAfter=20,
                textColor=self.colors['secondary'],
                alignment=1,
                fontName='Helvetica',
                italic=True
            ),
            
            'section_header': ParagraphStyle(
                'ProfessionalSectionHeader',
                parent=base_styles['Heading2'],
                fontSize=18,
                spaceAfter=16,
                spaceBefore=24,
                textColor=self.colors['primary'],
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=self.colors['medium'],
                borderPadding=8,
                backColor=self.colors['light']
            ),
            
            'subsection_header': ParagraphStyle(
                'ProfessionalSubsectionHeader',
                parent=base_styles['Heading3'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=16,
                textColor=self.colors['secondary'],
                fontName='Helvetica-Bold',
                leftIndent=12
            ),
            
            'body': ParagraphStyle(
                'ProfessionalBody',
                parent=base_styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leading=16,
                fontName='Helvetica',
                textColor=self.colors['primary'],
                alignment=0
            ),
            
            'body_indented': ParagraphStyle(
                'ProfessionalBodyIndented',
                parent=base_styles['Normal'],
                fontSize=11,
                spaceAfter=10,
                leading=15,
                fontName='Helvetica',
                textColor=self.colors['primary'],
                leftIndent=20,
                bulletIndent=8
            ),
            
            'emphasis': ParagraphStyle(
                'ProfessionalEmphasis',
                parent=base_styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                leading=16,
                fontName='Helvetica-Bold',
                textColor=self.colors['accent'],
                backColor=self.colors['light'],
                borderPadding=8
            ),
            
            'key_metric': ParagraphStyle(
                'ProfessionalKeyMetric',
                parent=base_styles['Normal'],
                fontSize=14,
                spaceAfter=8,
                fontName='Helvetica-Bold',
                textColor=self.colors['success'],
                alignment=1
            ),
            
            'caption': ParagraphStyle(
                'ProfessionalCaption',
                parent=base_styles['Normal'],
                fontSize=9,
                spaceAfter=6,
                fontName='Helvetica',
                textColor=self.colors['dark'],
                alignment=1,
                italic=True
            )
        }

    def generate_comprehensive_report(self, assessment_data: Dict[str, Any], output_path: str = None) -> str:
        """
        Generate a comprehensive investment report with institutional-grade design
        
        Args:
            assessment_data: User assessment data from the frontend OR rich report data from API
            output_path: Optional path for PDF output
        
        Returns:
            Path to generated PDF file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"/tmp/investment_report_{timestamp}.pdf"
        
        # Check if this is rich API data (contains report_title, portfolio_allocation, etc.)
        if self._is_rich_api_data(assessment_data):
            report_data = self._analyze_rich_api_data(assessment_data)
        else:
            # Analyze user data and create comprehensive report structure
            report_data = self._analyze_assessment_data_comprehensive(assessment_data)
        
        # Generate PDF with professional design
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=A4,
            rightMargin=60, 
            leftMargin=60,
            topMargin=80, 
            bottomMargin=80,
            title="Investment Portfolio Strategy Report",
            author="PortfolioAI Investment Advisory",
            subject="Comprehensive Investment Analysis"
        )
        
        story = self._build_comprehensive_report_story(report_data, assessment_data)
        doc.build(story)
        
        logger.info(f"Generated comprehensive investment report: {output_path}")
        return output_path

    def _is_rich_api_data(self, data: Dict[str, Any]) -> bool:
        """Check if the data is rich API data from the report endpoint"""
        # Rich API data contains specific fields that assessment data doesn't have
        api_indicators = ['report_title', 'portfolio_allocation', 'individual_holdings', 
                         'allocation_rationale', 'selection_rationale', 'risk_commentary']
        return any(indicator in data for indicator in api_indicators)

    def _analyze_rich_api_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert rich API data to report structure format"""
        
        # Extract portfolio value from individual holdings
        individual_holdings = api_data.get('individual_holdings', [])
        total_portfolio_value = sum(holding.get('value', 0) for holding in individual_holdings)
        
        # Estimate annual contribution based on portfolio size (rough estimate)
        estimated_annual_contribution = total_portfolio_value * 0.12  # Assume 12% annual contribution rate
        
        # Calculate projections with rich data
        portfolio_projections = self._calculate_rich_portfolio_projections(
            estimated_annual_contribution, 10, total_portfolio_value
        )
        
        return {
            'report_metadata': {
                'title': api_data.get('report_title', 'Investment Portfolio Analysis Report'),
                'generated_date': api_data.get('generated_date', datetime.now().strftime('%B %d, %Y')),
                'report_version': '3.0 Unified (AI Enhanced)',
                'confidentiality': 'CONFIDENTIAL - For Client Use Only'
            },
            'executive_summary': self._create_rich_executive_summary(api_data, portfolio_projections),
            'client_profile': self._create_rich_client_profile(api_data),
            'financial_analysis': self._create_rich_financial_analysis(api_data),
            'house_view': self._create_rich_house_view(api_data),
            'market_outlook': self._generate_rich_market_outlook(api_data),
            'strategic_allocation': self._create_rich_strategic_allocation(api_data),
            'portfolio_construction': self._create_rich_portfolio_construction(api_data),
            'risk_management': self._create_rich_risk_management(api_data),
            'esg_integration': self._create_rich_esg_integration(api_data),
            'implementation_roadmap': self._create_rich_implementation_roadmap(api_data),
            'monitoring_framework': self._create_rich_monitoring_framework(api_data),
            'portfolio_projections': portfolio_projections
        }

    def _calculate_rich_portfolio_projections(self, annual_investment: float, years: int, current_value: float = 0) -> Dict[str, Any]:
        """Calculate portfolio projections using rich API data"""
        
        expected_return = 0.076  # 7.6% from the API data
        
        # Calculate year-by-year projections starting with current portfolio value
        projections = []
        cumulative_contributions = 0
        portfolio_value = current_value
        
        for year in range(1, min(years + 1, 31)):
            cumulative_contributions += annual_investment
            portfolio_value = (portfolio_value + annual_investment) * (1 + expected_return)
            
            projections.append({
                'year': year,
                'contributions': cumulative_contributions,
                'portfolio_value': portfolio_value,
                'investment_gains': portfolio_value - current_value - cumulative_contributions
            })
        
        return {
            'annual_contribution': annual_investment,
            'expected_return': expected_return,
            'time_horizon': years,
            'initial_value': current_value,
            'final_portfolio_value': portfolio_value,
            'total_contributions': cumulative_contributions,
            'total_gains': portfolio_value - current_value - cumulative_contributions,
            'yearly_projections': projections[-10:] if len(projections) > 10 else projections
        }

    def _create_rich_executive_summary(self, api_data: Dict[str, Any], projections: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary from rich API data"""
        
        return {
            'investment_objective': api_data.get('executive_summary', 
                'This comprehensive investment strategy is designed to meet long-term financial objectives through a carefully balanced portfolio approach.'),
            'key_recommendations': api_data.get('key_recommendations', [
                "Implement systematic monthly investing strategy",
                "Maintain strategic asset allocation aligned with objectives", 
                "Review portfolio performance quarterly",
                "Consider tax-loss harvesting opportunities"
            ]),
            'projected_outcomes': {
                'portfolio_value_at_horizon': projections['final_portfolio_value'],
                'total_contributions': projections['total_contributions'],
                'projected_investment_gains': projections['total_gains'],
                'annualized_return_assumption': projections['expected_return'],
                'initial_portfolio_value': projections['initial_value']
            },
            'risk_considerations': [
                "Market volatility may cause short-term fluctuations in portfolio value",
                "Inflation risk may erode purchasing power over time",
                "Interest rate risk affects bond prices and overall portfolio performance",
                "ESG screening may limit investment universe",
                "Concentration risk from individual stock holdings"
            ]
        }

    def _create_rich_client_profile(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create client profile from rich API data"""
        
        individual_holdings = api_data.get('individual_holdings', [])
        total_value = sum(holding.get('value', 0) for holding in individual_holdings)
        
        return {
            'client_id': api_data.get('client_id', 'Portfolio Client'),
            'current_portfolio_value': f"${total_value:,.0f}",
            'investment_objectives': ["Long-term wealth building", "ESG-focused investing"],
            'time_horizon': "10+ years",
            'risk_tolerance': "Moderate",
            'esg_preferences': "Strong ESG focus with sector exclusions",
            'geographic_preference': "US-focused with international diversification"
        }

    def _create_rich_financial_analysis(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create financial analysis from rich API data"""
        
        individual_holdings = api_data.get('individual_holdings', [])
        equity_value = sum(h.get('value', 0) for h in individual_holdings if 'ETF' not in h.get('symbol', ''))
        bond_value = sum(h.get('value', 0) for h in individual_holdings if any(bond in h.get('symbol', '') for bond in ['BND', 'VTEB', 'TIP']))
        total_value = sum(holding.get('value', 0) for holding in individual_holdings)
        
        return {
            'total_portfolio_value': total_value,
            'equity_allocation': (equity_value / total_value * 100) if total_value > 0 else 0,
            'bond_allocation': (bond_value / total_value * 100) if total_value > 0 else 0,
            'diversification_score': 'High' if len(individual_holdings) > 10 else 'Medium',
            'analysis_completed': True
        }

    def _create_rich_house_view(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create house view from rich API data"""
        
        return {
            'investment_stance': 'Constructive Growth Orientation',
            'central_theme': 'ESG-integrated diversified growth strategy with technology focus',
            'key_convictions': [
                'Technology leadership drives long-term outperformance',
                'ESG integration enhances risk-adjusted returns',
                'Diversification across sectors reduces concentration risk',
                'Renewable energy represents secular growth opportunity',
                'Systematic investing benefits from dollar-cost averaging'
            ],
            'strategic_positioning': 'Moderate growth approach with ESG integration and technology overweight'
        }

    def _generate_rich_market_outlook(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market outlook from rich API data"""
        
        return {
            'overall_stance': 'Constructive with selective positioning',
            'key_themes': [
                'Digital transformation continues to drive technology sector growth',
                'Renewable energy transition creating long-term investment opportunities', 
                'ESG factors becoming increasingly important for risk management',
                'Interest rate environment supports balanced equity/bond allocation'
            ],
            'sector_preferences': [
                'Technology: Overweight due to AI and cloud computing trends',
                'Renewable Energy: Positive on regulatory support and cost declines',
                'Healthcare: Defensive characteristics with growth potential',
                'Real Estate: Modest allocation for inflation protection'
            ],
            'outlook_completed': True
        }

    def _create_rich_strategic_allocation(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create strategic allocation from rich API data"""
        
        portfolio_allocation = api_data.get('portfolio_allocation', {})
        allocation_rationale = api_data.get('allocation_rationale', '')
        
        return {
            "allocation_percentages": portfolio_allocation,
            "rationale": allocation_rationale,
            "risk_profile": "moderate",
            "time_horizon": "10+ years",
            "rebalancing_frequency": "Quarterly",
            "allocation_completed": True
        }

    def _create_rich_portfolio_construction(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create portfolio construction from rich API data"""
        
        individual_holdings = api_data.get('individual_holdings', [])
        
        # Convert individual holdings to our holdings format
        holdings = []
        for holding in individual_holdings:
            # Determine asset class based on symbol/name
            name = holding.get('name', '')
            symbol = holding.get('symbol', '')
            
            if 'Bond' in name or symbol in ['BND', 'VTEB', 'TIP']:
                asset_class = 'Fixed Income'
                risk_level = 'Low'
                expected_return = 3.8
            elif 'Real Estate' in name or 'REI' in symbol:
                asset_class = 'Real Estate'
                risk_level = 'Medium'
                expected_return = 6.5
            elif 'International' in name or symbol in ['VXUS', 'VEA']:
                asset_class = 'International Equities'
                risk_level = 'Medium-High'
                expected_return = 7.8
            elif 'Energy' in name or 'Solar' in name or symbol in ['NEE', 'TSLA', 'FSLR', 'BEPC']:
                asset_class = 'Renewable Energy'
                risk_level = 'Medium-High'
                expected_return = 8.5
            else:
                asset_class = 'US Equities'
                risk_level = 'Medium-High'
                expected_return = 8.5
            
            holdings.append({
                'asset_class': asset_class,
                'instrument_type': name,
                'allocation_percent': holding.get('allocation_percent', 0),
                'expected_return': expected_return,
                'risk_level': risk_level,
                'symbol': symbol,
                'value': holding.get('value', 0)
            })
        
        selection_rationale = api_data.get('selection_rationale', 
            'Holdings selected based on quality fundamentals, ESG characteristics, and strategic sector positioning.')
        
        return {
            "holdings": holdings,
            "construction_methodology": "AI-driven portfolio construction with ESG integration",
            "selection_rationale": selection_rationale,
            "rebalancing_strategy": "Quarterly rebalancing with 5% threshold triggers",
            "tax_efficiency": "Tax-loss harvesting and asset location optimization",
            "construction_completed": True
        }

    def _create_rich_risk_management(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create risk management from rich API data"""
        
        risk_commentary = api_data.get('risk_commentary', '')
        
        return {
            "risk_framework": "Comprehensive multi-factor risk management approach",
            "risk_commentary": risk_commentary,
            "risk_metrics": {
                "expected_volatility": "Moderate (12-15% annually)",
                "maximum_drawdown": "Conservative positioning limits to -20%",
                "diversification_ratio": "High across sectors and geographies",
                "esg_risk_mitigation": "Sector exclusions reduce regulatory risks"
            },
            "risk_management_completed": True
        }

    def _create_rich_esg_integration(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ESG integration from rich API data"""
        
        return {
            "esg_approach": "Integrated ESG analysis with sector exclusions",
            "exclusions": ["Tobacco", "Weapons", "Fossil Fuels"],
            "positive_screening": ["Renewable Energy", "Sustainable Technology", "Clean Transportation"],
            "impact_measurement": "Track ESG metrics and alignment with UN SDGs",
            "esg_completed": True
        }

    def _create_rich_implementation_roadmap(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation roadmap from rich API data"""
        
        next_steps = api_data.get('next_steps', [])
        
        return {
            "implementation_steps": next_steps,
            "timeline": "6-month implementation period with quarterly reviews",
            "monitoring_frequency": "Monthly performance tracking, quarterly rebalancing",
            "implementation_completed": True
        }

    def _create_rich_monitoring_framework(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring framework from rich API data"""
        
        return {
            "performance_benchmarks": ["S&P 500 (US Equities)", "Bloomberg Aggregate (Bonds)", "Custom ESG Index"],
            "review_schedule": "Monthly performance review, Quarterly strategy assessment",
            "rebalancing_triggers": ["5% allocation drift", "Significant market events", "Strategy changes"],
            "reporting": "Quarterly comprehensive performance reports with ESG metrics",
            "monitoring_completed": True
        }

    def _analyze_assessment_data_comprehensive(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis of assessment data"""
        
        # Extract and process user information with safe defaults
        goals = assessment_data.get('goals', [])
        time_horizon = assessment_data.get('timeHorizon', 10)
        risk_tolerance = assessment_data.get('riskTolerance', 'medium')
        annual_income = assessment_data.get('annualIncome', 0)
        monthly_savings = assessment_data.get('monthlySavings', 0)
        total_debt = assessment_data.get('totalDebt', 0)
        dependents = assessment_data.get('dependents', 0)
        values = assessment_data.get('values', {})
        esg_prioritization = assessment_data.get('esgPrioritization', False)
        market_selection = assessment_data.get('marketSelection', ['US'])
        
        # Calculate comprehensive financial metrics
        annual_investment_capacity = monthly_savings * 12
        debt_to_income_ratio = (total_debt / annual_income) if annual_income > 0 else 0
        savings_rate = (monthly_savings * 12 / annual_income) if annual_income > 0 else 0
        
        # Projected portfolio values
        portfolio_projections = self._calculate_portfolio_projections(
            annual_investment_capacity, time_horizon, risk_tolerance
        )
        
        return {
            'report_metadata': {
                'title': 'Comprehensive Investment Portfolio Strategy Report',
                'generated_date': datetime.now().strftime('%B %d, %Y'),
                'report_version': '3.0 Unified',
                'confidentiality': 'CONFIDENTIAL - For Client Use Only'
            },
            'executive_summary': self._create_executive_summary(assessment_data, portfolio_projections),
            'client_profile': self._create_detailed_client_profile(assessment_data),
            'financial_analysis': self._create_financial_analysis(assessment_data),
            'house_view': self._determine_comprehensive_house_view(assessment_data),
            'market_outlook': self._generate_detailed_market_outlook(assessment_data),
            'strategic_allocation': self._create_enhanced_strategic_allocation(assessment_data),
            'portfolio_construction': self._create_portfolio_construction_details(assessment_data),
            'risk_management': self._create_comprehensive_risk_management(assessment_data),
            'esg_integration': self._create_esg_integration_analysis(assessment_data) if esg_prioritization else None,
            'implementation_roadmap': self._create_implementation_roadmap(assessment_data),
            'monitoring_framework': self._create_monitoring_framework(assessment_data),
            'portfolio_projections': portfolio_projections
        }

    def _calculate_portfolio_projections(self, annual_investment: float, years: int, risk_tolerance: str) -> Dict[str, Any]:
        """Calculate detailed portfolio projections with risk-adjusted returns"""
        
        # Expected returns based on risk tolerance (conservative estimates)
        expected_returns = {
            'conservative': 0.05,
            'moderate-conservative': 0.06,
            'moderate': 0.07,
            'moderate-aggressive': 0.08,
            'aggressive': 0.09
        }
        
        expected_return = expected_returns.get(risk_tolerance, 0.07)
        
        # Calculate year-by-year projections
        projections = []
        cumulative_contributions = 0
        portfolio_value = 0
        
        for year in range(1, min(years + 1, 31)):  # Cap at 30 years for projections
            cumulative_contributions += annual_investment
            portfolio_value = (portfolio_value + annual_investment) * (1 + expected_return)
            
            projections.append({
                'year': year,
                'contributions': cumulative_contributions,
                'portfolio_value': portfolio_value,
                'investment_gains': portfolio_value - cumulative_contributions
            })
        
        return {
            'annual_contribution': annual_investment,
            'expected_return': expected_return,
            'time_horizon': years,
            'final_portfolio_value': portfolio_value,
            'total_contributions': cumulative_contributions,
            'total_gains': portfolio_value - cumulative_contributions,
            'yearly_projections': projections[-10:] if len(projections) > 10 else projections  # Show last 10 years
        }

    def _create_executive_summary(self, assessment_data: Dict[str, Any], projections: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive executive summary"""
        
        goals = assessment_data.get('goals', [])
        primary_goal = goals[0].get('label', "Wealth Building") if goals else "Wealth Building"
        time_horizon = assessment_data.get('timeHorizon', 10)
        annual_investment = projections['annual_contribution']
        final_value = projections['final_portfolio_value']
        esg_prioritization = assessment_data.get('esgPrioritization', False)
        
        return {
            'investment_objective': (
                f"This investment strategy is designed to achieve {primary_goal.lower()} over a {time_horizon}-year "
                f"time horizon through systematic investing of ${annual_investment:,.0f} annually."
            ),
            'key_recommendations': [
                "Implement systematic dollar-cost averaging strategy with monthly contributions",
                "Maintain strategic asset allocation aligned with risk tolerance and time horizon",
                "Prioritize tax-advantaged investment accounts for optimal tax efficiency",
                "Regular portfolio rebalancing to maintain target allocations",
                "Integrate ESG considerations while maintaining return objectives" if esg_prioritization else "Focus on diversified, low-cost investment vehicles",
                "Maintain emergency fund separate from investment portfolio",
                "Review and adjust strategy annually or when circumstances change"
            ],
            'projected_outcomes': {
                'portfolio_value_at_horizon': final_value,
                'total_contributions': projections['total_contributions'],
                'projected_investment_gains': projections['total_gains'],
                'annualized_return_assumption': projections['expected_return']
            },
            'risk_considerations': [
                "Market volatility may cause short-term fluctuations in portfolio value",
                "Inflation risk may erode purchasing power over time",
                "Sequence of returns risk near retirement or goal achievement dates",
                "Interest rate risk affects bond prices and overall portfolio performance",
                "Liquidity considerations for emergency fund and near-term goals"
            ]
        }

    def _build_comprehensive_report_story(self, report_data: Dict[str, Any], assessment_data: Dict[str, Any]) -> List:
        """Build comprehensive report story with professional design"""
        
        story = []
        
        # Title Page
        story.extend(self._create_title_page(report_data))
        
        # Table of Contents
        story.append(PageBreak())
        story.extend(self._create_table_of_contents())
        
        # Executive Summary
        story.append(PageBreak())
        story.extend(self._create_executive_summary_section(report_data))
        
        # Client Profile
        story.append(PageBreak())
        story.extend(self._create_client_profile_section(report_data))
        
        # House View
        story.append(PageBreak())
        story.extend(self._create_house_view_section(report_data))
        
        # Strategic Asset Allocation
        story.append(PageBreak())
        story.extend(self._create_strategic_allocation_section(report_data))
        
        # Risk Management
        story.append(PageBreak())
        story.extend(self._create_risk_management_section(report_data))
        
        # ESG Integration (if applicable)
        if report_data.get('esg_integration') and assessment_data.get('esgPrioritization'):
            story.extend(self._create_esg_section(report_data))
        
        # Implementation Roadmap
        story.append(PageBreak())
        story.extend(self._create_implementation_section(report_data))
        
        # Portfolio Projections
        story.append(PageBreak())
        story.extend(self._create_projections_section(report_data))
        
        return story

    def _create_title_page(self, report_data: Dict[str, Any]) -> List:
        """Create professional title page"""
        story = []
        
        # Title
        story.append(Spacer(1, 60))
        story.append(Paragraph(
            report_data['report_metadata']['title'], 
            self.styles['title']
        ))
        
        # Subtitle
        story.append(Paragraph(
            "Professional Investment Advisory Report", 
            self.styles['subtitle']
        ))
        
        story.append(Spacer(1, 40))
        
        # Report details
        details = [
            f"<b>Report Date:</b> {report_data['report_metadata']['generated_date']}",
            f"<b>Report Version:</b> {report_data['report_metadata']['report_version']}",
            f"<b>Prepared By:</b> PortfolioAI Investment Advisory",
            f"<b>Classification:</b> {report_data['report_metadata']['confidentiality']}"
        ]
        
        for detail in details:
            story.append(Paragraph(detail, self.styles['body']))
        
        story.append(Spacer(1, 60))
        
        # Disclaimer
        disclaimer = (
            "<i>This report contains confidential and proprietary investment recommendations "
            "prepared specifically for the client. The analysis and recommendations contained "
            "herein are based on the client's stated investment objectives, risk tolerance, "
            "and financial circumstances as of the report date.</i>"
        )
        story.append(Paragraph(disclaimer, self.styles['caption']))
        
        return story

    def _create_table_of_contents(self) -> List:
        """Create detailed table of contents"""
        story = []
        
        story.append(Paragraph("Table of Contents", self.styles['section_header']))
        story.append(Spacer(1, 20))
        
        toc_items = [
            ("1. Executive Summary", "3"),
            ("2. Client Profile Analysis", "4"), 
            ("3. Investment House View", "5"),
            ("4. Strategic Asset Allocation", "6"),
            ("5. Risk Management Framework", "7"),
            ("6. ESG Integration Strategy", "8"),
            ("7. Implementation Roadmap", "9"),
            ("8. Portfolio Projections", "10")
        ]
        
        toc_data = []
        for item, page in toc_items:
            toc_data.append([item, page])
        
        toc_table = Table(toc_data, colWidths=[4.5*inch, 0.5*inch])
        toc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors['medium']),
        ]))
        
        story.append(toc_table)
        
        return story

    def _create_executive_summary_section(self, report_data: Dict[str, Any]) -> List:
        """Create comprehensive executive summary section"""
        story = []
        
        story.append(Paragraph("1. Executive Summary", self.styles['section_header']))
        
        exec_summary = report_data['executive_summary']
        
        # Investment Objective
        story.append(Paragraph("Investment Objective", self.styles['subsection_header']))
        story.append(Paragraph(exec_summary['investment_objective'], self.styles['body']))
        story.append(Spacer(1, 12))
        
        # Key Recommendations
        story.append(Paragraph("Key Recommendations", self.styles['subsection_header']))
        for i, rec in enumerate(exec_summary['key_recommendations'], 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles['body_indented']))
        story.append(Spacer(1, 12))
        
        # Projected Outcomes
        story.append(Paragraph("Projected Portfolio Outcomes", self.styles['subsection_header']))
        outcomes = exec_summary['projected_outcomes']
        
        outcomes_data = [
            ['Metric', 'Value'],
            ['Current Portfolio Value', f"${outcomes.get('initial_portfolio_value', 0):,.0f}"],
            ['Projected Portfolio Value (10 years)', f"${outcomes['portfolio_value_at_horizon']:,.0f}"],
            ['Total Future Contributions', f"${outcomes['total_contributions']:,.0f}"],
            ['Projected Investment Gains', f"${outcomes['projected_investment_gains']:,.0f}"],
            ['Assumed Annual Return', f"{outcomes['annualized_return_assumption']:.1%}"]
        ]
        
        outcomes_table = Table(outcomes_data, colWidths=[2.5*inch, 2*inch])
        outcomes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['medium']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['dark']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(outcomes_table)
        story.append(Spacer(1, 12))
        
        # Risk Considerations
        story.append(Paragraph("Key Risk Considerations", self.styles['subsection_header']))
        for risk in exec_summary['risk_considerations']:
            story.append(Paragraph(f"• {risk}", self.styles['body_indented']))
        
        return story

    # Placeholder methods for comprehensive sections - these contain the detailed analysis logic
    def _create_detailed_client_profile(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed client profile analysis"""
        goals = assessment_data.get('goals', [])
        time_horizon = assessment_data.get('timeHorizon', 10)
        risk_tolerance = assessment_data.get('riskTolerance', 'medium')
        annual_income = assessment_data.get('annualIncome', 0)
        monthly_savings = assessment_data.get('monthlySavings', 0)
        
        return {
            'investment_objectives': [goal.get('label', '') for goal in goals],
            'time_horizon': f"{time_horizon} years",
            'risk_tolerance': risk_tolerance.title(),
            'annual_income': f"${annual_income:,.0f}",
            'monthly_savings_capacity': f"${monthly_savings:,.0f}",
            'esg_preferences': "Yes" if assessment_data.get('esgPrioritization') else "No",
            'geographic_preference': ", ".join(assessment_data.get('marketSelection', ['US']))
        }

    def _create_financial_analysis(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive financial analysis"""
        return {"analysis_completed": True}

    def _determine_comprehensive_house_view(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine comprehensive house view based on assessment"""
        risk_tolerance = assessment_data.get('riskTolerance', 'medium')
        time_horizon = assessment_data.get('timeHorizon', 10)
        esg_prioritization = assessment_data.get('esgPrioritization', False)
        
        return {
            'investment_stance': 'Constructive Growth Orientation',
            'central_theme': 'Diversified growth strategy with risk management',
            'key_convictions': [
                'Long-term equity appreciation drives wealth creation',
                'Diversification reduces concentration risk',
                'Systematic investing smooths market volatility',
                'ESG integration enhances long-term returns' if esg_prioritization else 'Quality fundamentals outperform over time'
            ],
            'strategic_positioning': f"{risk_tolerance.title()} approach with {time_horizon}-year focus"
        }

    def _generate_detailed_market_outlook(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed market outlook"""
        return {"outlook_completed": True}

    def _create_enhanced_strategic_allocation(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced strategic asset allocation with actual data"""
        risk_tolerance = assessment_data.get('riskTolerance', 'moderate')
        time_horizon = assessment_data.get('timeHorizon', 10)
        
        # Define allocation percentages based on risk tolerance
        allocations = {
            'conservative': {
                'US Equities': 30.0,
                'International Equities': 15.0,
                'Fixed Income': 40.0,
                'Real Estate': 10.0,
                'Cash & Equivalents': 5.0
            },
            'moderate': {
                'US Equities': 45.0,
                'International Equities': 25.0,
                'Fixed Income': 20.0,
                'Real Estate': 7.0,
                'Commodities': 3.0
            },
            'moderate-aggressive': {
                'US Equities': 55.0,
                'International Equities': 30.0,
                'Fixed Income': 10.0,
                'Real Estate': 3.0,
                'Commodities': 2.0
            },
            'aggressive': {
                'US Equities': 60.0,
                'International Equities': 35.0,
                'Fixed Income': 3.0,
                'Real Estate': 1.0,
                'Commodities': 1.0
            }
        }
        
        allocation_percentages = allocations.get(risk_tolerance, allocations['moderate'])
        
        # Create allocation rationale
        rationale = f"""
        The strategic allocation is designed for a {risk_tolerance} risk profile with a {time_horizon}-year investment horizon. 
        This allocation emphasizes {'growth-oriented assets' if risk_tolerance in ['aggressive', 'moderate-aggressive'] else 'balanced diversification'} 
        while maintaining {'aggressive growth potential' if risk_tolerance == 'aggressive' else 'prudent risk management'}.
        """
        
        return {
            "allocation_percentages": allocation_percentages,
            "rationale": rationale.strip(),
            "risk_profile": risk_tolerance,
            "time_horizon": time_horizon,
            "rebalancing_frequency": "Quarterly",
            "allocation_completed": True
        }

    def _create_portfolio_construction_details(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create portfolio construction details with holdings data"""
        risk_tolerance = assessment_data.get('riskTolerance', 'moderate')
        
        # Define holdings based on the strategic allocation
        holdings_templates = {
            'conservative': [
                {'asset_class': 'US Equities', 'instrument_type': 'Large Cap Index Fund', 'allocation_percent': 30.0, 'expected_return': 7.5, 'risk_level': 'Medium'},
                {'asset_class': 'International Equities', 'instrument_type': 'Developed Markets Fund', 'allocation_percent': 15.0, 'expected_return': 7.0, 'risk_level': 'Medium'},
                {'asset_class': 'Fixed Income', 'instrument_type': 'Aggregate Bond Fund', 'allocation_percent': 40.0, 'expected_return': 3.5, 'risk_level': 'Low'},
                {'asset_class': 'Real Estate', 'instrument_type': 'REIT Index Fund', 'allocation_percent': 10.0, 'expected_return': 6.0, 'risk_level': 'Medium'},
                {'asset_class': 'Cash & Equivalents', 'instrument_type': 'Money Market Fund', 'allocation_percent': 5.0, 'expected_return': 2.5, 'risk_level': 'Low'}
            ],
            'moderate': [
                {'asset_class': 'US Equities', 'instrument_type': 'Total Stock Market Fund', 'allocation_percent': 45.0, 'expected_return': 8.5, 'risk_level': 'Medium-High'},
                {'asset_class': 'International Equities', 'instrument_type': 'Global Ex-US Fund', 'allocation_percent': 25.0, 'expected_return': 7.8, 'risk_level': 'Medium-High'},
                {'asset_class': 'Fixed Income', 'instrument_type': 'Core Bond Fund', 'allocation_percent': 20.0, 'expected_return': 3.8, 'risk_level': 'Low'},
                {'asset_class': 'Real Estate', 'instrument_type': 'Global REIT Fund', 'allocation_percent': 7.0, 'expected_return': 6.5, 'risk_level': 'Medium'},
                {'asset_class': 'Commodities', 'instrument_type': 'Commodity Index Fund', 'allocation_percent': 3.0, 'expected_return': 5.0, 'risk_level': 'High'}
            ],
            'moderate-aggressive': [
                {'asset_class': 'US Equities', 'instrument_type': 'Growth & Value Blend', 'allocation_percent': 55.0, 'expected_return': 9.0, 'risk_level': 'High'},
                {'asset_class': 'International Equities', 'instrument_type': 'Emerging Markets Blend', 'allocation_percent': 30.0, 'expected_return': 8.5, 'risk_level': 'High'},
                {'asset_class': 'Fixed Income', 'instrument_type': 'Short-Term Bond Fund', 'allocation_percent': 10.0, 'expected_return': 3.0, 'risk_level': 'Low'},
                {'asset_class': 'Real Estate', 'instrument_type': 'Global Real Estate', 'allocation_percent': 3.0, 'expected_return': 7.0, 'risk_level': 'Medium-High'},
                {'asset_class': 'Commodities', 'instrument_type': 'Natural Resources Fund', 'allocation_percent': 2.0, 'expected_return': 5.5, 'risk_level': 'High'}
            ],
            'aggressive': [
                {'asset_class': 'US Equities', 'instrument_type': 'Small-Cap Growth Fund', 'allocation_percent': 60.0, 'expected_return': 10.0, 'risk_level': 'High'},
                {'asset_class': 'International Equities', 'instrument_type': 'Emerging Markets Fund', 'allocation_percent': 35.0, 'expected_return': 9.5, 'risk_level': 'High'},
                {'asset_class': 'Fixed Income', 'instrument_type': 'Treasury Bills', 'allocation_percent': 3.0, 'expected_return': 2.5, 'risk_level': 'Low'},
                {'asset_class': 'Real Estate', 'instrument_type': 'High-Growth REIT', 'allocation_percent': 1.0, 'expected_return': 8.0, 'risk_level': 'High'},
                {'asset_class': 'Commodities', 'instrument_type': 'Precious Metals Fund', 'allocation_percent': 1.0, 'expected_return': 6.0, 'risk_level': 'High'}
            ]
        }
        
        holdings = holdings_templates.get(risk_tolerance, holdings_templates['moderate'])
        
        return {
            "holdings": holdings,
            "construction_methodology": f"Portfolio constructed using {risk_tolerance} risk allocation model",
            "rebalancing_strategy": "Quarterly rebalancing with 5% threshold triggers",
            "tax_efficiency": "Tax-loss harvesting and asset location optimization",
            "construction_completed": True
        }

    def _create_comprehensive_risk_management(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive risk management framework"""
        return {"risk_management_completed": True}

    def _create_esg_integration_analysis(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ESG integration analysis"""
        return {"esg_completed": True}

    def _create_implementation_roadmap(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation roadmap"""
        return {"implementation_completed": True}

    def _create_monitoring_framework(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring framework"""
        return {"monitoring_completed": True}

    # Placeholder section builders - these would contain the actual PDF content generation
    def _create_client_profile_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("2. Client Profile Analysis", self.styles['section_header']))
        
        client_profile = report_data.get('client_profile', {})
        
        # Client Overview
        story.append(Paragraph("Client Overview", self.styles['subsection_header']))
        story.append(Paragraph("Investment profile based on comprehensive assessment and portfolio analysis.", self.styles['body']))
        story.append(Spacer(1, 12))
        
        # Create client profile table
        profile_data = [
            ['Profile Element', 'Details'],
            ['Current Portfolio Value', client_profile.get('current_portfolio_value', 'N/A')],
            ['Investment Objectives', ', '.join(client_profile.get('investment_objectives', ['Wealth Building']))],
            ['Time Horizon', client_profile.get('time_horizon', '10+ years')],
            ['Risk Tolerance', client_profile.get('risk_tolerance', 'Moderate')],
            ['ESG Preferences', client_profile.get('esg_preferences', 'ESG Integration')],
            ['Geographic Preference', client_profile.get('geographic_preference', 'Global Diversification')]
        ]
        
        profile_table = Table(profile_data, colWidths=[2.5*inch, 3*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['medium']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['dark']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(profile_table)
        story.append(Spacer(1, 16))
        
        # Financial Analysis Summary
        financial_analysis = report_data.get('financial_analysis', {})
        if financial_analysis.get('analysis_completed'):
            story.append(Paragraph("Financial Position Analysis", self.styles['subsection_header']))
            
            total_value = financial_analysis.get('total_portfolio_value', 0)
            equity_pct = financial_analysis.get('equity_allocation', 0)
            bond_pct = financial_analysis.get('bond_allocation', 0)
            diversification = financial_analysis.get('diversification_score', 'Medium')
            
            story.append(Paragraph(f"Current portfolio value of <b>${total_value:,.0f}</b> with <b>{equity_pct:.1f}%</b> equity allocation and <b>{bond_pct:.1f}%</b> fixed income allocation. Portfolio diversification score: <b>{diversification}</b>.", self.styles['body']))
        
        return story

    def _create_house_view_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("3. Investment House View", self.styles['section_header']))
        house_view = report_data.get('house_view', {})
        
        story.append(Paragraph("Investment Stance", self.styles['subsection_header']))
        story.append(Paragraph(house_view.get('investment_stance', 'Constructive Growth Orientation'), self.styles['emphasis']))
        
        story.append(Paragraph("Central Theme", self.styles['subsection_header']))
        story.append(Paragraph(house_view.get('central_theme', 'Diversified growth strategy'), self.styles['body']))
        
        story.append(Paragraph("Key Convictions", self.styles['subsection_header']))
        for conviction in house_view.get('key_convictions', []):
            story.append(Paragraph(f"• {conviction}", self.styles['body_indented']))
            
        return story

    def _create_strategic_allocation_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("4. Strategic Asset Allocation", self.styles['section_header']))
        
        # Add allocation rationale with enhanced content
        strategic_allocation = report_data.get('strategic_allocation', {})
        allocation_text = strategic_allocation.get('rationale', 
            'Strategic allocation framework designed to optimize risk-adjusted returns while maintaining alignment with client objectives.')
        
        if allocation_text:
            story.append(Paragraph(allocation_text, self.styles['body']))
            story.append(Spacer(1, 12))
        
        # Add risk profile and time horizon information
        risk_profile = strategic_allocation.get('risk_profile', 'moderate')
        time_horizon = strategic_allocation.get('time_horizon', '10+ years')
        
        story.append(Paragraph(f"The strategic allocation is designed for a <b>{risk_profile}</b> risk profile with a <b>{time_horizon}</b> investment horizon. This allocation emphasizes balanced diversification while maintaining prudent risk management.", self.styles['body']))
        story.append(Spacer(1, 16))
        
        # Add pie chart if allocation data is available
        allocation_percentages = strategic_allocation.get('allocation_percentages', {})
        
        if allocation_percentages:
            story.append(Paragraph("Asset Allocation Overview", self.styles['subsection_header']))
            # Create and add pie chart
            pie_chart = self.create_portfolio_pie_chart(allocation_percentages)
            if pie_chart:
                story.append(pie_chart)
                story.append(Spacer(1, 20))
        
        # Add holdings table if available
        portfolio_construction = report_data.get('portfolio_construction', {})
        holdings = portfolio_construction.get('holdings', [])
        
        if holdings:
            story.append(Paragraph("Strategic Holdings Breakdown", self.styles['subsection_header']))
            
            # Add selection rationale if available
            selection_rationale = portfolio_construction.get('selection_rationale', '')
            if selection_rationale:
                story.append(Paragraph(selection_rationale, self.styles['body']))
                story.append(Spacer(1, 12))
            
            holdings_table = self.create_enhanced_holdings_table(holdings)
            if holdings_table:
                story.append(holdings_table)
                story.append(Spacer(1, 20))
                
                # Add summary statistics
                total_allocation = sum(h.get('allocation_percent', 0) for h in holdings)
                num_holdings = len(holdings)
                story.append(Paragraph(f"<b>Portfolio Summary:</b> {num_holdings} total holdings with {total_allocation:.1f}% total allocation", self.styles['body']))
        
        return story

    def _create_risk_management_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("5. Risk Management Framework", self.styles['section_header']))
        
        risk_mgmt = report_data.get('risk_management', {})
        
        # Risk Framework Overview
        framework = risk_mgmt.get('risk_framework', 'Comprehensive multi-factor risk management approach')
        story.append(Paragraph("Risk Management Approach", self.styles['subsection_header']))
        story.append(Paragraph(framework, self.styles['body']))
        story.append(Spacer(1, 12))
        
        # Risk Commentary from API
        risk_commentary = risk_mgmt.get('risk_commentary', '')
        if risk_commentary:
            story.append(Paragraph("Portfolio Risk Analysis", self.styles['subsection_header']))
            story.append(Paragraph(risk_commentary, self.styles['body']))
            story.append(Spacer(1, 12))
        
        # Risk Metrics Table
        risk_metrics = risk_mgmt.get('risk_metrics', {})
        if risk_metrics:
            story.append(Paragraph("Key Risk Metrics", self.styles['subsection_header']))
            
            metrics_data = [
                ['Risk Measure', 'Assessment'],
                ['Expected Volatility', risk_metrics.get('expected_volatility', 'Moderate (12-15% annually)')],
                ['Maximum Drawdown', risk_metrics.get('maximum_drawdown', 'Conservative positioning')],
                ['Diversification', risk_metrics.get('diversification_ratio', 'High across sectors')],
                ['ESG Risk Mitigation', risk_metrics.get('esg_risk_mitigation', 'Sector exclusions reduce risks')]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2.5*inch, 3.5*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['medium']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, self.colors['dark']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 12))
        
        # Risk Mitigation Strategies
        story.append(Paragraph("Risk Mitigation Strategies", self.styles['subsection_header']))
        risk_strategies = [
            "Portfolio diversification across asset classes, sectors, and geographies",
            "Systematic rebalancing to maintain target allocations",
            "ESG screening to reduce regulatory and reputational risks",
            "Quality-focused security selection to minimize individual company risk",
            "Regular monitoring and stress testing of portfolio positions"
        ]
        
        for strategy in risk_strategies:
            story.append(Paragraph(f"• {strategy}", self.styles['body_indented']))
        
        return story

    def _create_esg_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("ESG Integration Strategy", self.styles['subsection_header']))
        story.append(Paragraph("Environmental, Social, and Governance integration approach.", self.styles['body']))
        return story

    def _create_implementation_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("6. Implementation Roadmap", self.styles['section_header']))
        
        implementation = report_data.get('implementation_roadmap', {})
        
        # Implementation Overview
        timeline = implementation.get('timeline', '6-month implementation period with quarterly reviews')
        story.append(Paragraph("Implementation Overview", self.styles['subsection_header']))
        story.append(Paragraph(f"Portfolio implementation will follow a structured approach with the following timeline: <b>{timeline}</b>", self.styles['body']))
        story.append(Spacer(1, 12))
        
        # Implementation Steps
        implementation_steps = implementation.get('implementation_steps', [])
        if implementation_steps:
            story.append(Paragraph("Next Steps", self.styles['subsection_header']))
            for i, step in enumerate(implementation_steps, 1):
                story.append(Paragraph(f"{i}. {step}", self.styles['body_indented']))
            story.append(Spacer(1, 12))
        
        # Monitoring Framework
        monitoring = report_data.get('monitoring_framework', {})
        if monitoring.get('monitoring_completed'):
            story.append(Paragraph("Monitoring and Review Schedule", self.styles['subsection_header']))
            
            review_schedule = monitoring.get('review_schedule', 'Monthly performance review, Quarterly strategy assessment')
            story.append(Paragraph(f"<b>Review Frequency:</b> {review_schedule}", self.styles['body']))
            story.append(Spacer(1, 8))
            
            benchmarks = monitoring.get('performance_benchmarks', [])
            if benchmarks:
                story.append(Paragraph(f"<b>Performance Benchmarks:</b> {', '.join(benchmarks)}", self.styles['body']))
                story.append(Spacer(1, 8))
            
            triggers = monitoring.get('rebalancing_triggers', [])
            if triggers:
                story.append(Paragraph(f"<b>Rebalancing Triggers:</b> {', '.join(triggers)}", self.styles['body']))
                story.append(Spacer(1, 8))
            
            reporting = monitoring.get('reporting', '')
            if reporting:
                story.append(Paragraph(f"<b>Performance Reporting:</b> {reporting}", self.styles['body']))
        
        return story

    def _create_projections_section(self, report_data: Dict[str, Any]) -> List:
        story = []
        story.append(Paragraph("7. Portfolio Projections", self.styles['section_header']))
        
        projections = report_data.get('portfolio_projections', {})
        
        story.append(Paragraph("Portfolio Growth Projections", self.styles['subsection_header']))
        story.append(Paragraph(f"Based on annual contributions of ${projections.get('annual_contribution', 0):,.0f} "
                              f"and expected return of {projections.get('expected_return', 0.07):.1%}.", self.styles['body']))
        
        # Create projections table
        yearly_projections = projections.get('yearly_projections', [])
        if yearly_projections:
            proj_data = [['Year', 'Contributions', 'Portfolio Value', 'Investment Gains']]
            for proj in yearly_projections[-5:]:  # Show last 5 years
                proj_data.append([
                    str(proj['year']),
                    f"${proj['contributions']:,.0f}",
                    f"${proj['portfolio_value']:,.0f}",
                    f"${proj['investment_gains']:,.0f}"
                ])
            
            proj_table = Table(proj_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            proj_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['medium']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.colors['dark']),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            story.append(proj_table)
            story.append(Spacer(1, 20))
            
            # Add performance projection chart
            story.append(Paragraph("Portfolio Growth Visualization", self.styles['subsection_header']))
            performance_chart = self.create_performance_chart(yearly_projections)
            if performance_chart:
                story.append(performance_chart)
                story.append(Spacer(1, 20))
        
        return story
    
    def create_portfolio_pie_chart(self, allocation_data: Dict[str, float]) -> Optional[Image]:
        """
        Create a professional pie chart for portfolio allocation using matplotlib
        Enhanced version with better styling and professional appearance
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Prepare data
            labels = list(allocation_data.keys())
            sizes = list(allocation_data.values())
            
            # Professional color palette aligned with report theme
            colors_palette = ['#2563eb', '#059669', '#dc2626', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
            
            # Create enhanced pie chart with professional styling
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels, 
                autopct='%1.1f%%',
                startangle=90, 
                colors=colors_palette[:len(labels)],
                wedgeprops=dict(width=0.8, edgecolor='white', linewidth=2),
                textprops={'fontsize': 11, 'fontweight': 'bold'}
            )
            
            # Enhanced styling for professional appearance
            plt.setp(autotexts, size=10, weight="bold", color='white')
            plt.setp(texts, size=11, weight="bold")
            
            ax.set_title('Strategic Asset Allocation', fontsize=16, fontweight='bold', pad=30)
            
            # Add legend for better readability
            ax.legend(wedges, labels, title="Asset Classes", loc="center left", 
                     bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
            
            # Save to BytesIO with high quality
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=200, 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image with appropriate sizing
            return Image(img_buffer, width=5*inch, height=4*inch)
            
        except Exception as e:
            logger.error(f"Error creating portfolio pie chart: {e}")
            return None
    
    def create_enhanced_holdings_table(self, holdings_data: List[Dict[str, Any]]) -> Optional[Table]:
        """
        Create an enhanced professional holdings table with improved styling
        """
        try:
            # Enhanced table headers
            headers = ['Asset Class', 'Instrument Type', 'Allocation %', 'Expected Return', 'Risk Level']
            
            # Prepare data with enhanced formatting
            table_data = [headers]
            for holding in holdings_data:
                row = [
                    holding.get('asset_class', 'N/A'),
                    holding.get('instrument_type', 'N/A'),
                    f"{holding.get('allocation_percent', 0):.1f}%",
                    f"{holding.get('expected_return', 0):.1f}%",
                    holding.get('risk_level', 'Medium')
                ]
                table_data.append(row)
            
            # Create table with optimized column widths
            col_widths = [1.8*inch, 1.5*inch, 1*inch, 1.2*inch, 1*inch]
            table = Table(table_data, colWidths=col_widths)
            
            # Professional styling with enhanced appearance
            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['accent']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Body styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8f9fa')]),
                
                # Grid and borders
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
                ('LINEABOVE', (0, 1), (-1, 1), 2, self.colors['accent']),
                ('LINEBELOW', (0, -1), (-1, -1), 2, self.colors['accent']),
                
                # Padding for better readability
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Error creating enhanced holdings table: {e}")
            return None
    
    def create_performance_chart(self, projection_data: List[Dict[str, Any]]) -> Optional[Image]:
        """
        Create a performance projection chart showing portfolio growth over time
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract data for plotting
            years = [proj['year'] for proj in projection_data]
            portfolio_values = [proj['portfolio_value'] for proj in projection_data]
            contributions = [proj['contributions'] for proj in projection_data]
            
            # Create area chart for better visualization
            ax.fill_between(years, portfolio_values, alpha=0.3, color='#2563eb', label='Total Portfolio Value')
            ax.plot(years, portfolio_values, color='#2563eb', linewidth=3, marker='o', markersize=6)
            ax.plot(years, contributions, color='#059669', linewidth=2, linestyle='--', 
                   marker='s', markersize=4, label='Cumulative Contributions')
            
            # Styling
            ax.set_title('Portfolio Growth Projection', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Years', fontsize=12, fontweight='bold')
            ax.set_ylabel('Portfolio Value ($)', fontsize=12, fontweight='bold')
            
            # Format y-axis as currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Grid and legend
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=10)
            
            # Save to BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=200, 
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=6*inch, height=3.5*inch)
            
        except Exception as e:
            logger.error(f"Error creating performance chart: {e}")
            return None


# Convenience function for backward compatibility
def generate_pdf_report(assessment_data: Dict[str, Any], output_path: str = None) -> str:
    """
    Convenience function to generate a PDF report
    Maintains backward compatibility with existing code
    """
    generator = UnifiedReportGenerator()
    return generator.generate_comprehensive_report(assessment_data, output_path)


# Main class alias for backward compatibility
ReportGenerator = UnifiedReportGenerator
EnhancedReportGenerator = UnifiedReportGenerator
SuperiorReportGenerator = UnifiedReportGenerator