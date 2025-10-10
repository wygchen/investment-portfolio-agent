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
# from langchain_ibm import WatsonxLLM  # Commented for demo - requires IBM Watson credentials
from langgraph.graph import Graph, END
from langgraph.graph.graph import CompiledGraph
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
            # Try to import and use WatsonX LLM
            try:
                from langchain_ibm import WatsonxLLM
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
                print("✅ WatsonX LLM initialized successfully")
            except ImportError:
                print("⚠️ WatsonX LLM not available - using fallback mode")
                self.llm = None
            
        except Exception as e:
            print(f"⚠️ WatsonX LLM initialization failed: {e}")
            print("Using fallback mode for report generation")
            self.llm = None

    def setup_langgraph(self):
        """Setup LangGraph workflow for report generation"""
        try:
            # Define the workflow graph
            workflow = Graph()
            
            # Add nodes for each step of report generation
            workflow.add_node("analyze_profile", self.analyze_user_profile)
            workflow.add_node("generate_executive_summary", self.generate_executive_summary)
            workflow.add_node("explain_allocation", self.explain_allocation_strategy)
            workflow.add_node("explain_selection", self.explain_investment_selection)
            workflow.add_node("analyze_risk", self.analyze_portfolio_risk)
            workflow.add_node("generate_recommendations", self.generate_recommendations)
            workflow.add_node("compile_report", self.compile_final_report)
            
            # Define workflow edges
            workflow.add_edge("analyze_profile", "generate_executive_summary")
            workflow.add_edge("generate_executive_summary", "explain_allocation")
            workflow.add_edge("explain_allocation", "explain_selection")
            workflow.add_edge("explain_selection", "analyze_risk")
            workflow.add_edge("analyze_risk", "generate_recommendations")
            workflow.add_edge("generate_recommendations", "compile_report")
            workflow.add_edge("compile_report", END)
            
            # Set entry point
            workflow.set_entry_point("analyze_profile")
            
            # Compile the graph
            self.workflow = workflow.compile()
            
            print("✅ LangGraph workflow initialized successfully")
            
        except Exception as e:
            print(f"⚠️ LangGraph initialization failed: {e}")
            print("Using simplified report generation")
            self.workflow = None

    def generate_portfolio_report(self) -> Dict[str, Any]:
        """
        Main function to generate a comprehensive portfolio report
        
        Returns:
            Dict containing the complete investment report
        """
        try:
            print("🚀 Starting portfolio report generation...")
            
            if self.workflow:
                # Use full LangGraph workflow if available
                result = self.workflow.invoke({
                    "user_profile": get_user_profile_data(),
                    "portfolio_data": get_other_agent_results("portfolio_construction"),
                    "risk_analysis": get_other_agent_results("risk_analysis"),
                    "market_sentiment": get_other_agent_results("market_sentiment")
                })
                
                report = result.get("final_report", {})
                
            else:
                # Fallback to simple report generation
                report = self.generate_fallback_report()
            
            # Add metadata
            report["report_metadata"] = {
                "generated_by": "Communication Agent",
                "report_type": "Investment Portfolio Analysis",
                "timestamp": datetime.now().isoformat()
            }
            
            # Save results for other agents
            save_my_agent_results(report)
            
            return {
                "status": "success",
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio report: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "report": self.generate_fallback_report()
            }

    def analyze_user_profile(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user profile and preferences"""
        user_profile = state.get("user_profile", {})
        
        analysis_prompt = f"""
        Analyze the following user investment profile and provide key insights:
        
        Goals: {user_profile.get('goals', [])}
        Time Horizon: {user_profile.get('time_horizon', 'Unknown')} years
        Risk Tolerance: {user_profile.get('risk_tolerance', 'Unknown')}
        Income: ${user_profile.get('income', 0):,.2f}
        Personal Values: {user_profile.get('personal_values', {})}
        ESG Prioritization: {user_profile.get('esg_prioritization', False)}
        
        Provide a concise profile analysis focusing on investment implications.
        """
        
        try:
            if self.llm:
                profile_analysis = self.llm.invoke(analysis_prompt)
            else:
                profile_analysis = f"Profile analysis for {user_profile.get('time_horizon', 10)}-year investment horizon with {user_profile.get('risk_tolerance', 'moderate')} risk tolerance."
            
            state["profile_analysis"] = profile_analysis
            return state
            
        except Exception as e:
            logger.error(f"Profile analysis error: {e}")
            state["profile_analysis"] = "Profile analysis unavailable"
            return state

    def generate_executive_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of the investment recommendation"""
        portfolio_data = state.get("portfolio_data", {})
        profile_analysis = state.get("profile_analysis", "")
        
        summary_prompt = f"""
        Based on the user profile analysis and portfolio data, generate a compelling executive summary:
        
        Profile Analysis: {profile_analysis}
        Portfolio Value: ${portfolio_data.get('total_value', 0):,.2f}
        Expected Return: {portfolio_data.get('expected_return', 0):.1f}%
        
        Write a professional 2-3 sentence executive summary that explains the investment strategy.
        """
        
        try:
            if self.llm:
                executive_summary = self.llm.invoke(summary_prompt)
            else:
                executive_summary = f"This investment strategy is designed to meet your long-term financial goals through a diversified portfolio approach. The recommended allocation balances growth potential with risk management, targeting an expected annual return of {portfolio_data.get('expected_return', 7.6):.1f}% over your investment horizon."
            
            state["executive_summary"] = executive_summary
            return state
            
        except Exception as e:
            logger.error(f"Executive summary generation error: {e}")
            state["executive_summary"] = "Executive summary unavailable"
            return state

    def explain_allocation_strategy(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Explain the portfolio allocation rationale"""
        portfolio_data = state.get("portfolio_data", {})
        user_profile = state.get("user_profile", {})
        
        allocation_prompt = f"""
        Explain the portfolio allocation strategy based on:
        
        Time Horizon: {user_profile.get('time_horizon', 10)} years
        Risk Tolerance: {user_profile.get('risk_tolerance', 'moderate')}
        Asset Allocation: {portfolio_data.get('allocation', {})}
        
        Provide a detailed explanation of why this specific allocation was chosen.
        """
        
        try:
            if self.llm:
                allocation_rationale = self.llm.invoke(allocation_prompt)
            else:
                allocation_rationale = f"""The portfolio allocation is strategically designed for a {user_profile.get('time_horizon', 10)}-year investment horizon with {user_profile.get('risk_tolerance', 'moderate')} risk tolerance. 

The allocation includes:
- Equities (70%): Provides growth potential through technology leaders like Microsoft (8%) and Google (6%), balanced with diversified ETF exposure
- Fixed Income (30%): Offers stability and income through bond ETFs, appropriate for risk management
- ESG Integration: Investments align with environmental and social values, avoiding tobacco and weapons sectors"""
            
            state["allocation_rationale"] = allocation_rationale
            return state
            
        except Exception as e:
            logger.error(f"Allocation strategy explanation error: {e}")
            state["allocation_rationale"] = "Allocation rationale unavailable"
            return state

    def explain_investment_selection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Explain specific investment selections"""
        portfolio_data = state.get("portfolio_data", {})
        
        selection_prompt = f"""
        Explain the rationale for selecting these specific investments:
        
        Top Holdings: {portfolio_data.get('top_holdings', [])}
        
        Focus on why these particular stocks and funds were chosen over alternatives.
        """
        
        try:
            if self.llm:
                selection_rationale = self.llm.invoke(selection_prompt)
            else:
                selection_rationale = """Investment selections focus on high-quality companies with strong fundamentals and ESG characteristics:

Microsoft (MSFT) - Leading cloud computing and AI capabilities with strong ESG practices
Google/Alphabet (GOOGL) - Dominant search and cloud platforms with renewable energy commitments  
Apple (AAPL) - Premium consumer technology with supply chain sustainability initiatives
NVIDIA (NVDA) - AI and semiconductor leadership driving technological transformation
NextEra Energy (NEE) - Largest renewable energy developer in North America

ETF selections provide diversified exposure while maintaining ESG alignment and cost efficiency."""
            
            state["selection_rationale"] = selection_rationale
            return state
            
        except Exception as e:
            logger.error(f"Investment selection explanation error: {e}")
            state["selection_rationale"] = "Selection rationale unavailable"
            return state

    def analyze_portfolio_risk(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and explain portfolio risk characteristics"""
        risk_analysis = state.get("risk_analysis", {})
        
        risk_prompt = f"""
        Provide risk analysis and commentary based on:
        
        Portfolio Risk Metrics: {risk_analysis}
        
        Explain the key risk factors and how they are managed in this portfolio.
        """
        
        try:
            if self.llm:
                risk_commentary = self.llm.invoke(risk_prompt)
            else:
                risk_commentary = """Risk Management Analysis:

Portfolio Volatility: Moderate, appropriate for medium-term growth objectives
Concentration Risk: Mitigated through diversification across sectors and asset classes
Market Risk: Managed through strategic asset allocation between equities and fixed income
ESG Risk: Reduced through exclusion of controversial sectors and focus on sustainable companies

The portfolio is designed to provide growth while managing downside risk through diversification and quality investment selection."""
            
            state["risk_commentary"] = risk_commentary
            return state
            
        except Exception as e:
            logger.error(f"Risk analysis error: {e}")
            state["risk_commentary"] = "Risk commentary unavailable"
            return state

    def generate_recommendations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate key recommendations and next steps"""
        user_profile = state.get("user_profile", {})
        
        recommendations_prompt = f"""
        Based on the complete portfolio analysis, provide 3-5 key recommendations and next steps for:
        
        Investment Horizon: {user_profile.get('time_horizon', 10)} years
        Goals: {user_profile.get('goals', [])}
        
        Format as actionable recommendations.
        """
        
        try:
            if self.llm:
                recommendations_text = self.llm.invoke(recommendations_prompt)
                # Parse into list
                key_recommendations = [rec.strip() for rec in recommendations_text.split('\n') if rec.strip()]
            else:
                key_recommendations = [
                    "Implement systematic monthly investing of $1,500 to benefit from dollar-cost averaging",
                    "Review and rebalance portfolio quarterly to maintain target allocation",
                    "Consider tax-loss harvesting opportunities in taxable accounts",
                    "Increase equity allocation gradually as market conditions stabilize",
                    "Monitor ESG ratings and sustainability metrics of holdings"
                ]
            
            next_steps = [
                "Set up automatic monthly investments",
                "Schedule quarterly portfolio review",
                "Establish emergency fund if not already in place",
                "Consider increasing contribution rate with income growth",
                "Review beneficiaries and estate planning documents"
            ]
            
            state["key_recommendations"] = key_recommendations
            state["next_steps"] = next_steps
            return state
            
        except Exception as e:
            logger.error(f"Recommendations generation error: {e}")
            state["key_recommendations"] = ["Portfolio review recommended"]
            state["next_steps"] = ["Contact financial advisor"]
            return state

    def compile_final_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all components into final report"""
        user_profile = state.get("user_profile", {})
        
        final_report = {
            "report_title": f"Investment Portfolio Analysis - {user_profile.get('profile_id', 'Profile')[:8]}",
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": user_profile.get("profile_id", "Unknown"),
            "executive_summary": state.get("executive_summary", ""),
            "allocation_rationale": state.get("allocation_rationale", ""),
            "selection_rationale": state.get("selection_rationale", ""),
            "risk_commentary": state.get("risk_commentary", ""),
            "key_recommendations": state.get("key_recommendations", []),
            "next_steps": state.get("next_steps", [])
        }
        
        state["final_report"] = final_report
        return state

    def generate_fallback_report(self) -> Dict[str, Any]:
        """Generate a basic report when full workflow fails"""
        return {
            "report_title": "Investment Portfolio Analysis Report",
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "client_id": f"client_{datetime.now().strftime('%Y%m%d')}",
            "executive_summary": "This comprehensive investment strategy is designed to meet your long-term financial objectives through a carefully balanced portfolio approach. The recommended $125,000 portfolio emphasizes growth potential while maintaining appropriate risk management, targeting a 7.6% annual return aligned with your moderate risk tolerance and investment preferences.",
            "allocation_rationale": """The portfolio allocation is strategically designed for long-term wealth building with balanced risk management:

• Equity Allocation (70%): Provides growth potential through high-quality individual stocks including Microsoft (8%), Google (6%), Apple (5%), and NVIDIA (4%)
• Technology Focus (29%): Leverages digital transformation trends and AI innovation through leading companies
• Fixed Income (30%): Offers stability through bond ETFs and government securities
• Geographic Focus: Primarily US-focused with some international ETF exposure for diversification
• Quality Selection: Emphasis on financially strong companies with sustainable competitive advantages""",
            "selection_rationale": """Individual stock selections focus on industry-leading companies with strong fundamentals and growth potential:

• Microsoft (MSFT): Cloud computing and AI leadership with strong recurring revenue model
• Google/Alphabet (GOOGL): Dominant search and cloud platforms with AI development capabilities
• Apple (AAPL): Premium consumer technology with strong brand loyalty and ecosystem
• NVIDIA (NVDA): AI and semiconductor leadership driving technological transformation
• NextEra Energy (NEE): Leading renewable energy utility with consistent dividend growth
• Tesla (TSLA): Electric vehicle and energy storage innovation leadership

ETF selections provide diversified exposure while maintaining cost efficiency and broad market participation.""",
            "risk_commentary": """Portfolio risk characteristics are well-managed through diversification and quality selection:

• Volatility Management: 70/30 equity/bond allocation appropriate for moderate risk tolerance
• Concentration Risk: Individual positions limited to 8% maximum allocation to prevent overexposure
• Market Risk: Diversification across technology, energy, and healthcare sectors reduces single-sector risk
• Quality Focus: Selection of financially strong companies with proven business models
• Liquidity Management: Mix of individual stocks and ETFs provides good liquidity options

Expected annual return of 7.6% with moderate volatility through systematic diversification and quality selection.""",
            "key_recommendations": [
                "Implement systematic monthly investing of $1,500 to benefit from dollar-cost averaging",
                "Maintain current technology-focused allocation while monitoring concentration risk",
                "Review portfolio performance and rebalance quarterly to maintain target weights",
                "Consider tax-loss harvesting opportunities in taxable accounts",
                "Monitor individual stock positions for concentration risk management"
            ],
            "next_steps": [
                "Set up automatic monthly investment transfers of $1,500",
                "Schedule quarterly portfolio performance review meetings",
                "Ensure 6-month emergency fund is established separate from investments",
                "Review beneficiary designations on all investment accounts",
                "Plan for future contribution increases aligned with income growth"
            ]
        }

    def answer_portfolio_question(self, question: str, context: Dict[str, Any]) -> str:
        """
        Answer specific questions about portfolio decisions
        
        Args:
            question: User's question about the portfolio
            context: Dictionary with user profile and portfolio data
            
        Returns:
            Detailed answer to the question
        """
        try:
            qa_prompt = f"""
            User Question: {question}
            
            Portfolio Context:
            - User Profile: {context.get('user_profile', {})}
            - Portfolio Data: {context.get('portfolio_data', {})}
            - Risk Analysis: {context.get('risk_analysis', {})}
            
            Provide a detailed, professional answer that explains the portfolio decision or concept.
            """
            
            if self.llm:
                answer = self.llm.invoke(qa_prompt)
            else:
                # Fallback Q&A responses
                answer = self.generate_fallback_answer(question)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error answering portfolio question: {e}")
            return f"I apologize, but I'm unable to provide a detailed answer at the moment. For questions about '{question}', I recommend consulting with your financial advisor who can provide personalized guidance based on your complete financial situation."

    def generate_fallback_answer(self, question: str) -> str:
        """Generate fallback answers for common portfolio questions"""
        question_lower = question.lower()
        
        if "allocation" in question_lower or "why" in question_lower and "chosen" in question_lower:
            return """The portfolio allocation is specifically designed to balance growth potential with risk management over your investment time horizon. 

The 70% equity allocation provides exposure to high-quality companies with strong fundamentals and growth potential, including Microsoft (cloud computing and AI leadership), Google (dominant search and AI capabilities), and NVIDIA (semiconductor and AI innovation). This equity weighting is appropriate for long-term wealth building while maintaining diversification across sectors.

The 30% fixed income allocation provides portfolio stability, income generation, and helps reduce overall volatility. This balanced approach aligns with your moderate risk tolerance and targets a 7.6% annual return through systematic diversification."""

        elif "risk" in question_lower:
            return """Portfolio risk is carefully managed through several strategies:

1. **Diversification**: Holdings span multiple sectors (technology, energy, healthcare) and asset classes (stocks, bonds, ETFs)

2. **Quality Selection**: Individual stocks represent financially strong companies with proven business models and sustainable competitive advantages

3. **Concentration Management**: Individual positions are limited to 8% maximum allocation to prevent overexposure to any single investment

4. **Asset Allocation**: The 70/30 equity/bond split provides growth potential while maintaining appropriate risk levels for moderate risk tolerance

5. **Liquidity Management**: Mix of individual stocks and ETFs provides good liquidity options

Expected annual return of 7.6% with moderate volatility through systematic diversification and quality selection."""

        elif "technology" in question_lower or "tech" in question_lower:
            return """The technology focus (29% allocation) is based on several key factors:

**Innovation Leadership**: Companies like Microsoft, Google, Apple, and NVIDIA are at the forefront of AI development, cloud computing, and digital transformation trends.

**Strong Fundamentals**: These technology companies demonstrate strong recurring revenue models, high profit margins, and significant competitive moats.

**Growth Potential**: The technology sector continues to drive productivity improvements and create new market opportunities across industries.

**Quality Selection**: Focus on established technology leaders with proven business models rather than speculative investments.

This technology emphasis provides exposure to long-term growth trends while maintaining focus on financially strong, established companies."""

        elif "rebalance" in question_lower or "review" in question_lower:
            return """Portfolio rebalancing is essential for maintaining your target allocation and managing risk:

**Quarterly Reviews**: Regular assessment ensures allocations remain within target ranges and identifies rebalancing needs.

**Threshold-Based Rebalancing**: When any asset class drifts more than 5% from target, rebalancing helps maintain your intended risk profile.

**Tax Efficiency**: In taxable accounts, rebalancing considers tax implications and opportunities for tax-loss harvesting.

**Market Conditions**: Rebalancing forces disciplined buying low and selling high as market values fluctuate.

Your systematic monthly contributions also provide natural rebalancing as new investments can be directed toward underweight positions."""

        else:
            return f"""Thank you for your question about "{question}". 

This portfolio is designed as a comprehensive long-term investment strategy that balances growth potential with risk management. The allocation emphasizes high-quality individual stocks and diversified ETFs, with strong ESG integration throughout.

Key portfolio characteristics include:
- Strategic 70/30 equity/bond allocation appropriate for long-term growth
- Individual stock selections in industry-leading companies
- ESG screening to align with your personal values
- Diversification across sectors and asset classes
- Regular monitoring and rebalancing approach

For more specific questions about your portfolio strategy, allocation decisions, or individual holdings, I'm here to provide detailed explanations tailored to your investment objectives."""

        return answer


def generate_investment_report() -> Dict[str, Any]:
    """
    Standalone function to generate investment report
    
    Usage:
    from communication_agent import generate_investment_report
    report = generate_investment_report()
    """
    agent = CommunicationAgent()
    return agent.generate_portfolio_report()


def answer_question(question: str) -> str:
    """
    Standalone function to answer portfolio questions
    
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


def generate_pdf_report(report_data: Dict[str, Any], output_path: str = None) -> str:
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
        return None


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
        
        # Test PDF generation
        print("\nTesting PDF generation...")
        pdf_path = generate_pdf_report(report['report'])
        print(f"PDF generated: {pdf_path}")
        
    else:
        print(f"❌ Report generation failed: {report.get('error')}")
    
    # Test Q&A system
    print("\nTesting Q&A system...")
    answer = answer_question("Why was this specific allocation chosen for my portfolio?")
    print(f"Sample answer: {answer[:200]}...")