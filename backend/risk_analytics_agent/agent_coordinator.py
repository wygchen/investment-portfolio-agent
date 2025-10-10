"""
Agent Coordinator for managing multi-agent workflows in the PortfolioAI system.
Orchestrates communication between specialized agents and manages the overall workflow.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_ibm import ChatWatsonx

from .base_agent import AgentContext, AgentResponse, AgentStatus
from .risk_analytics_agent import RiskAnalyticsAgent


logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Coordinates communication between specialized agents and manages workflow.
    Provides the main entry point for multi-agent portfolio analysis.
    """
    
    def __init__(self, llm: ChatWatsonx):
        """
        Initialize Agent Coordinator with LLM and specialized agents.
        
        Args:
            llm: ChatWatsonx instance for AI processing
        """
        self.llm = llm
        
        # Initialize specialized agents
        self.risk_agent = RiskAnalyticsAgent(llm)
        
        # Workflow state
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Agent Coordinator initialized with Risk Analytics Agent")
    
    async def process_portfolio_request(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for portfolio generation workflow.
        Coordinates multiple agents to generate comprehensive portfolio recommendations.
        
        Args:
            assessment_data: User assessment data
            
        Returns:
            Dictionary with complete portfolio analysis results
        """
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting portfolio analysis workflow for session {session_id}")
        
        try:
            # Create agent context
            context = AgentContext(
                session_id=session_id,
                user_assessment=assessment_data,
                timestamp=datetime.now().isoformat()
            )
            
            # Initialize session tracking
            self.active_sessions[session_id] = {
                "start_time": start_time,
                "status": "processing",
                "completed_agents": [],
                "results": {}
            }
            
            # Step 1: Risk Analysis
            logger.info(f"Session {session_id}: Starting risk analysis")
            risk_response = await self._execute_agent_with_monitoring(
                self.risk_agent, context, "risk_analysis"
            )
            
            if not risk_response.success:
                raise Exception(f"Risk analysis failed: {risk_response.error}")
            
            # Update context with risk analysis results
            context.risk_profile = risk_response.structured_data
            
            # Step 2: Future agents (Portfolio Agent, Market Agent) would go here
            # For now, we'll focus on the risk analysis as the foundation
            
            # Compile final results
            total_time = time.time() - start_time
            
            final_results = {
                "session_id": session_id,
                "success": True,
                "processing_time": total_time,
                "risk_analysis": {
                    "content": risk_response.content,
                    "risk_blueprint": risk_response.structured_data.get("risk_blueprint"),
                    "financial_ratios": risk_response.structured_data.get("financial_ratios"),
                    "risk_score": risk_response.structured_data.get("risk_score"),
                    "volatility_target": risk_response.structured_data.get("volatility_target"),
                    "agent_metadata": {
                        "processing_time": risk_response.processing_time,
                        "confidence": risk_response.confidence
                    }
                },
                "workflow_metadata": {
                    "completed_agents": self.active_sessions[session_id]["completed_agents"],
                    "total_processing_time": total_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Update session status
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["results"] = final_results
            
            logger.info(f"Portfolio analysis workflow completed for session {session_id} in {total_time:.2f}s")
            
            return final_results
            
        except Exception as e:
            error_msg = str(e)
            total_time = time.time() - start_time
            
            logger.error(f"Portfolio analysis workflow failed for session {session_id}: {error_msg}")
            
            # Update session status
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = "failed"
                self.active_sessions[session_id]["error"] = error_msg
            
            return {
                "session_id": session_id,
                "success": False,
                "error": error_msg,
                "processing_time": total_time,
                "workflow_metadata": {
                    "completed_agents": self.active_sessions.get(session_id, {}).get("completed_agents", []),
                    "total_processing_time": total_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _execute_agent_with_monitoring(self, 
                                           agent, 
                                           context: AgentContext, 
                                           agent_type: str) -> AgentResponse:
        """
        Execute agent with monitoring and error handling.
        
        Args:
            agent: Agent instance to execute
            context: Agent context
            agent_type: Type identifier for the agent
            
        Returns:
            AgentResponse with results
        """
        session_id = context.session_id
        
        try:
            logger.info(f"Session {session_id}: Executing {agent_type} agent ({agent.name})")
            
            # Execute agent
            response = await agent.process(context)
            
            # Update session tracking
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["completed_agents"].append({
                    "agent_name": agent.name,
                    "agent_type": agent_type,
                    "success": response.success,
                    "processing_time": response.processing_time,
                    "confidence": response.confidence,
                    "timestamp": datetime.now().isoformat()
                })
            
            if response.success:
                logger.info(f"Session {session_id}: {agent_type} completed successfully in {response.processing_time:.2f}s")
            else:
                logger.warning(f"Session {session_id}: {agent_type} failed: {response.error}")
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Session {session_id}: {agent_type} execution failed: {error_msg}")
            
            # Create error response
            return AgentResponse(
                agent_name=agent.name,
                success=False,
                content="",
                error=error_msg,
                status=AgentStatus.ERROR
            )
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information or None if not found
        """
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session_data["status"],
            "start_time": session_data["start_time"],
            "elapsed_time": time.time() - session_data["start_time"],
            "completed_agents": session_data["completed_agents"],
            "error": session_data.get("error")
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents in the coordinator."""
        return {
            "coordinator_status": "active",
            "active_sessions": len(self.active_sessions),
            "agents": {
                "risk_analytics": self.risk_agent.get_status()
            },
            "session_summary": {
                session_id: {
                    "status": data["status"],
                    "elapsed_time": time.time() - data["start_time"],
                    "completed_agents": len(data["completed_agents"])
                }
                for session_id, data in self.active_sessions.items()
            }
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old sessions to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age of sessions to keep
            
        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        
        for session_id, session_data in self.active_sessions.items():
            if current_time - session_data["start_time"] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
        
        return len(sessions_to_remove)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all agents and coordinator.
        
        Returns:
            Health check results
        """
        health_results = {
            "coordinator": "healthy",
            "agents": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check risk analytics agent
            risk_status = self.risk_agent.get_status()
            health_results["agents"]["risk_analytics"] = {
                "status": risk_status["status"],
                "healthy": risk_status["status"] != "error"
            }
            
            # Overall health assessment
            all_agents_healthy = all(
                agent_health["healthy"] 
                for agent_health in health_results["agents"].values()
            )
            
            health_results["overall_health"] = "healthy" if all_agents_healthy else "degraded"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_results["coordinator"] = "error"
            health_results["error"] = str(e)
            health_results["overall_health"] = "unhealthy"
        
        return health_results


# Global coordinator instance
_agent_coordinator: Optional[AgentCoordinator] = None


def get_agent_coordinator() -> Optional[AgentCoordinator]:
    """Get global agent coordinator instance."""
    return _agent_coordinator


async def initialize_agent_coordinator(llm: ChatWatsonx) -> AgentCoordinator:
    """
    Initialize global agent coordinator.
    
    Args:
        llm: ChatWatsonx instance
        
    Returns:
        Initialized AgentCoordinator
    """
    global _agent_coordinator
    
    logger.info("Initializing Agent Coordinator...")
    
    coordinator = AgentCoordinator(llm)
    
    # Perform health check
    health_status = await coordinator.health_check()
    
    if health_status["overall_health"] == "healthy":
        logger.info("Agent Coordinator initialized successfully - all agents healthy")
    else:
        logger.warning(f"Agent Coordinator initialized with issues: {health_status}")
    
    _agent_coordinator = coordinator
    return coordinator