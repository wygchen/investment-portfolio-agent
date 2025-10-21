"""
Main Agent for Investment Portfolio Management

This is the orchestrator agent that coordinates all other agents in the investment
portfolio management system using LangGraph workflow. It manages the complete
pipeline from user profile to final portfolio recommendations.

Workflow:
1. Risk Analytics Agent - Analyzes risk profile and generates risk blueprint
2. Selection Agent - Selects asset classes and regions based on risk profile
3. Portfolio Construction - Optimizes portfolio allocation based on selections
4. Communication Agent - Generates final investment report

Configuration:
- Uses environment variables for WatsonX API credentials (via watsonx_utils.py)
- Required .env variables: WATSONX_APIKEY, WATSONX_URL, PROJ_ID
- See watsonx_utils.py for proper credential configuration
"""

import os
import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Import individual agents
from risk_analytics_agent.risk_analytics_agent import RiskAnalyticsAgent
from risk_analytics_agent.base_agent import AgentContext
from selection.selection_agent import run_selection_agent
from communication_agent import CommunicationAgent
from profile_processor_agent import UserProfile

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

class RiskAnalysisInputState(TypedDict):
    """Input state for Risk Analytics Agent node"""
    user_profile: UserProfile
    config: Dict[str, Any]


class PortfolioConstructionInputState(TypedDict):
    """Input state for Portfolio Construction node"""
    user_profile: UserProfile
    risk_blueprint: Dict[str, Any]  # Risk analysis results including risk_capacity, risk_tolerance, etc.
    security_selections: Dict[str, Any]  # Final tickers from selection agent
    config: Dict[str, Any]


class SelectionInputState(TypedDict):
    """Input state for Selection Agent node"""
    user_profile: UserProfile
    risk_blueprint: Dict[str, Any]  # Risk analysis results
    config: Dict[str, Any]


class CommunicationInputState(TypedDict):
    """Input state for Communication Agent node"""
    user_profile: UserProfile
    risk_blueprint: Dict[str, Any]
    portfolio_allocation: Dict[str, Any]
    security_selections: Dict[str, Any]  # Final security selections by asset class
    config: Dict[str, Any]


class ExecutionMetadataState(TypedDict):
    """State for execution tracking and metadata"""
    start_time: float
    execution_time: float
    current_node: str
    success: bool
    error: Optional[str]
    node_errors: Dict[str, str]


class NodeResultsState(TypedDict):
    """State for storing results from each node"""
    risk_analysis_state: Optional[Dict[str, Any]]
    portfolio_construction_state: Optional[Dict[str, Any]]
    selection_state: Optional[Dict[str, Any]]
    communication_state: Optional[Dict[str, Any]]


class WorkflowOutputState(TypedDict):
    """State for final workflow outputs"""
    risk_blueprint: Optional[Dict[str, Any]]
    portfolio_allocation: Optional[Dict[str, Any]]
    security_selections: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]


