"""
Base agent class for the PortfolioAI multi-agent system.
Provides common functionality for all specialized agents.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ibm import ChatWatsonx


logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentContext:
    """Context object passed between agents"""
    session_id: str
    user_assessment: Dict[str, Any]
    market_conditions: Optional[Dict[str, Any]] = None
    risk_profile: Optional[Dict[str, Any]] = None
    portfolio_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Standardized agent response"""
    agent_name: str
    success: bool
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    confidence: float = 1.0
    error: Optional[str] = None
    status: AgentStatus = AgentStatus.COMPLETED


class BaseAgent(ABC):
    """
    Abstract base class for all PortfolioAI agents.
    Provides common functionality and interface for specialized agents.
    """
    
    def __init__(self, 
                 name: str,
                 llm: ChatWatsonx,
                 system_prompt: str,
                 max_retries: int = 2):
        """
        Initialize base agent.
        
        Args:
            name: Agent name/identifier
            llm: ChatWatsonx instance for AI processing
            system_prompt: System prompt defining agent behavior
            max_retries: Maximum retry attempts for failed operations
        """
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        
        # Agent state
        self.status = AgentStatus.IDLE
        self.conversation_history: List[Dict[str, Any]] = []
        self.context: Optional[AgentContext] = None
        
        logger.info(f"Initialized {self.name} agent")
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Main processing method for the agent.
        
        Args:
            context: Agent context with input data
            
        Returns:
            AgentResponse with processing results
        """
        start_time = time.time()
        self.status = AgentStatus.PROCESSING
        self.context = context
        
        try:
            logger.info(f"{self.name} agent starting processing for session {context.session_id}")
            
            # Validate input
            validation_result = self._validate_input(context)
            if not validation_result["valid"]:
                raise ValueError(f"Input validation failed: {validation_result['error']}")
            
            # Perform agent-specific processing
            result = await self._execute_agent_logic(context)
            
            # Post-process results
            processed_result = self._post_process_results(result, context)
            
            self.status = AgentStatus.COMPLETED
            processing_time = time.time() - start_time
            
            response = AgentResponse(
                agent_name=self.name,
                success=True,
                content=processed_result.get("content", ""),
                structured_data=processed_result.get("structured_data"),
                processing_time=processing_time,
                confidence=processed_result.get("confidence", 1.0),
                status=AgentStatus.COMPLETED
            )
            
            logger.info(f"{self.name} agent completed processing in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"{self.name} agent failed: {error_msg}")
            
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="",
                processing_time=processing_time,
                error=error_msg,
                status=AgentStatus.ERROR
            )
    
    @abstractmethod
    async def _execute_agent_logic(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute agent-specific logic. Must be implemented by subclasses.
        
        Args:
            context: Agent context with input data
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    def _validate_input(self, context: AgentContext) -> Dict[str, Any]:
        """
        Validate input context. Can be overridden by subclasses.
        
        Args:
            context: Agent context to validate
            
        Returns:
            Dictionary with validation results
        """
        if not context.session_id:
            return {"valid": False, "error": "Missing session_id"}
        
        if not context.user_assessment:
            return {"valid": False, "error": "Missing user_assessment"}
        
        return {"valid": True}
    
    def _post_process_results(self, 
                            result: Dict[str, Any], 
                            context: AgentContext) -> Dict[str, Any]:
        """
        Post-process agent results. Can be overridden by subclasses.
        
        Args:
            result: Raw processing results
            context: Agent context
            
        Returns:
            Post-processed results
        """
        return result
    
    async def _call_llm_with_retry(self, 
                                 messages: List[Any],
                                 max_retries: Optional[int] = None) -> str:
        """
        Call LLM with retry logic.
        
        Args:
            messages: List of messages for the LLM
            max_retries: Override default max retries
            
        Returns:
            LLM response content
            
        Raises:
            Exception: If all retry attempts fail
        """
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"{self.name} LLM call attempt {attempt + 1}/{retries + 1}")
                
                response = await self._invoke_llm_async(messages)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Log conversation for debugging
                self._log_conversation(messages, content)
                
                return content
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"{self.name} LLM call failed on attempt {attempt + 1}: {last_error}")
                
                if attempt < retries:
                    await self._wait_before_retry(attempt)
        
        raise Exception(f"LLM call failed after {retries + 1} attempts. Last error: {last_error}")
    
    async def _invoke_llm_async(self, messages: List[Any]) -> Any:
        """Async wrapper for LLM invocation"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm.invoke, messages)
    
    async def _wait_before_retry(self, attempt: int) -> None:
        """Wait before retry with exponential backoff"""
        import asyncio
        wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
        await asyncio.sleep(wait_time)
    
    def _log_conversation(self, messages: List[Any], response: str) -> None:
        """Log conversation for debugging and monitoring"""
        conversation_entry = {
            "timestamp": time.time(),
            "agent": self.name,
            "messages": [{"role": msg.__class__.__name__, "content": str(msg.content)} for msg in messages],
            "response": response[:200] + "..." if len(response) > 200 else response
        }
        self.conversation_history.append(conversation_entry)
        
        # Keep only last 10 conversations to prevent memory issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _create_messages(self, user_prompt: str, include_context: bool = True) -> List[Any]:
        """
        Create message list for LLM with system prompt and user input.
        
        Args:
            user_prompt: User/agent prompt
            include_context: Whether to include context information
            
        Returns:
            List of messages for LLM
        """
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add context information if available and requested
        if include_context and self.context:
            context_info = self._format_context_for_llm(self.context)
            if context_info:
                messages.append(HumanMessage(content=f"CONTEXT:\n{context_info}\n\n"))
        
        messages.append(HumanMessage(content=user_prompt))
        return messages
    
    def _format_context_for_llm(self, context: AgentContext) -> str:
        """
        Format context information for LLM consumption.
        
        Args:
            context: Agent context to format
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if context.user_assessment:
            assessment = context.user_assessment
            context_parts.append(f"USER PROFILE:")
            context_parts.append(f"- Age: {assessment.get('age', 'N/A')}")
            context_parts.append(f"- Income: ${assessment.get('income', 0):,}")
            context_parts.append(f"- Net Worth: ${assessment.get('net_worth', 0):,}")
            context_parts.append(f"- Risk Tolerance: {assessment.get('risk_tolerance', 'N/A')}/10")
            context_parts.append(f"- Time Horizon: {assessment.get('time_horizon', 'N/A')} years")
        
        if context.market_conditions:
            context_parts.append(f"\nMARKET CONDITIONS:")
            for key, value in context.market_conditions.items():
                context_parts.append(f"- {key}: {value}")
        
        if context.risk_profile:
            context_parts.append(f"\nRISK PROFILE:")
            for key, value in context.risk_profile.items():
                context_parts.append(f"- {key}: {value}")
        
        return "\n".join(context_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "name": self.name,
            "status": self.status.value,
            "conversation_history_length": len(self.conversation_history),
            "has_context": self.context is not None,
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def reset(self) -> None:
        """Reset agent state"""
        self.status = AgentStatus.IDLE
        self.context = None
        self.conversation_history.clear()
        logger.info(f"{self.name} agent reset")