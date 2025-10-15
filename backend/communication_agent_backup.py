"""
Communication Agent for Investment Portfolio Management

This agent generates professional investment reports and provides explanations
for portfolio decisions, similar to bank house views. It uses IBM WatsonX LLM
to create tailored explanations and rationales for user portfolios.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from langchain_ibm import WatsonxLLM
from langgraph.graph import StateGraph, END
from langgraph.graph import CompiledGraph
import logging

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import base64

# Import our data sharing utilities
from data_sharing import get_user_profile_data, get_other_agent_results, save_my_agent_results

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommunicationAgent:
    """
    Generate a professional PDF investment report with visualizations
    
    Args:
        report_data: Dictionary containing report content and portfolio data
        output_path: Optional path for PDF output, defaults to temp file
    
    Returns:
        Path to generated PDF file
    """
    if output_path is None:
        output_path = f"investment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles for professional report
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=HexColor('#2563eb'),
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor('#1e40af')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leading=14
    )
    
    # Build story (content)
    story = []
    
    # Title Page
    story.append(Paragraph(report_data.get('report_title', 'Investment Portfolio Analysis'), title_style))
    story.append(Spacer(1, 12))
    
    # Header information
    story.append(Paragraph(f"Generated: {report_data.get('generated_date', datetime.now().strftime('%B %d, %Y'))}", body_style))
    story.append(Paragraph(f"Client Profile: {report_data.get('client_id', 'N/A')}", body_style))
    story.append(Spacer(1, 30))
    
    # Generate portfolio pie chart
    if 'portfolio_allocation' in report_data:
        chart_image = create_portfolio_pie_chart(report_data['portfolio_allocation'])
        if chart_image:
            story.append(chart_image)
            story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(report_data.get('executive_summary', ''), body_style))
    story.append(Spacer(1, 20))
    
    # Portfolio Allocation Strategy
    story.append(Paragraph("Portfolio Allocation Strategy", heading_style))
    story.append(Paragraph(report_data.get('allocation_rationale', ''), body_style))
    story.append(Spacer(1, 20))
    
    # Investment Selection Rationale
    story.append(Paragraph("Investment Selection Rationale", heading_style))
    story.append(Paragraph(report_data.get('selection_rationale', ''), body_style))
    story.append(Spacer(1, 20))
    
    # Risk Analysis
    story.append(Paragraph("Risk Analysis & Commentary", heading_style))
    story.append(Paragraph(report_data.get('risk_commentary', ''), body_style))
    story.append(Spacer(1, 20))
    
    # Key Holdings Table
    if 'individual_holdings' in report_data:
        story.append(Paragraph("Portfolio Holdings", heading_style))
        holdings_table = create_holdings_table(report_data['individual_holdings'])
        if holdings_table:
            story.append(holdings_table)
            story.append(Spacer(1, 20))
    
    # Key Recommendations
    if 'key_recommendations' in report_data:
        story.append(Paragraph("Key Recommendations", heading_style))
        for i, rec in enumerate(report_data['key_recommendations'], 1):
            story.append(Paragraph(f"{i}. {rec}", body_style))
        story.append(Spacer(1, 20))
    
    # Next Steps
    if 'next_steps' in report_data:
        story.append(Paragraph("Recommended Next Steps", heading_style))
        for i, step in enumerate(report_data['next_steps'], 1):
            story.append(Paragraph(f"{i}. {step}", body_style))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )
    story.append(Paragraph("This report is generated by AI Investment Advisory System for informational purposes only.", footer_style))
    
    # Build PDF
    doc.build(story)
    
    return output_path


def create_portfolio_pie_chart(allocation_data: Dict[str, float]) -> Image:
    """Create a professional pie chart for portfolio allocation"""
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Prepare data
        labels = list(allocation_data.keys())
        sizes = list(allocation_data.values())
        
        # Professional color palette
        colors_palette = ['#2563eb', '#059669', '#dc2626', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors_palette[:len(labels)])
        
        # Styling
        plt.setp(autotexts, size=10, weight="bold")
        plt.setp(texts, size=11)
        
        ax.set_title('Portfolio Allocation', fontsize=14, fontweight='bold', pad=20)
        
        # Save to BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()
        
        # Create ReportLab Image
        return Image(img_buffer, width=4*inch, height=3*inch)
        
    except Exception as e:
        logger.error(f"Error creating pie chart: {e}")
        return None


def create_holdings_table(holdings_data: List[Dict[str, Any]]) -> Table:
    """Create a professional holdings table"""
    try:
        # Table headers
        headers = ['Security', 'Symbol', 'Allocation %', 'Value ($)']
        
        # Prepare data
        table_data = [headers]
        for holding in holdings_data:
            row = [
                holding.get('name', 'N/A'),
                holding.get('symbol', 'N/A'),
                f"{holding.get('allocation_percent', 0):.1f}%",
                f"${holding.get('value', 0):,.0f}"
            ]
            table_data.append(row)
        
        # Create table
        table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.2*inch])
        
        # Styling
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
        
    except Exception as e:
        logger.error(f"Error creating holdings table: {e}")
        return NonebleStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import base64

# Import our data sharing utilities
from data_sharing import get_user_profile_data, get_other_agent_results, save_my_agent_results

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommunicationAgent:
    """
    Communication Agent that generates professional investment reports
    and explanations for portfolio decisions
    """
    
    def __init__(self):
        """Initialize the Communication Agent with WatsonX LLM"""
        self.setup_watsonx_llm()
        self.setup_langgraph()
    
    def setup_watsonx_llm(self):
        """Setup IBM WatsonX LLM for report generation"""
        try:
            # Use same configuration as your teammate's market sentiment agent
            self.llm = WatsonxLLM(
                model_id="ibm/granite-3-8b-instruct",
                project_id=os.getenv("WATSONX_PROJECT_ID", "9fb38a1d-5fae-47c2-a1a1-780e63b953f7"),
                apikey=os.getenv("WATSONX_API_KEY", "0VrXkis1OeScydFGNiufjJItYgNtxKW7RXbY7ODBzp7j"),
                url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
                params={
                    "decoding_method": "greedy",
                    "max_new_tokens": 800,
                    "temperature": 0.3,
                    "repetition_penalty": 1.1
                }
            )
            logger.info("WatsonX LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WatsonX LLM: {e}")
            self.llm = None
    
    def setup_langgraph(self):
        """Setup LangGraph workflow for report generation"""
        try:
            # Create workflow graph
            workflow = StateGraph(dict)
            
            # Add nodes for different report sections
            workflow.add_node("analyze_profile", self.analyze_user_profile)
            workflow.add_node("generate_executive_summary", self.generate_executive_summary)
            workflow.add_node("explain_allocation", self.explain_allocation_rationale)
            workflow.add_node("explain_selections", self.explain_selection_rationale)
            workflow.add_node("generate_risk_commentary", self.generate_risk_commentary)
            workflow.add_node("compile_report", self.compile_final_report)
            
            # Define workflow edges
            workflow.add_edge("analyze_profile", "generate_executive_summary")
            workflow.add_edge("generate_executive_summary", "explain_allocation")
            workflow.add_edge("explain_allocation", "explain_selections")
            workflow.add_edge("explain_selections", "generate_risk_commentary")
            workflow.add_edge("generate_risk_commentary", "compile_report")
            workflow.add_edge("compile_report", END)
            
            # Set entry point
            workflow.set_entry_point("analyze_profile")
            
            # Compile the graph
            self.workflow = workflow.compile()
            logger.info("LangGraph workflow initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph: {e}")
            self.workflow = None
    
    def analyze_user_profile(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user profile data to extract key characteristics"""
        try:
            profile = state.get("user_profile", {})
            
            # Extract key characteristics
            analysis = {
                "investor_type": self._determine_investor_type(profile),
                "risk_profile": profile.get("risk_tolerance", "medium"),
                "time_horizon": profile.get("time_horizon", 10),
                "primary_goals": [g.get("description", "") for g in profile.get("goals", [])[:3]],
                "esg_preferences": profile.get("personal_values", {}).get("esg_preferences", {}),
                "financial_capacity": {
                    "income": profile.get("income", 0),
                    "savings_rate": profile.get("savings_rate", 0),
                    "debt_ratio": self._calculate_debt_ratio(profile)
                }
            }
            
            state["profile_analysis"] = analysis
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing user profile: {e}")
            state["profile_analysis"] = {"error": str(e)}
            return state
    
    def generate_executive_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary using WatsonX LLM"""
        try:
            if not self.llm:
                state["executive_summary"] = "Executive summary generation unavailable - LLM not initialized"
                return state
            
            analysis = state.get("profile_analysis", {})
            portfolio_data = state.get("portfolio_data", {})
            
            prompt = f"""
            Generate a professional executive summary for an investment portfolio report, similar to bank house views.
            
            Client Profile:
            - Investor Type: {analysis.get('investor_type', 'Balanced')}
            - Risk Tolerance: {analysis.get('risk_profile', 'Medium')}
            - Investment Horizon: {analysis.get('time_horizon', 10)} years
            - Primary Goals: {', '.join(analysis.get('primary_goals', []))}
            - Annual Income: ${analysis.get('financial_capacity', {}).get('income', 0):,.0f}
            
            Portfolio Overview:
            - Total Value: ${portfolio_data.get('total_value', 500000):,.0f}
            - Expected Return: {portfolio_data.get('expected_return', 8.5):.1f}%
            - Risk Score: {portfolio_data.get('risk_score', 6.8):.1f}/10
            
            Write a 3-4 sentence executive summary that:
            1. Acknowledges the client's financial goals
            2. Summarizes the portfolio strategy
            3. Highlights key benefits and alignment with client needs
            4. Mentions risk-return profile
            
            Use professional, banking industry language. Be concise and confident.
            """
            
            response = self._generate_llm_response(prompt)
            state["executive_summary"] = response
            return state
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            state["executive_summary"] = "Executive summary generation failed"
            return state
    
    def explain_allocation_rationale(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate allocation rationale explanations"""
        try:
            if not self.llm:
                state["allocation_rationale"] = "Allocation rationale unavailable - LLM not initialized"
                return state
            
            analysis = state.get("profile_analysis", {})
            portfolio_data = state.get("portfolio_data", {})
            allocations = portfolio_data.get("allocations", [])
            
            prompt = f"""
            Explain the asset allocation strategy for this investment portfolio in professional terms.
            
            Client Context:
            - Risk Tolerance: {analysis.get('risk_profile', 'Medium')}
            - Time Horizon: {analysis.get('time_horizon', 10)} years
            - Primary Goals: {', '.join(analysis.get('primary_goals', []))}
            - ESG Preferences: {analysis.get('esg_preferences', {}).get('prefer_industries', [])}
            
            Portfolio Allocations:
            {json.dumps(allocations, indent=2) if allocations else "Standard balanced allocation"}
            
            Provide a detailed rationale explaining:
            1. Why this specific allocation mix was chosen
            2. How it aligns with the client's risk tolerance and time horizon
            3. Regional/sector preferences and diversification benefits
            4. How it addresses the client's specific goals
            
            Use professional investment advisory language. Be specific about percentages and reasoning.
            """
            
            response = self._generate_llm_response(prompt)
            state["allocation_rationale"] = response
            return state
            
        except Exception as e:
            logger.error(f"Error generating allocation rationale: {e}")
            state["allocation_rationale"] = "Allocation rationale generation failed"
            return state
    
    def explain_selection_rationale(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific investment selection explanations"""
        try:
            if not self.llm:
                state["selection_rationale"] = "Selection rationale unavailable - LLM not initialized"
                return state
            
            analysis = state.get("profile_analysis", {})
            portfolio_data = state.get("portfolio_data", {})
            selections = portfolio_data.get("selections", [])
            
            prompt = f"""
            Explain the specific investment selections in this portfolio and why they were chosen.
            
            Client Profile:
            - Investment Goals: {', '.join(analysis.get('primary_goals', []))}
            - Risk Profile: {analysis.get('risk_profile', 'Medium')}
            - ESG Preferences: {analysis.get('esg_preferences', {})}
            
            Selected Investments:
            {json.dumps(selections, indent=2) if selections else "Standard diversified selections"}
            
            For each major holding or category, explain:
            1. Why this specific investment was selected
            2. How it contributes to the overall strategy
            3. Risk-return characteristics
            4. Alignment with client preferences (ESG, regions, sectors)
            5. Role in portfolio diversification
            
            Be specific about individual selections and their strategic purpose.
            Use professional investment language with clear reasoning.
            """
            
            response = self._generate_llm_response(prompt)
            state["selection_rationale"] = response
            return state
            
        except Exception as e:
            logger.error(f"Error generating selection rationale: {e}")
            state["selection_rationale"] = "Selection rationale generation failed"
            return state
    
    def generate_risk_commentary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk analysis commentary"""
        try:
            if not self.llm:
                state["risk_commentary"] = "Risk commentary unavailable - LLM not initialized"
                return state
            
            analysis = state.get("profile_analysis", {})
            portfolio_data = state.get("portfolio_data", {})
            risk_data = state.get("risk_analysis", {})
            
            prompt = f"""
            Generate a professional risk analysis commentary for this investment portfolio.
            
            Client Risk Profile:
            - Risk Tolerance: {analysis.get('risk_profile', 'Medium')}
            - Time Horizon: {analysis.get('time_horizon', 10)} years
            - Financial Capacity: ${analysis.get('financial_capacity', {}).get('income', 0):,.0f} income
            
            Portfolio Risk Metrics:
            - Risk Score: {portfolio_data.get('risk_score', 6.8):.1f}/10
            - Expected Volatility: {portfolio_data.get('volatility', 12.3):.1f}%
            - Sharpe Ratio: {portfolio_data.get('sharpe_ratio', 1.42):.2f}
            - Risk Analysis: {json.dumps(risk_data, indent=2) if risk_data else "Standard risk profile"}
            
            Provide commentary covering:
            1. Overall risk assessment and alignment with client tolerance
            2. Key risk factors and mitigation strategies
            3. Stress testing results and downside protection
            4. Risk monitoring and rebalancing recommendations
            5. How the risk profile supports long-term goals
            
            Use professional risk management language. Be reassuring but realistic about risks.
            """
            
            response = self._generate_llm_response(prompt)
            state["risk_commentary"] = response
            return state
            
        except Exception as e:
            logger.error(f"Error generating risk commentary: {e}")
            state["risk_commentary"] = "Risk commentary generation failed"
            return state
    
    def compile_final_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all sections into final professional report"""
        try:
            report = {
                "report_title": "Investment Portfolio Analysis & Recommendations",
                "generated_date": datetime.now().strftime("%B %d, %Y"),
                "client_id": state.get("user_profile", {}).get("profile_id", "Unknown"),
                
                "executive_summary": state.get("executive_summary", ""),
                "allocation_rationale": state.get("allocation_rationale", ""),
                "selection_rationale": state.get("selection_rationale", ""),
                "risk_commentary": state.get("risk_commentary", ""),
                
                "key_recommendations": self._generate_key_recommendations(state),
                "next_steps": self._generate_next_steps(state),
                
                "report_metadata": {
                    "generated_by": "PortfolioAI Communication Agent",
                    "report_type": "House View Style Investment Report",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            state["final_report"] = report
            return state
            
        except Exception as e:
            logger.error(f"Error compiling final report: {e}")
            state["final_report"] = {"error": f"Report compilation failed: {str(e)}"}
            return state
    
    def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using WatsonX LLM with error handling"""
        try:
            if not self.llm:
                return "LLM response unavailable - service not initialized"
            
            # Generate response using same pattern as teammate's code
            response = self.llm.generate(prompts=[prompt])
            
            # Parse response based on different possible formats
            if isinstance(response, dict) and 'results' in response:
                return response['results'][0].get('generated_text', '').strip()
            elif hasattr(response, 'generations'):
                generations = response.generations
                if generations and generations[0]:
                    gen = generations[0][0]
                    return getattr(gen, 'text', '') or getattr(gen, 'generation_text', '')
            elif isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"Content generation failed: {str(e)}"
    
    def _determine_investor_type(self, profile: Dict[str, Any]) -> str:
        """Determine investor type based on profile characteristics"""
        risk_tolerance = profile.get("risk_tolerance", "medium")
        time_horizon = profile.get("time_horizon", 10)
        age = self._estimate_age_from_goals(profile.get("goals", []))
        
        if risk_tolerance == "low" or time_horizon < 5:
            return "Conservative"
        elif risk_tolerance == "high" and time_horizon > 15:
            return "Aggressive Growth"
        elif age < 35 and time_horizon > 20:
            return "Young Accumulator"
        elif age > 50 and time_horizon < 10:
            return "Pre-Retirement"
        else:
            return "Balanced Growth"
    
    def _estimate_age_from_goals(self, goals: List[Dict[str, Any]]) -> int:
        """Estimate age based on investment goals"""
        goal_types = [g.get("goal_type", "") for g in goals]
        
        if "retirement" in goal_types:
            return 45  # Retirement planning suggests mid-career
        elif "house" in goal_types:
            return 30  # Home buying suggests younger investor
        elif "education" in goal_types:
            return 40  # Education funding suggests parent age
        else:
            return 35  # Default mid-career age
    
    def _calculate_debt_ratio(self, profile: Dict[str, Any]) -> float:
        """Calculate debt-to-income ratio"""
        income = profile.get("income", 1)
        debt = profile.get("liabilities", 0)
        return (debt / income) * 100 if income > 0 else 0
    
    def _generate_key_recommendations(self, state: Dict[str, Any]) -> List[str]:
        """Generate key recommendations based on analysis"""
        recommendations = []
        analysis = state.get("profile_analysis", {})
        
        # Add recommendations based on profile analysis
        if analysis.get("debt_ratio", 0) > 30:
            recommendations.append("Consider debt reduction strategy before increasing investments")
        
        if analysis.get("time_horizon", 10) > 15:
            recommendations.append("Leverage long investment horizon with growth-oriented allocations")
        
        esg_prefs = analysis.get("esg_preferences", {})
        if esg_prefs.get("prefer_industries"):
            recommendations.append("Maintain ESG focus while ensuring adequate diversification")
        
        recommendations.append("Review and rebalance portfolio quarterly")
        recommendations.append("Monitor risk metrics and adjust as market conditions change")
        
        return recommendations
    
    def _generate_next_steps(self, state: Dict[str, Any]) -> List[str]:
        """Generate next steps for the client"""
        return [
            "Review this analysis with your financial advisor",
            "Monitor portfolio performance against benchmarks",
            "Schedule quarterly portfolio review meetings",
            "Update investment profile if circumstances change",
            "Consider tax-loss harvesting opportunities"
        ]
    
    def generate_portfolio_report(self, include_qa_system: bool = True) -> Dict[str, Any]:
        """
        Main method to generate comprehensive portfolio report
        
        Args:
            include_qa_system: Whether to include Q&A system data
            
        Returns:
            Dict containing the complete report and Q&A responses
        """
        try:
            # Gather all available data
            user_profile = get_user_profile_data()
            portfolio_data = get_other_agent_results("portfolio_construction")
            risk_analysis = get_other_agent_results("risk_analysis")
            selection_data = get_other_agent_results("selection_agent")
            
            if not user_profile:
                return {
                    "error": "No user profile data available. Please complete assessment first.",
                    "status": "failed"
                }
            
            # Prepare initial state for LangGraph
            initial_state = {
                "user_profile": user_profile,
                "portfolio_data": portfolio_data or {},
                "risk_analysis": risk_analysis or {},
                "selection_data": selection_data or {}
            }
            
            # Run LangGraph workflow if available
            if self.workflow:
                try:
                    result_state = self.workflow.invoke(initial_state)
                    report = result_state.get("final_report", {})
                except Exception as e:
                    logger.error(f"LangGraph workflow error: {e}")
                    report = self._generate_fallback_report(initial_state)
            else:
                # Fallback to simple report generation
                report = self._generate_fallback_report(initial_state)
            
            # Add Q&A system if requested
            if include_qa_system:
                qa_system = self.setup_qa_system(initial_state)
                report["qa_system"] = qa_system
            
            # Save report results
            save_my_agent_results("communication_agent", report)
            
            return {
                "status": "success",
                "report": report,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio report: {e}")
            return {
                "error": f"Report generation failed: {str(e)}",
                "status": "failed"
            }
    
    def _generate_fallback_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback report when LangGraph is unavailable"""
        user_profile = state.get("user_profile", {})
        portfolio_data = state.get("portfolio_data", {})
        
        return {
            "report_title": "Investment Portfolio Analysis & Recommendations",
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": user_profile.get("profile_id", "Unknown"),
            
            "executive_summary": self._create_simple_summary(user_profile, portfolio_data),
            "allocation_rationale": self._create_simple_allocation_explanation(user_profile, portfolio_data),
            "selection_rationale": self._create_simple_selection_explanation(user_profile, portfolio_data),
            "risk_commentary": self._create_simple_risk_commentary(user_profile, portfolio_data),
            
            "key_recommendations": [
                "Maintain diversified portfolio allocation",
                "Review portfolio performance quarterly",
                "Adjust risk exposure as goals approach",
                "Consider tax-efficient investment strategies"
            ],
            "next_steps": [
                "Monitor portfolio performance",
                "Schedule regular reviews",
                "Update profile if circumstances change"
            ],
            
            "report_metadata": {
                "generated_by": "PortfolioAI Communication Agent (Fallback Mode)",
                "report_type": "Basic Investment Report",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _create_simple_summary(self, profile: Dict, portfolio: Dict) -> str:
        """Create simple executive summary without LLM"""
        goals = [g.get("description", "") for g in profile.get("goals", [])]
        risk_level = profile.get("risk_tolerance", "medium")
        
        return f"""Based on your investment goals of {', '.join(goals[:2])}, we have constructed a {risk_level}-risk portfolio 
        designed to meet your {profile.get('time_horizon', 10)}-year investment horizon. The portfolio emphasizes diversification 
        while aligning with your risk tolerance and financial objectives. With an expected annual return of 
        {portfolio.get('expected_return', 8.5):.1f}% and a risk score of {portfolio.get('risk_score', 6.8):.1f}/10, 
        this allocation balances growth potential with prudent risk management."""
    
    def _create_simple_allocation_explanation(self, profile: Dict, portfolio: Dict) -> str:
        """Create simple allocation explanation"""
        risk_level = profile.get("risk_tolerance", "medium")
        time_horizon = profile.get("time_horizon", 10)
        
        return f"""The asset allocation is designed for a {risk_level} risk investor with a {time_horizon}-year time horizon. 
        The portfolio emphasizes equity exposure for long-term growth while maintaining fixed income positions for stability. 
        Geographic diversification across developed and emerging markets provides exposure to global growth opportunities while 
        managing regional risks. The allocation considers your ESG preferences and sector interests to ensure alignment with 
        your values while maintaining optimal diversification."""
    
    def _create_simple_selection_explanation(self, profile: Dict, portfolio: Dict) -> str:
        """Create simple selection explanation"""
        esg_prefs = profile.get("personal_values", {}).get("esg_preferences", {})
        
        explanation = """Individual investment selections focus on high-quality assets with strong fundamentals and growth potential. 
        Equity positions emphasize companies with sustainable competitive advantages and consistent earnings growth."""
        
        if esg_prefs.get("prefer_industries"):
            explanation += f" Special attention has been given to {', '.join(esg_prefs['prefer_industries'])} sectors " \
                         "in alignment with your ESG preferences."
        
        if esg_prefs.get("avoid_industries"):
            explanation += f" The portfolio avoids exposure to {', '.join(esg_prefs['avoid_industries'])} " \
                         "as requested in your investment guidelines."
        
        return explanation
    
    def _create_simple_risk_commentary(self, profile: Dict, portfolio: Dict) -> str:
        """Create simple risk commentary"""
        risk_score = portfolio.get("risk_score", 6.8)
        volatility = portfolio.get("volatility", 12.3)
        
        return f"""The portfolio maintains a risk score of {risk_score:.1f}/10, which aligns with your {profile.get('risk_tolerance', 'medium')} 
        risk tolerance. With an expected volatility of {volatility:.1f}%, the portfolio balances growth potential with downside protection. 
        Diversification across asset classes, regions, and sectors helps mitigate concentration risk while stress testing indicates 
        the portfolio can weather typical market downturns. Regular monitoring and rebalancing will ensure the risk profile 
        remains aligned with your investment objectives and changing market conditions."""
    
    def setup_qa_system(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Q&A system for portfolio questions"""
        return {
            "available": True,
            "common_questions": [
                {
                    "question": "Why was this specific allocation chosen for my portfolio?",
                    "context": "allocation_rationale",
                    "answer_type": "detailed_explanation"
                },
                {
                    "question": "How does this portfolio align with my risk tolerance?", 
                    "context": "risk_commentary",
                    "answer_type": "risk_analysis"
                },
                {
                    "question": "Why were these specific investments selected?",
                    "context": "selection_rationale", 
                    "answer_type": "selection_explanation"
                },
                {
                    "question": "What are the main risks in my portfolio?",
                    "context": "risk_commentary",
                    "answer_type": "risk_breakdown"
                },
                {
                    "question": "How often should I review my portfolio?",
                    "context": "recommendations",
                    "answer_type": "maintenance_guidance"
                }
            ],
            "state_data": state
        }
    
    def answer_portfolio_question(self, question: str, context_data: Dict[str, Any]) -> str:
        """
        Answer specific questions about the portfolio using LLM
        
        Args:
            question: User's question about the portfolio
            context_data: Relevant portfolio and user data
            
        Returns:
            Detailed answer to the question
        """
        try:
            if not self.llm:
                return "Q&A system unavailable - LLM service not initialized"
            
            prompt = f"""
            Answer this investment portfolio question in a professional, informative manner:
            
            Question: {question}
            
            Context Data:
            {json.dumps(context_data, indent=2)}
            
            Provide a clear, detailed answer that:
            1. Directly addresses the question
            2. Uses specific data from the portfolio context
            3. Explains the reasoning behind decisions
            4. Uses professional investment language
            5. Is helpful and educational
            
            Keep the answer focused and informative, similar to how a financial advisor would explain it.
            """
            
            return self._generate_llm_response(prompt)
            
        except Exception as e:
            logger.error(f"Error answering portfolio question: {e}")
            return f"Unable to generate answer: {str(e)}"


# Convenience functions for API integration
def generate_investment_report() -> Dict[str, Any]:
    """
    Quick function to generate investment report
    
    Usage:
    from communication_agent import generate_investment_report
    report = generate_investment_report()
    """
    agent = CommunicationAgent()
    return agent.generate_portfolio_report()


def answer_question(question: str) -> str:
    """
    Quick function to answer portfolio questions
    
    Usage:
    from communication_agent import answer_question
    answer = answer_question("Why was this allocation chosen?")
    """
    agent = CommunicationAgent()
    
    # Get context data
    context = {
        "user_profile": get_user_profile_data(),
        "portfolio_data": get_other_agent_results("portfolio_construction"),
        "risk_analysis": get_other_agent_results("risk_analysis")
    }
    
    return agent.answer_portfolio_question(question, context)


# Example usage and testing
if __name__ == "__main__":
    # Test the communication agent
    agent = CommunicationAgent()
    
    print("Testing Communication Agent...")
    report = agent.generate_portfolio_report()
    
    if report.get("status") == "success":
        print("✅ Report generated successfully!")
        print(f"Report title: {report['report']['report_title']}")
        print(f"Generated: {report['report']['generated_date']}")
    else:
        print(f"❌ Report generation failed: {report.get('error')}")
    
    # Test Q&A system
    print("\nTesting Q&A system...")
    answer = answer_question("Why was this specific allocation chosen for my portfolio?")
    print(f"Sample answer: {answer[:200]}...")
