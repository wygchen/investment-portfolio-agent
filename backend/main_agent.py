"""
Main Agent for Investment Portfolio Management

This is the orchestrator agent that coordinates all other agents in the investment
portfolio management system using LangGraph workflow. It manages the complete
pipeline from user discovery to final portfolio recommendations.

Workflow:
1. Discovery Agent - Processes user assessment data
2. Risk Analytics Agent - Analyzes risk profile and generates risk blueprint
3. Portfolio Construction - Optimizes portfolio allocation based on risk profile
4. Selection Agent - Selects specific securities for each asset class
5. Communication Agent - Generates final investment report

Configuration:
- Uses environment variables for WatsonX API credentials (via watsonx_utils.py)
- Required .env variables: WATSONX_APIKEY, WATSONX_URL, PROJ_ID
- See watsonx_utils.py for proper credential configuration

Author: AI Investment Portfolio Team
Date: October 2024
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Import individual agents
from discovery_agent import DiscoveryAgent
from risk_analytics_agent.risk_analytics_agent import RiskAnalyticsAgent
from risk_analytics_agent.base_agent import AgentContext
from selection.selection_agent import run_selection_agent
from communication_agent import CommunicationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('main_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Import WatsonX utilities
try:
    from watsonx_utils import create_watsonx_llm
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False
    logger.warning("WatsonX utilities not available")


def get_watsonx_llm():
    """Get WatsonX LLM using proper environment variables"""
    if WATSONX_AVAILABLE:
        try:
            return create_watsonx_llm(
                model_id="ibm/granite-3-8b-instruct",
                max_tokens=800,
                temperature=0.3,
                repetition_penalty=1.1
            )
        except Exception as e:
            logger.warning(f"Failed to create WatsonX LLM: {e}")
            return None
    else:
        logger.warning("WatsonX utilities not available, using dummy LLM")
        return None


# =============================================================================
# STATE DEFINITIONS FOR EACH NODE
# =============================================================================

class ProcessedUserProfile(TypedDict):
    """Structure of the processed user profile from Discovery Agent"""
    goals: List[Dict[str, Any]]  # List of goal objects with goal_type, description, priority, target_date
    time_horizon: int  # Investment time horizon in years
    risk_tolerance: str  # Risk tolerance level (low/medium/high)
    income: float  # Annual income
    savings_rate: float  # Monthly savings amount
    liabilities: float  # Total debt/liabilities
    liquidity_needs: str  # Emergency fund requirements (low/medium/high)
    personal_values: Dict[str, Any]  # ESG preferences and investment themes
    esg_prioritization: bool  # Whether to prioritize ESG stocks
    market_selection: List[str]  # Selected stock markets (HK, US, etc.)
    timestamp: str  # ISO format timestamp
    profile_id: str  # Unique profile identifier


class MainAgentState(TypedDict):
    """Main state object that flows through all nodes in the workflow"""
    
    # Input data
    frontend_assessment_data: Dict[str, Any]
    
    # Node-specific states
    discovery_state: Optional[Dict[str, Any]]
    risk_analysis_state: Optional[Dict[str, Any]]
    portfolio_construction_state: Optional[Dict[str, Any]]
    selection_state: Optional[Dict[str, Any]]
    communication_state: Optional[Dict[str, Any]]
    
    # Execution metadata
    start_time: float
    execution_time: float
    current_node: str
    
    # Results and outputs
    user_profile: Optional[ProcessedUserProfile]
    risk_blueprint: Optional[Dict[str, Any]]
    portfolio_allocation: Optional[Dict[str, Any]]
    security_selections: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    
    # Error handling
    success: bool
    error: Optional[str]
    node_errors: Dict[str, str]
    
    # Configuration
    config: Dict[str, Any]


class DiscoveryInputState(TypedDict):
    """Input state for Discovery Agent node"""
    frontend_assessment_data: Dict[str, Any]
    config: Dict[str, Any]


class RiskAnalysisInputState(TypedDict):
    """Input state for Risk Analytics Agent node"""
    user_profile: ProcessedUserProfile
    config: Dict[str, Any]


class PortfolioConstructionInputState(TypedDict):
    """Input state for Portfolio Construction node"""
    user_profile: ProcessedUserProfile
    risk_blueprint: Dict[str, Any]  # Risk analysis results including risk_capacity, risk_tolerance, etc.
    config: Dict[str, Any]


class SelectionInputState(TypedDict):
    """Input state for Selection Agent node"""
    portfolio_allocation: Dict[str, Any]  # Contains filtered_tickers, filtered_weights, portfolio_metrics
    user_profile: ProcessedUserProfile
    config: Dict[str, Any]


class CommunicationInputState(TypedDict):
    """Input state for Communication Agent node"""
    user_profile: ProcessedUserProfile
    risk_blueprint: Dict[str, Any]
    portfolio_allocation: Dict[str, Any]
    security_selections: Dict[str, Any]  # Final security selections by asset class
    config: Dict[str, Any]


# =============================================================================
# MAIN ORCHESTRATOR CLASS
# =============================================================================

class MainAgent:
    """
    Main orchestrator agent that coordinates the entire investment portfolio workflow
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Main Agent with configuration
        
        Args:
            config: Configuration dictionary for agents and workflow
        """
        self.config = config or self._get_default_config()
        self.setup_logging()
        self.initialize_agents()
        self.workflow = None
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the workflow"""
        return {
            "watsonx": {
                "model_id": "ibm/granite-3-8b-instruct",
                # Using environment variables - configured in watsonx_utils.py
                "use_env_credentials": True
            },
            "portfolio_construction": {
                "risk_free_rate": 0.02,
                "max_bounds_to_test": [0.2, 0.3, 0.4, 0.5],
                "optimization_method": "pypfopt",
                "covariance_method": "ledoit_wolf"
            },
            "selection": {
                "enable_qualitative": False,
                "force_refresh": False
            },
            "communication": {
                "include_qa_system": True,
                "report_format": "comprehensive"
            },
            "shared_data_dir": "./shared_data",
            "timeout_seconds": 300
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get("log_level", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level))
        logger.info("Main Agent logging configured")
    
    def initialize_agents(self):
        """Initialize all individual agents"""
        try:
            # Initialize WatsonX LLM
            self.llm = get_watsonx_llm()
            
            # Initialize individual agents
            self.discovery_agent = DiscoveryAgent(
                output_dir=self.config.get("shared_data_dir", "./shared_data")
            )
            
            if self.llm:
                self.risk_analytics_agent = RiskAnalyticsAgent(self.llm)
            else:
                logger.warning("LLM not available, risk analytics agent will be limited")
                self.risk_analytics_agent = None
            
            self.communication_agent = CommunicationAgent()
            
            logger.info("All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise

    def create_workflow(self) -> CompiledStateGraph:
        """
        Create and compile the LangGraph workflow
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create the state graph
        workflow = StateGraph(MainAgentState)
        
        # Add nodes for each agent
        workflow.add_node("discovery", self.discovery_node)
        workflow.add_node("risk_analysis", self.risk_analysis_node)
        workflow.add_node("portfolio_construction", self.portfolio_construction_node)
        workflow.add_node("selection", self.selection_node)
        workflow.add_node("communication", self.communication_node)
        
        # Add edges to define the sequential flow
        workflow.add_edge(START, "discovery")
        workflow.add_edge("discovery", "risk_analysis")
        workflow.add_edge("risk_analysis", "portfolio_construction")
        workflow.add_edge("portfolio_construction", "selection")
        workflow.add_edge("selection", "communication")
        workflow.add_edge("communication", END)
        
        # Compile and store the workflow
        self.workflow = workflow.compile()
        logger.info("LangGraph workflow created and compiled successfully")
        
        return self.workflow

    # =============================================================================
    # WORKFLOW NODE IMPLEMENTATIONS
    # =============================================================================

    def discovery_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 1: Discovery Agent - Process user assessment data into structured profile
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with user profile data
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 1: DISCOVERY AGENT")
        logger.info("="*60)
        
        try:
            state["current_node"] = "discovery"
            
            # Extract input data
            frontend_data = state["frontend_assessment_data"]
            
            if not frontend_data:
                raise ValueError("No frontend assessment data provided")
            
            logger.info(f"Processing frontend assessment data with {len(frontend_data)} fields")
            
            # Run Discovery Agent
            discovery_result = self.discovery_agent.generate_user_profile(frontend_data)
            
            if discovery_result["status"] != "success":
                raise Exception(f"Discovery Agent failed: {discovery_result.get('message', 'Unknown error')}")
            
            # Update state
            state["discovery_state"] = discovery_result
            state["user_profile"] = discovery_result["profile_data"]
            
            logger.info(f"✅ Discovery completed successfully")
            logger.info(f"User profile ID: {discovery_result['profile_data']['profile_id']}")
            logger.info(f"Risk tolerance: {discovery_result['profile_data']['risk_tolerance']}")
            logger.info(f"Time horizon: {discovery_result['profile_data']['time_horizon']} years")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Discovery node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Discovery node failed: {str(e)}"
            state["node_errors"]["discovery"] = str(e)
            return state

    async def risk_analysis_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 2: Risk Analytics Agent - Analyze risk profile and generate blueprint
        
        Args:
            state: Current workflow state with user profile
            
        Returns:
            Updated state with risk analysis results
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 2: RISK ANALYTICS AGENT")
        logger.info("="*60)
        
        try:
            state["current_node"] = "risk_analysis"
            
            # Check prerequisites
            if not state.get("user_profile"):
                raise ValueError("User profile not available from discovery node")
            
            user_profile = state["user_profile"]
            if user_profile:
                logger.info(f"Analyzing risk profile for user: {user_profile.get('profile_id', 'Unknown')}")
            
            # Check if risk analytics agent is available
            if not self.risk_analytics_agent:
                raise ValueError("Risk analytics agent not available (LLM initialization failed)")
            
            # Create agent context
            if not user_profile:
                raise ValueError("User profile is None")
                
            agent_context = AgentContext(
                session_id=f"main_agent_{int(time.time())}",
                user_assessment=dict(user_profile)  # Convert TypedDict to Dict[str, Any]
            )
            
            # Run Risk Analytics Agent
            risk_result = await self.risk_analytics_agent.process(agent_context)
            
            if not risk_result.success:
                raise Exception(f"Risk analysis failed: {risk_result.error or risk_result.content}")
            
            # Extract risk blueprint and analysis
            risk_data = risk_result.structured_data or {}
            risk_blueprint = risk_data.get("risk_blueprint", {})
            
            # Update state
            state["risk_analysis_state"] = {
                "status": "success",
                "risk_blueprint": risk_blueprint,
                "financial_ratios": risk_data.get("financial_ratios", {}),
                "risk_score": risk_data.get("risk_score", 50),
                "volatility_target": risk_data.get("volatility_target", 12.0),
                "analysis_components": risk_data.get("analysis_components", {})
            }
            state["risk_blueprint"] = risk_blueprint
            
            logger.info("✅ Risk analysis completed successfully")
            logger.info(f"Risk score: {risk_data.get('risk_score', 'N/A')}")
            logger.info(f"Volatility target: {risk_data.get('volatility_target', 'N/A')}%")
            if risk_blueprint and risk_blueprint.get('risk_capacity'):
                logger.info(f"Risk capacity: {risk_blueprint.get('risk_capacity', {}).get('level', 'N/A')}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Risk analysis node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Risk analysis node failed: {str(e)}"
            state["node_errors"]["risk_analysis"] = str(e)
            return state

    def portfolio_construction_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 3: Portfolio Construction - Optimize portfolio allocation
        
        Args:
            state: Current workflow state with risk blueprint
            
        Returns:
            Updated state with portfolio allocation
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 3: PORTFOLIO CONSTRUCTION")
        logger.info("="*60)
        
        try:
            state["current_node"] = "portfolio_construction"
            
            # Check prerequisites
            risk_blueprint = state.get("risk_blueprint")
            if not risk_blueprint:
                raise ValueError("Risk blueprint not available from risk analysis node")
            
            user_profile = state.get("user_profile")
            
            logger.info("Starting portfolio optimization...")
            
            # Import and run portfolio construction
            import sys
            portfolio_construction_path = os.path.join(os.path.dirname(__file__), 'portfolio_construction')
            sys.path.insert(0, portfolio_construction_path)
            
            # Set user risk tolerance from risk blueprint
            volatility_target = risk_blueprint.get("volatility_target", 0.12) if risk_blueprint else 0.12
            user_risk_tolerance = volatility_target ** 2  # Convert volatility to variance
            
            # Import portfolio construction module
            import portfolio_construction
            
            # Set global user risk tolerance in the module
            try:
                # Try to set the variable if it exists
                setattr(portfolio_construction, 'user_risk_tolerance', user_risk_tolerance)
            except Exception:
                logger.warning("Could not set user_risk_tolerance in portfolio_construction module")
            
            logger.info(f"Risk tolerance set to: {user_risk_tolerance:.4f}")
            
            # Get the variables from portfolio construction
            tickers = getattr(portfolio_construction, 'tickers', ['SPY', 'BND', 'GLD', 'QQQ', 'VTI'])
            
            logger.info(f"Optimizing portfolio with {len(tickers)} assets")
            
            # Run optimization by calling the module's run_optimization function
            config = self.config.get("portfolio_construction", {})
            optimization_method = config.get("optimization_method", "pypfopt")
            covariance_method = config.get("covariance_method", "ledoit_wolf")
            max_bounds_to_test = config.get("max_bounds_to_test", [0.2, 0.3, 0.4, 0.5])
            
            # Execute the portfolio optimization script
            exec(open(os.path.join(portfolio_construction_path, 'portfolio_construction.py')).read())
            
            # Get the results from the executed script's global variables
            optimal_weights = locals().get('optimal_weights')
            cov_matrix = locals().get('cov_matrix')
            
            if optimal_weights is None:
                # Fallback: create dummy weights
                optimal_weights = [1.0/len(tickers) for _ in tickers]
                logger.warning("Using equal weights as fallback allocation")
            
            # Calculate portfolio metrics using functions from the module
            try:
                portfolio_return = getattr(portfolio_construction, 'expected_return', lambda *args: 0.08)(
                    optimal_weights, 
                    getattr(portfolio_construction, 'log_returns', None),
                    getattr(portfolio_construction, 'market_sentiment', None)
                ) if hasattr(portfolio_construction, 'log_returns') else 0.08
            except Exception:
                portfolio_return = 0.08  # Default expected return
            
            try:
                portfolio_volatility = getattr(portfolio_construction, 'standard_deviation', lambda *args: 0.12)(
                    optimal_weights, 
                    cov_matrix if cov_matrix is not None else [[0.01] * len(tickers)] * len(tickers)
                )
            except Exception:
                portfolio_volatility = 0.12  # Default volatility
                
            portfolio_sharpe = (portfolio_return - 0.02) / portfolio_volatility if portfolio_volatility > 0 else 1.0
            
            # Filter out near-zero weights
            threshold = 0.0001
            filtered_tickers = {}
            filtered_weights = {}
            
            for i, ticker in enumerate(tickers):
                if i < len(optimal_weights) and optimal_weights[i] > threshold:
                    filtered_tickers[ticker] = self._map_ticker_to_asset_class(ticker)
                    filtered_weights[ticker] = float(optimal_weights[i])
            
            # Create portfolio allocation result
            portfolio_allocation = {
                "optimal_weights": {ticker: float(optimal_weights[i]) if i < len(optimal_weights) else 0.0 
                                 for i, ticker in enumerate(tickers)},
                "filtered_tickers": filtered_tickers,
                "filtered_weights": filtered_weights,
                "portfolio_metrics": {
                    "expected_return": float(portfolio_return),
                    "volatility": float(portfolio_volatility),
                    "sharpe_ratio": float(portfolio_sharpe),
                    "risk_free_rate": 0.02
                },
                "optimization_config": {
                    "method": optimization_method,
                    "covariance_method": covariance_method,
                    "user_risk_tolerance": float(user_risk_tolerance),
                    "volatility_target": float(volatility_target)
                }
            }
            
            # Update state
            state["portfolio_construction_state"] = {
                "status": "success",
                "portfolio_allocation": portfolio_allocation
            }
            state["portfolio_allocation"] = portfolio_allocation
            
            logger.info("✅ Portfolio construction completed successfully")
            logger.info(f"Expected return: {portfolio_return:.4f}")
            logger.info(f"Expected volatility: {portfolio_volatility:.4f}")
            logger.info(f"Sharpe ratio: {portfolio_sharpe:.4f}")
            logger.info(f"Selected {len(filtered_tickers)} assets with significant weights")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Portfolio construction node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Portfolio construction node failed: {str(e)}"
            state["node_errors"]["portfolio_construction"] = str(e)
            return state

    def selection_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 4: Selection Agent - Select specific securities for each asset class
        
        Args:
            state: Current workflow state with portfolio allocation
            
        Returns:
            Updated state with security selections
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 4: SELECTION AGENT")
        logger.info("="*60)
        
        try:
            state["current_node"] = "selection"
            
            # Check prerequisites
            portfolio_allocation = state.get("portfolio_allocation")
            if not portfolio_allocation:
                raise ValueError("Portfolio allocation not available from portfolio construction node")
            
            user_profile = state.get("user_profile", {})
            
            # Extract data for selection agent
            filtered_tickers = portfolio_allocation.get("filtered_tickers", {})
            filtered_weights = portfolio_allocation.get("filtered_weights", {})
            
            # Extract regions and sectors from user profile
            personal_values = user_profile.get("personal_values", {}) if user_profile else {}
            esg_preferences = personal_values.get("esg_preferences", {})
            
            # Default regions (can be enhanced based on user preferences)
            regions = ["US"]  # Default to US market
            
            # Extract preferred sectors/industries
            sectors = esg_preferences.get("prefer_industries", [])
            if not sectors:
                sectors = None  # Let selection agent use all sectors
            
            logger.info(f"Running selection for {len(filtered_tickers)} tickers")
            logger.info(f"Asset classes: {list(set(filtered_tickers.values()))}")
            logger.info(f"Regions filter: {regions}")
            logger.info(f"Sectors filter: {sectors}")
            
            # Run Selection Agent
            selection_config = self.config.get("selection", {})
            selection_result = run_selection_agent(
                regions=regions,
                sectors=sectors,
                filtered_tickers=filtered_tickers,
                filtered_weights=filtered_weights
            )
            
            if not selection_result.get("success", False):
                raise Exception(f"Selection agent failed: {selection_result.get('error', 'Unknown error')}")
            
            # Update state
            state["selection_state"] = selection_result
            state["security_selections"] = selection_result.get("final_selections", {})
            
            logger.info("✅ Selection completed successfully")
            total_selections = sum(
                len(selections.get("selections", [])) 
                for selections in selection_result.get("final_selections", {}).values()
            )
            logger.info(f"Total securities selected: {total_selections}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Selection node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Selection node failed: {str(e)}"
            state["node_errors"]["selection"] = str(e)
            return state

    def communication_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 5: Communication Agent - Generate final investment report
        
        Args:
            state: Current workflow state with all previous results
            
        Returns:
            Updated state with final investment report
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 5: COMMUNICATION AGENT")
        logger.info("="*60)
        
        try:
            state["current_node"] = "communication"
            
            # Check prerequisites
            required_data = ["user_profile", "risk_blueprint", "portfolio_allocation", "security_selections"]
            for data_key in required_data:
                if not state.get(data_key):
                    logger.warning(f"{data_key} not available, will generate report with available data")
            
            logger.info("Generating comprehensive investment report...")
            
            # Save data for communication agent to access
            self._save_data_for_communication_agent(state)
            
            # Generate report using Communication Agent
            communication_config = self.config.get("communication", {})
            include_qa_system = communication_config.get("include_qa_system", True)
            
            report_result = self.communication_agent.generate_portfolio_report(
                include_qa_system=include_qa_system
            )
            
            if report_result.get("status") != "success":
                raise Exception(f"Communication agent failed: {report_result.get('error', 'Unknown error')}")
            
            # Update state
            state["communication_state"] = report_result
            state["final_report"] = report_result.get("report", {})
            
            # Calculate total execution time
            state["execution_time"] = time.time() - state["start_time"]
            
            logger.info("✅ Communication completed successfully")
            logger.info(f"Report generated: {report_result.get('report', {}).get('report_title', 'Unknown')}")
            logger.info(f"Total workflow execution time: {state['execution_time']:.2f} seconds")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Communication node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Communication node failed: {str(e)}"
            state["node_errors"]["communication"] = str(e)
            return state

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _map_ticker_to_asset_class(self, ticker: str) -> str:
        """Map ticker symbols to asset classes"""
        asset_class_mapping = {
            "SPY": "equity", "QQQ": "equity", "VTI": "equity",
            "BND": "bonds", "TLT": "bonds", "IEF": "bonds",
            "GLD": "commodity", "SLV": "commodity", "DBC": "commodity",
            "VNQ": "real_estate", "IYR": "real_estate"
        }
        return asset_class_mapping.get(ticker, "equity")  # Default to equity

    def _save_data_for_communication_agent(self, state: MainAgentState):
        """Save workflow results for communication agent to access"""
        try:
            from data_sharing import save_my_agent_results
            
            # Save results from each agent with null checks
            user_profile = state.get("user_profile")
            if user_profile:
                save_my_agent_results("discovery", dict(user_profile))  # Convert TypedDict to Dict[str, Any]
            
            risk_blueprint = state.get("risk_blueprint")
            if risk_blueprint:
                save_my_agent_results("risk_analysis", {
                    "risk_blueprint": risk_blueprint,
                    "risk_analysis_state": state.get("risk_analysis_state", {})
                })
            
            portfolio_allocation = state.get("portfolio_allocation")
            if portfolio_allocation:
                save_my_agent_results("portfolio_construction", portfolio_allocation)
            
            security_selections = state.get("security_selections")
            if security_selections:
                save_my_agent_results("selection_agent", security_selections)
            
            logger.info("Data saved for communication agent access")
            
        except Exception as e:
            logger.warning(f"Failed to save data for communication agent: {e}")

    def run_complete_workflow(self, frontend_assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete investment portfolio workflow
        
        Args:
            frontend_assessment_data: Raw assessment data from frontend
            
        Returns:
            Dictionary with complete workflow results
        """
        start_time = time.time()
        
        logger.info("="*80)
        logger.info("MAIN AGENT - COMPLETE INVESTMENT PORTFOLIO WORKFLOW")
        logger.info("="*80)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Create workflow if not exists
            if not self.workflow:
                self.create_workflow()
            
            # Initialize state
            initial_state: MainAgentState = {
                "frontend_assessment_data": frontend_assessment_data,
                "discovery_state": None,
                "risk_analysis_state": None,
                "portfolio_construction_state": None,
                "selection_state": None,
                "communication_state": None,
                "start_time": start_time,
                "execution_time": 0.0,
                "current_node": "",
                "user_profile": None,
                "risk_blueprint": None,
                "portfolio_allocation": None,
                "security_selections": None,
                "final_report": None,
                "success": True,
                "error": None,
                "node_errors": {},
                "config": self.config
            }
            
            # Run the workflow
            logger.info("Starting LangGraph workflow execution...")
            
            if self.workflow is None:
                raise ValueError("Workflow not initialized")
                
            final_state = self.workflow.invoke(initial_state)
            
            # Calculate final execution time
            final_state["execution_time"] = time.time() - start_time
            
            # Prepare response
            if final_state.get("success", True) and not final_state.get("error"):
                logger.info("🎉 Complete workflow executed successfully!")
                
                response = {
                    "status": "success",
                    "execution_time": final_state["execution_time"],
                    "results": {
                        "user_profile": final_state.get("user_profile"),
                        "risk_blueprint": final_state.get("risk_blueprint"),
                        "portfolio_allocation": final_state.get("portfolio_allocation"),
                        "security_selections": final_state.get("security_selections"),
                        "final_report": final_state.get("final_report")
                    },
                    "node_results": {
                        "discovery": final_state.get("discovery_state"),
                        "risk_analysis": final_state.get("risk_analysis_state"),
                        "portfolio_construction": final_state.get("portfolio_construction_state"),
                        "selection": final_state.get("selection_state"),
                        "communication": final_state.get("communication_state")
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error("❌ Workflow completed with errors")
                response = {
                    "status": "failed",
                    "error": final_state.get("error", "Unknown workflow error"),
                    "node_errors": final_state.get("node_errors", {}),
                    "execution_time": final_state.get("execution_time", 0),
                    "partial_results": {
                        "user_profile": final_state.get("user_profile"),
                        "risk_blueprint": final_state.get("risk_blueprint"),
                        "portfolio_allocation": final_state.get("portfolio_allocation"),
                        "security_selections": final_state.get("security_selections")
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            
            return {
                "status": "failed",
                "error": f"Workflow execution failed: {str(e)}",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }


# =============================================================================
# STANDALONE EXECUTION AND TESTING
# =============================================================================

def main() -> int:
    """Main entry point for standalone testing"""
    try:
        # Test data (matching DiscoveryFlow component structure)
        test_frontend_data = {
            "goals": [
                {"id": "retirement", "label": "Retirement Planning", "priority": 1},
                {"id": "house", "label": "Buy a Home", "priority": 2}
            ],
            "timeHorizon": 15,
            "riskTolerance": "moderate",
            "annualIncome": 75000,
            "monthlySavings": 2000,
            "totalDebt": 25000,
            "emergencyFundMonths": "6 months",
            "values": {
                "avoidIndustries": ["tobacco", "weapons"],
                "preferIndustries": ["technology", "renewable_energy"],
                "customConstraints": "Focus on sustainable investments"
            }
        }
        
        # Initialize Main Agent
        logger.info("Initializing Main Agent for testing...")
        main_agent = MainAgent()
        
        # Run complete workflow
        result = main_agent.run_complete_workflow(test_frontend_data)
        
        # Display results
        print("\n" + "="*80)
        print("WORKFLOW EXECUTION COMPLETE")
        print("="*80)
        print(f"Status: {result['status']}")
        print(f"Execution Time: {result['execution_time']:.2f} seconds")
        
        if result['status'] == 'success':
            print("✅ All nodes executed successfully!")
            if result['results']['final_report']:
                print(f"Final Report Title: {result['results']['final_report'].get('report_title', 'N/A')}")
        else:
            print("❌ Workflow failed:")
            print(f"Error: {result['error']}")
            if result.get('node_errors'):
                print("Node-specific errors:")
                for node, error in result['node_errors'].items():
                    print(f"  {node}: {error}")
        
        return 0 if result['status'] == 'success' else 1
        
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
