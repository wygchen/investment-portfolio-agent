"""
Chatbot Agent with Custom Planning Framework

This module implements a deep planning chatbot agent that can:
1. Analyze user questions and design to-do lists
2. Call context agent for portfolio-specific information
3. Call browser agent for web search when needed
4. Synthesize comprehensive answers with reasoning traces
5. Maintain conversation context using LangChain memory
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re

# Import our custom agents
from context_agent import get_context_agent, retrieve_portfolio_context
from browser_agent import get_browser_agent, search_web
from chat_memory import get_memory_manager, add_chat_message, get_conversation_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotAgent:
    """
    Deep planning chatbot agent with custom reasoning framework.
    
    Features:
    - Question analysis and task decomposition
    - Tool calling (context retrieval, web search)
    - Answer synthesis with reasoning traces
    - Conversation memory management
    - Source attribution and transparency
    """
    
    def __init__(self, 
                 llm=None,
                 max_reasoning_steps: int = 5,
                 enable_web_search: bool = True,
                 enable_context_retrieval: bool = True):
        """
        Initialize the chatbot agent.
        
        Args:
            llm: Language model for reasoning (optional)
            max_reasoning_steps: Maximum reasoning steps per query
            enable_web_search: Whether to enable web search
            enable_context_retrieval: Whether to enable context retrieval
        """
        self.llm = llm
        self.max_reasoning_steps = max_reasoning_steps
        self.enable_web_search = enable_web_search
        self.enable_context_retrieval = enable_context_retrieval
        
        # Initialize sub-agents
        self.context_agent = get_context_agent()
        self.browser_agent = get_browser_agent()
        self.memory_manager = get_memory_manager()
        
        logger.info("Chatbot agent initialized with custom planning framework")
    
    def process_message(self, 
                       user_id: str, 
                       message: str,
                       session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            user_id: User identifier
            message: User's message
            session_id: Optional session identifier
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            logger.info(f"Processing message for user {user_id}: {message[:100]}...")
            
            # Add user message to memory
            add_chat_message(user_id, message, "human")
            
            # Analyze the question and create reasoning plan
            reasoning_plan = self._analyze_question(message)
            
            # Execute the reasoning plan
            execution_result = self._execute_reasoning_plan(user_id, message, reasoning_plan)
            
            # Generate final answer
            final_answer = self._synthesize_answer(
                user_id, message, reasoning_plan, execution_result
            )
            
            # Add AI response to memory
            add_chat_message(user_id, final_answer, "ai")
            
            # Prepare response
            response = {
                "answer": final_answer,
                "reasoning_trace": execution_result.get("reasoning_trace", []),
                "sources_used": execution_result.get("sources_used", []),
                "tools_called": execution_result.get("tools_called", []),
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "reasoning_steps": len(execution_result.get("reasoning_trace", [])),
                    "context_retrieved": execution_result.get("context_retrieved", False),
                    "web_searched": execution_result.get("web_searched", False)
                }
            }
            
            logger.info(f"Generated response for user {user_id} with {len(execution_result.get('reasoning_trace', []))} reasoning steps")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your message: {str(e)}",
                "reasoning_trace": [{"step": "error", "action": "Error occurred", "result": str(e)}],
                "sources_used": [],
                "tools_called": [],
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            }
    
    def _analyze_question(self, message: str) -> Dict[str, Any]:
        """
        Analyze the user's question and create a reasoning plan.
        
        Args:
            message: User's message
            
        Returns:
            Dictionary containing reasoning plan
        """
        try:
            # Simple keyword-based analysis (can be enhanced with LLM)
            message_lower = message.lower()
            
            # Determine question type
            question_type = "general"
            if any(word in message_lower for word in ["portfolio", "allocation", "investment", "risk", "return"]):
                question_type = "portfolio_specific"
            elif any(word in message_lower for word in ["market", "news", "stock", "price", "trend"]):
                question_type = "market_related"
            elif any(word in message_lower for word in ["what", "how", "why", "when", "where"]):
                question_type = "informational"
            
            # Create reasoning plan
            plan = {
                "question_type": question_type,
                "needs_context": question_type in ["portfolio_specific", "general"],
                "needs_web_search": question_type in ["market_related", "informational"],
                "reasoning_steps": []
            }
            
            # Add reasoning steps based on question type
            if plan["needs_context"]:
                plan["reasoning_steps"].append({
                    "step": 1,
                    "action": "retrieve_portfolio_context",
                    "description": "Search portfolio reports for relevant information",
                    "priority": "high"
                })
            
            if plan["needs_web_search"]:
                plan["reasoning_steps"].append({
                    "step": 2,
                    "action": "search_web",
                    "description": "Search web for current market information",
                    "priority": "medium"
                })
            
            plan["reasoning_steps"].append({
                "step": 3,
                "action": "synthesize_answer",
                "description": "Combine information and generate comprehensive answer",
                "priority": "high"
            })
            
            logger.debug(f"Created reasoning plan: {plan}")
            return plan
            
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            return {
                "question_type": "general",
                "needs_context": True,
                "needs_web_search": False,
                "reasoning_steps": [{"step": 1, "action": "synthesize_answer", "description": "Generate basic answer", "priority": "high"}]
            }
    
    def _execute_reasoning_plan(self, 
                               user_id: str, 
                               message: str, 
                               plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the reasoning plan step by step.
        
        Args:
            user_id: User identifier
            message: User's message
            plan: Reasoning plan
            
        Returns:
            Dictionary containing execution results
        """
        try:
            reasoning_trace = []
            sources_used = []
            tools_called = []
            context_retrieved = False
            web_searched = False
            
            # Get conversation context
            conversation_context = get_conversation_context(user_id)
            
            # Execute each reasoning step
            for step in plan["reasoning_steps"]:
                step_result = self._execute_reasoning_step(
                    user_id, message, step, conversation_context
                )
                
                reasoning_trace.append(step_result)
                
                # Track results
                if step_result.get("action") == "retrieve_portfolio_context":
                    context_retrieved = True
                    if step_result.get("sources"):
                        sources_used.extend(step_result["sources"])
                
                if step_result.get("action") == "search_web":
                    web_searched = True
                    if step_result.get("sources"):
                        sources_used.extend(step_result["sources"])
                
                tools_called.append(step_result.get("action", "unknown"))
            
            return {
                "reasoning_trace": reasoning_trace,
                "sources_used": sources_used,
                "tools_called": tools_called,
                "context_retrieved": context_retrieved,
                "web_searched": web_searched
            }
            
        except Exception as e:
            logger.error(f"Error executing reasoning plan: {e}")
            return {
                "reasoning_trace": [{"step": "error", "action": "Error", "result": str(e)}],
                "sources_used": [],
                "tools_called": [],
                "context_retrieved": False,
                "web_searched": False
            }
    
    def _execute_reasoning_step(self, 
                               user_id: str, 
                               message: str, 
                               step: Dict[str, Any],
                               conversation_context: str) -> Dict[str, Any]:
        """
        Execute a single reasoning step.
        
        Args:
            user_id: User identifier
            message: User's message
            step: Reasoning step definition
            conversation_context: Conversation context
            
        Returns:
            Dictionary containing step execution result
        """
        try:
            action = step.get("action")
            step_num = step.get("step", 0)
            
            if action == "retrieve_portfolio_context":
                return self._execute_context_retrieval(user_id, message, step_num)
            elif action == "search_web":
                return self._execute_web_search(user_id, message, step_num)
            elif action == "synthesize_answer":
                return self._execute_answer_synthesis(user_id, message, step_num, conversation_context)
            else:
                return {
                    "step": step_num,
                    "action": action,
                    "result": f"Unknown action: {action}",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error executing reasoning step {step.get('action', 'unknown')}: {e}")
            return {
                "step": step.get("step", 0),
                "action": step.get("action", "unknown"),
                "result": f"Error: {str(e)}",
                "success": False
            }
    
    def _execute_context_retrieval(self, user_id: str, message: str, step_num: int) -> Dict[str, Any]:
        """Execute context retrieval step."""
        try:
            if not self.enable_context_retrieval:
                return {
                    "step": step_num,
                    "action": "retrieve_portfolio_context",
                    "result": "Context retrieval disabled",
                    "success": False
                }
            
            # Retrieve portfolio context
            context_result = retrieve_portfolio_context(user_id, message, top_k=3)
            
            if context_result.get("total_chunks", 0) > 0:
                sources = context_result.get("sources", [])
                return {
                    "step": step_num,
                    "action": "retrieve_portfolio_context",
                    "result": f"Retrieved {context_result['total_chunks']} relevant portfolio sections",
                    "success": True,
                    "context": context_result,
                    "sources": sources
                }
            else:
                return {
                    "step": step_num,
                    "action": "retrieve_portfolio_context",
                    "result": "No relevant portfolio context found",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error in context retrieval: {e}")
            return {
                "step": step_num,
                "action": "retrieve_portfolio_context",
                "result": f"Error: {str(e)}",
                "success": False
            }
    
    def _execute_web_search(self, user_id: str, message: str, step_num: int) -> Dict[str, Any]:
        """Execute web search step."""
        try:
            if not self.enable_web_search:
                return {
                    "step": step_num,
                    "action": "search_web",
                    "result": "Web search disabled",
                    "success": False
                }
            
            # Determine search type based on message content
            search_type = "google"
            if any(word in message.lower() for word in ["news", "recent", "latest"]):
                search_type = "duckduckgo"
            
            # Perform web search
            search_result = search_web(message, search_type, max_results=3)
            
            if search_result.get("total_results", 0) > 0:
                sources = []
                for result in search_result.get("results", []):
                    sources.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", ""),
                        "source_type": "web_search"
                    })
                
                return {
                    "step": step_num,
                    "action": "search_web",
                    "result": f"Found {search_result['total_results']} web search results",
                    "success": True,
                    "search_result": search_result,
                    "sources": sources
                }
            else:
                return {
                    "step": step_num,
                    "action": "search_web",
                    "result": "No web search results found",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                "step": step_num,
                "action": "search_web",
                "result": f"Error: {str(e)}",
                "success": False
            }
    
    def _execute_answer_synthesis(self, 
                                user_id: str, 
                                message: str, 
                                step_num: int,
                                conversation_context: str) -> Dict[str, Any]:
        """Execute answer synthesis step."""
        try:
            # This is a placeholder for answer synthesis
            # In a full implementation, this would use an LLM to synthesize
            # the answer from context, web search results, and conversation history
            
            return {
                "step": step_num,
                "action": "synthesize_answer",
                "result": "Answer synthesis completed",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in answer synthesis: {e}")
            return {
                "step": step_num,
                "action": "synthesize_answer",
                "result": f"Error: {str(e)}",
                "success": False
            }
    
    def _synthesize_answer(self, 
                          user_id: str, 
                          message: str, 
                          plan: Dict[str, Any],
                          execution_result: Dict[str, Any]) -> str:
        """
        Synthesize the final answer from all gathered information.
        
        Args:
            user_id: User identifier
            message: User's message
            plan: Reasoning plan
            execution_result: Execution results
            
        Returns:
            Synthesized answer string
        """
        try:
            # Get conversation context
            conversation_context = get_conversation_context(user_id)
            
            # Extract information from execution results
            context_info = ""
            web_info = ""
            sources_info = ""
            
            for step in execution_result.get("reasoning_trace", []):
                if step.get("action") == "retrieve_portfolio_context" and step.get("success"):
                    context_data = step.get("context", {})
                    if context_data:
                        context_info = self._format_context_for_answer(context_data)
                
                elif step.get("action") == "search_web" and step.get("success"):
                    search_data = step.get("search_result", {})
                    if search_data:
                        web_info = self._format_web_info_for_answer(search_data)
            
            # Format sources
            sources = execution_result.get("sources_used", [])
            if sources:
                sources_info = self._format_sources_for_answer(sources)
            
            # Generate answer based on available information
            answer = self._generate_contextual_answer(
                message, context_info, web_info, conversation_context, sources_info
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            return f"I apologize, but I encountered an error while generating my response. Please try rephrasing your question."
    
    def _format_context_for_answer(self, context_data: Dict[str, Any]) -> str:
        """Format context data for answer generation."""
        try:
            context_chunks = context_data.get("context_chunks", [])
            if not context_chunks:
                return ""
            
            formatted = "## Portfolio Information\n\n"
            for chunk in context_chunks:
                content = chunk.get("content", "")
                if content:
                    formatted += f"{content}\n\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            return ""
    
    def _format_web_info_for_answer(self, search_data: Dict[str, Any]) -> str:
        """Format web search data for answer generation."""
        try:
            results = search_data.get("results", [])
            if not results:
                return ""
            
            formatted = "## Current Market Information\n\n"
            for result in results[:2]:  # Limit to top 2 results
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if title and snippet:
                    formatted += f"**{title}**\n{snippet}\n\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting web info: {e}")
            return ""
    
    def _format_sources_for_answer(self, sources: List[Dict[str, Any]]) -> str:
        """Format sources for answer generation."""
        try:
            if not sources:
                return ""
            
            formatted = "\n## Sources\n\n"
            for i, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
                if source.get("source_type") == "web_search":
                    title = source.get("title", "")
                    url = source.get("url", "")
                    if title and url:
                        formatted += f"{i}. [{title}]({url})\n"
                else:
                    # Portfolio source
                    section = source.get("section", "Portfolio Report")
                    formatted += f"{i}. {section} (Portfolio Report)\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting sources: {e}")
            return ""
    
    def _generate_contextual_answer(self, 
                                  message: str, 
                                  context_info: str, 
                                  web_info: str,
                                  conversation_context: str,
                                  sources_info: str) -> str:
        """
        Generate a contextual answer based on available information.
        
        This is a simplified implementation. In a full system, this would
        use an LLM to generate sophisticated responses.
        """
        try:
            # Simple rule-based answer generation
            message_lower = message.lower()
            
            # Portfolio-specific questions
            if any(word in message_lower for word in ["allocation", "portfolio", "investment"]):
                if context_info:
                    return f"Based on your portfolio analysis:\n\n{context_info}\n\n{sources_info}"
                else:
                    return "I don't have access to your portfolio information. Please ensure your portfolio report has been generated first."
            
            # Market-related questions
            elif any(word in message_lower for word in ["market", "stock", "price", "news"]):
                if web_info:
                    return f"Here's the current market information:\n\n{web_info}\n\n{sources_info}"
                else:
                    return "I don't have current market information available. Please try asking about your portfolio instead."
            
            # General questions
            else:
                if context_info:
                    return f"Based on your portfolio information:\n\n{context_info}\n\n{sources_info}"
                elif web_info:
                    return f"Here's some relevant information:\n\n{web_info}\n\n{sources_info}"
                else:
                    return "I'd be happy to help! Could you please ask a specific question about your portfolio or investment strategy?"
            
        except Exception as e:
            logger.error(f"Error generating contextual answer: {e}")
            return "I apologize, but I'm having trouble generating a response. Please try again."


# Global chatbot agent instance
_chatbot_agent = None

def get_chatbot_agent() -> ChatbotAgent:
    """Get the global chatbot agent instance."""
    global _chatbot_agent
    if _chatbot_agent is None:
        _chatbot_agent = ChatbotAgent()
    return _chatbot_agent


# Convenience functions for easy integration
def process_chat_message(user_id: str, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Process a chat message and return response."""
    agent = get_chatbot_agent()
    return agent.process_message(user_id, message, session_id)


if __name__ == "__main__":
    # Test the chatbot agent
    agent = ChatbotAgent()
    
    # Test user
    test_user = "test_user"
    test_message = "What is my portfolio allocation strategy?"
    
    print(f"Testing chatbot agent for user: {test_user}")
    print(f"Message: {test_message}")
    
    response = agent.process_message(test_user, test_message)
    
    print(f"\nResponse: {response['answer']}")
    print(f"Reasoning steps: {len(response['reasoning_trace'])}")
    print(f"Sources used: {len(response['sources_used'])}")
    
    for step in response['reasoning_trace']:
        print(f"Step {step['step']}: {step['action']} - {step['result']}")