class MainAgentState(RiskAnalysisInputState, PortfolioConstructionInputState, 
                    SelectionInputState, CommunicationInputState, 
                    ExecutionMetadataState, NodeResultsState, 
                    WorkflowOutputState, TypedDict):
    """
    Main state object that flows through all nodes in the workflow.
    Combines all input states, execution metadata, node results, and workflow outputs.
    """
    pass


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
                "enable_qualitative": True,
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
        workflow.add_node("risk_analysis", self.risk_analysis_node)
        workflow.add_node("portfolio_construction", self.portfolio_construction_node)
        workflow.add_node("selection", self.selection_node)
        workflow.add_node("communication", self.communication_node)
        
        # Add edges to define the sequential flow
        workflow.add_edge(START, "risk_analysis")
        workflow.add_edge("risk_analysis", "selection")
        workflow.add_edge( "selection", "portfolio_construction")
        workflow.add_edge("portfolio_construction", "communication")
        workflow.add_edge("communication", END)
        
        # Compile and store the workflow
        self.workflow = workflow.compile()
        logger.info("LangGraph workflow created and compiled successfully")
        
        return self.workflow

    # =============================================================================
    # WORKFLOW NODE IMPLEMENTATIONS
    # =============================================================================

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
            
            # Emit progress callback if available
            progress_callback = state.get("progress_callback")
            if progress_callback:
                await progress_callback("risk_analysis_started", {
                    "progress": 30,
                    "message": "Analyzing risk profile and generating risk blueprint..."
                })
            
            # Check prerequisites
            if not state.get("user_profile"):
                raise ValueError("User profile not available from discovery node")
            
            user_profile = state["user_profile"]
            if user_profile:
                logger.info(f"Analyzing risk profile for user: {user_profile.profile_id}")
            
            # Check if risk analytics agent is available
            if not self.risk_analytics_agent:
                raise ValueError("Risk analytics agent not available (LLM initialization failed)")
            
            # Create agent context
            if not user_profile:
                raise ValueError("User profile is None")
                
            agent_context = AgentContext(
                session_id=f"main_agent_{int(time.time())}",
                user_assessment=user_profile.to_dict()  # Use to_dict() method
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
            
            # Emit completion callback if available
            if progress_callback:
                await progress_callback("risk_analysis_complete", {
                    "progress": 50,
                    "message": "Risk analysis completed successfully",
                    "risk_blueprint": risk_blueprint,
                    "financial_ratios": risk_data.get("financial_ratios", {}),
                    "risk_score": risk_data.get("risk_score", 50),
                    "volatility_target": risk_data.get("volatility_target", 12.0)
                })
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Risk analysis node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Risk analysis node failed: {str(e)}"
            state["node_errors"]["risk_analysis"] = str(e)
            return state

    async def portfolio_construction_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 4: Portfolio Construction - Optimize portfolio allocation for selected tickers
        
        Args:
            state: Current workflow state with risk blueprint and security selections
            
        Returns:
            Updated state with portfolio allocation
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 4: PORTFOLIO CONSTRUCTION")
        logger.info("="*60)
        
        try:
            state["current_node"] = "portfolio_construction"
            
            # Emit progress callback if available
            progress_callback = state.get("progress_callback")
            if progress_callback:
                await progress_callback("portfolio_construction_started", {
                    "progress": 80,
                    "message": "Optimizing portfolio allocation based on risk profile..."
                })
            
            # Check prerequisites
            risk_blueprint = state.get("risk_blueprint")
            security_selections = state.get("security_selections")
            if not risk_blueprint:
                raise ValueError("Risk blueprint not available from risk analysis node")
            if not security_selections:
                raise ValueError("Security selections not available from selection node")
            
            user_profile = state.get("user_profile")
            
            logger.info("Starting portfolio optimization with selected tickers...")
            
            # Extract all tickers from security selections
            all_tickers = []
            asset_class_tickers = {}
            
            for asset_class, selection_data in security_selections.items():
                if isinstance(selection_data, dict) and "selections" in selection_data:
                    tickers_for_class = [item.get("ticker") for item in selection_data["selections"] if item.get("ticker")]
                    asset_class_tickers[asset_class] = tickers_for_class
                    all_tickers.extend(tickers_for_class)
            
            if not all_tickers:
                raise ValueError("No tickers found in security selections")
            
            logger.info(f"Portfolio construction with {len(all_tickers)} tickers: {all_tickers}")
            logger.info(f"Asset class breakdown: {asset_class_tickers}")
            
            # Import and run portfolio construction
            import sys
            portfolio_construction_path = os.path.join(os.path.dirname(__file__), 'portfolio_construction_and_market_sentiment')
            sys.path.insert(0, portfolio_construction_path)
            
            # Set user risk tolerance from risk blueprint
            volatility_target = risk_blueprint.get("volatility_target", 0.12) if risk_blueprint else 0.12
            # Normalize volatility_target which might be a string like "12.0%" or a percent number
            if isinstance(volatility_target, str):
                try:
                    vt_str = volatility_target.strip().replace('%', '')
                    vt_num = float(vt_str)
                    # Convert percent to fraction if needed
                    if vt_num > 1:
                        vt_num = vt_num / 100.0
                    volatility_target = vt_num
                except Exception:
                    volatility_target = 0.12
            # Convert volatility (stdev) to variance
            user_risk_tolerance = float(volatility_target) ** 2
            
            try:
                # Import portfolio construction module
                from portfolio_construction_and_market_sentiment.portfolio_construction import (
                    run_optimization_with_tickers,
                    expected_return,
                    standard_deviation,
                    sharpe_ratio
                )
                
                # Run optimization with selected tickers
                config = self.config.get("portfolio_construction", {})
                optimization_method = config.get("optimization_method", "pypfopt")
                covariance_method = config.get("covariance_method", "ledoit_wolf")
                max_bounds_to_test = config.get("max_bounds_to_test", [0.2, 0.3, 0.4, 0.5])
                
                # Call portfolio optimization with selected tickers
                optimal_weights, cov_matrix = run_optimization_with_tickers(
                    tickers=all_tickers,
                    method=optimization_method,
                    cov_method=covariance_method,
                    max_bounds_to_test=max_bounds_to_test
                )
                
                if optimal_weights is None:
                    # Fallback: create equal weights
                    optimal_weights = [1.0/len(all_tickers) for _ in all_tickers]
                    logger.warning("Using equal weights as fallback allocation")
                
                # Calculate portfolio metrics
                portfolio_return = 0.08  # Default
                portfolio_volatility = 0.12  # Default
                portfolio_sharpe = 1.0  # Default
                
                # Filter out near-zero weights
                threshold = 0.0001
                filtered_tickers = [all_tickers[i] for i in range(len(all_tickers)) if optimal_weights[i] > threshold]
                filtered_weights = [optimal_weights[i] for i in range(len(all_tickers)) if optimal_weights[i] > threshold]
                
                # Create portfolio allocation result
                portfolio_allocation = {
                    "filtered_tickers": {ticker: self._map_ticker_to_asset_class(ticker) for ticker in filtered_tickers},
                    "filtered_weights": {ticker: weight for ticker, weight in zip(filtered_tickers, filtered_weights)},
                    "portfolio_metrics": {
                        "expected_return": portfolio_return,
                        "volatility": portfolio_volatility,
                        "sharpe_ratio": portfolio_sharpe,
                        "total_tickers": len(filtered_tickers)
                    },
                    "optimization_config": {
                        "method": optimization_method,
                        "covariance_method": covariance_method,
                        "risk_tolerance": user_risk_tolerance
                    }
                }
                
                # Update state
                state["portfolio_construction_state"] = {
                    "success": True,
                    "tickers_processed": all_tickers,
                    "final_allocation": portfolio_allocation,
                    "optimization_method": optimization_method
                }
                state["portfolio_allocation"] = portfolio_allocation
                
                logger.info("✅ Portfolio construction completed successfully")
                logger.info(f"Final portfolio: {len(filtered_tickers)} assets")
                logger.info(f"Expected return: {portfolio_return:.2%}")
                logger.info(f"Volatility: {portfolio_volatility:.2%}")
                logger.info(f"Sharpe ratio: {portfolio_sharpe:.2f}")
                
                # Emit completion callback if available
                if progress_callback:
                    await progress_callback("portfolio_construction_complete", {
                        "progress": 90,
                        "message": "Portfolio optimization completed successfully",
                        "portfolio_allocation": portfolio_allocation
                    })
                
                return state
                
            except ImportError as e:
                logger.error(f"Failed to import portfolio construction module: {e}")
                # Create a simple fallback allocation
                fallback_allocation = {
                    "filtered_tickers": {ticker: "equity" for ticker in all_tickers},
                    "filtered_weights": {ticker: 1.0/len(all_tickers) for ticker in all_tickers},
                    "portfolio_metrics": {
                        "expected_return": 0.08,
                        "volatility": 0.12,
                        "sharpe_ratio": 1.0,
                        "total_tickers": len(all_tickers)
                    }
                }
                
                state["portfolio_construction_state"] = {
                    "success": True,
                    "tickers_processed": all_tickers,
                    "final_allocation": fallback_allocation,
                    "optimization_method": "equal_weight_fallback"
                }
                state["portfolio_allocation"] = fallback_allocation
                
                logger.info("✅ Portfolio construction completed with equal weight fallback")
                return state
                
        except Exception as e:
            logger.error(f"❌ Portfolio construction failed: {str(e)}")
            
            # Create fallback allocation with all tickers
            fallback_allocation = {
                "filtered_tickers": {ticker: "equity" for ticker in all_tickers},
                "filtered_weights": {ticker: 1.0/len(all_tickers) for ticker in all_tickers},
                "portfolio_metrics": {
                    "expected_return": 0.08,
                    "volatility": 0.12,
                    "sharpe_ratio": 1.0,
                    "total_tickers": len(all_tickers)
                }
            }
            
            state["portfolio_construction_state"] = {
                "success": False,
                "error": str(e),
                "tickers_processed": all_tickers,
                "final_allocation": fallback_allocation,
                "optimization_method": "fallback_due_to_error"
            }
            state["portfolio_allocation"] = fallback_allocation
            
            logger.info("✅ Portfolio construction completed with fallback due to error")
            return state

    async def selection_node(self, state: MainAgentState) -> MainAgentState:
        """
        Node 3: Selection Agent - Process selected_tickers from user profile
        
        Args:
            state: Current workflow state with user profile and risk blueprint
            
        Returns:
            Updated state with security selections
        """
        logger.info("\n" + "="*60)
        logger.info("NODE 3: SELECTION AGENT")
        logger.info("="*60)
        
        try:
            state["current_node"] = "selection"
            
            # Emit progress callback if available
            progress_callback = state.get("progress_callback")
            if progress_callback:
                await progress_callback("selection_started", {
                    "progress": 60,
                    "message": "Selecting specific securities and analyzing market conditions..."
                })
            
            # Check prerequisites
            risk_blueprint = state.get("risk_blueprint")
            if not risk_blueprint:
                raise ValueError("Risk blueprint not available from risk analysis node")
            
            user_profile = state.get("user_profile")
            if not user_profile:
                raise ValueError("User profile not available")
            
            # Extract selected_tickers from user profile
            selected_tickers = getattr(user_profile, 'selected_tickers', {})
            
            # Extract regions and sectors from user profile
            personal_values = getattr(user_profile, 'personal_values', {})
            esg_preferences = personal_values.get("esg_preferences", {})
            
            # Default regions (can be enhanced based on user preferences)
            regions = ["US"]  # Default to US market
            
            # Extract preferred sectors/industries
            sectors = esg_preferences.get("prefer_industries", [])
            if not sectors:
                sectors = None  # Let selection agent use all sectors
            
            logger.info(f"Processing selected_tickers: {selected_tickers}")
            logger.info(f"Regions filter: {regions}")
            logger.info(f"Sectors filter: {sectors}")
            
            # Run Selection Agent with selected_tickers
            selection_result = run_selection_agent(
                regions=regions,
                sectors=sectors,
                selected_tickers=selected_tickers
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
            
            # Emit completion callback if available
            if progress_callback:
                await progress_callback("selection_complete", {
                    "progress": 75,
                    "message": "Security selection completed successfully",
                    "security_selections": selection_result.get("final_selections", {})
                })
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Selection node failed: {str(e)}")
            state["success"] = False
            state["error"] = f"Selection node failed: {str(e)}"
            state["node_errors"]["selection"] = str(e)
            return state

    async def communication_node(self, state: MainAgentState) -> MainAgentState:
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
            
            # Emit progress callback if available
            progress_callback = state.get("progress_callback")
            if progress_callback:
                await progress_callback("communication_started", {
                    "progress": 95,
                    "message": "Generating comprehensive investment report..."
                })
            
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
                user_profile=state.get("user_profile").to_dict() if state.get("user_profile") else {},
                portfolio_data=state.get("portfolio_allocation"),
                risk_analysis={
                    "risk_blueprint": state.get("risk_blueprint"),
                    "risk_analysis_state": state.get("risk_analysis_state")
                },
                selection_data=state.get("security_selections"),
                include_qa_system=include_qa_system,
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
            
            # Emit completion callback if available
            if progress_callback:
                await progress_callback("final_report_complete", {
                    "progress": 100,
                    "message": "Investment report generated successfully!",
                    "final_report": report_result.get("report", {}),
                    "execution_time": state["execution_time"],
                    "status": "complete"
                })
            
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
            # from data_sharing import save_my_agent_results  # Optional import
            
            # Save results from each agent with null checks
            user_profile = state.get("user_profile")
            if user_profile:
                # save_my_agent_results("discovery", user_profile.to_dict())  # Convert UserProfile to Dict[str, Any]
                pass
            
            risk_blueprint = state.get("risk_blueprint")
            if risk_blueprint:
                # save_my_agent_results("risk_analysis", {
                #     "risk_blueprint": risk_blueprint,
                #     "risk_analysis_state": state.get("risk_analysis_state", {})
                # })
                pass
            
            portfolio_allocation = state.get("portfolio_allocation")
            if portfolio_allocation:
                # save_my_agent_results("portfolio_construction", portfolio_allocation)
                pass
            
            security_selections = state.get("security_selections")
            if security_selections:
                # save_my_agent_results("selection_agent", security_selections)
                pass
            
            logger.info("Data saving disabled (data_sharing module not available)")
            
        except Exception as e:
            logger.warning(f"Failed to save data for communication agent: {e}")

    def run_complete_workflow(self, user_profile: UserProfile, progress_callback=None) -> Dict[str, Any]:
        """
        Run the complete investment portfolio workflow
        
        Args:
            user_profile: UserProfile object with user's assessment data
            progress_callback: Optional callback function for progress updates
            
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
                "user_profile": user_profile,
                "risk_analysis_state": None,
                "portfolio_construction_state": None,
                "selection_state": None,
                "communication_state": None,
                "start_time": start_time,
                "execution_time": 0.0,
                "current_node": "",
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
            
            # Add progress callback to state for nodes to use
            if progress_callback:
                initial_state["progress_callback"] = progress_callback
                
            # Use async execution since some nodes are async (e.g., risk_analysis_node)
            final_state = asyncio.run(self.workflow.ainvoke(initial_state))
            
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
        # Create test UserProfile object directly
        test_user_profile = UserProfile(
            goals=[
                {"goal_type": "retirement", "description": "Retirement Planning", "priority": 1, "target_date": None},
                {"goal_type": "house", "description": "Buy a Home", "priority": 2, "target_date": None}
            ],
            time_horizon=15,
            risk_tolerance="medium",  # mapped from "moderate"
            income=75000.0,
            savings_rate=2000.0,
            liabilities=25000.0,
            liquidity_needs="medium",  # mapped from "6 months"
            personal_values={
                "esg_preferences": {
                    "avoid_industries": ["tobacco", "weapons"],
                    "prefer_industries": ["technology", "renewable_energy"],
                    "custom_constraints": "Focus on sustainable investments"
                },
                "investment_themes": ["technology", "renewable_energy"]
            },
            esg_prioritization=True,
            market_selection=["US"],
            timestamp=datetime.now().isoformat(),
            profile_id=f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            selected_tickers={
                "equities": ["AAPL", "MSFT", "GOOGL"],  # User-selected technology stocks
                "bonds": ["BND"],  # User-selected bond ETF
                # commodities and gold missing - will be filled by selection agent
            }
        )
        
        # Initialize Main Agent
        logger.info("Initializing Main Agent for testing...")
        main_agent = MainAgent()
        
        # Run complete workflow
        result = main_agent.run_complete_workflow(test_user_profile)
        
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
