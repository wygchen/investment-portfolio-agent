"""
Context Agent for Portfolio Report Retrieval

This agent retrieves relevant document chunks from the Milvus vector store
based on user queries. It uses semantic similarity search to find the most
relevant sections of portfolio reports for chatbot context.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from vector_store import get_vector_store, search_portfolio_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextAgent:
    """
    Context retrieval agent that finds relevant portfolio report sections
    based on user queries using semantic similarity search.
    """
    
    def __init__(self, 
                 top_k: int = 5,
                 score_threshold: float = 0.7,
                 max_context_length: int = 4000):
        """
        Initialize the context agent.
        
        Args:
            top_k: Number of top similar chunks to retrieve
            score_threshold: Minimum similarity score for chunks
            max_context_length: Maximum total context length
        """
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.max_context_length = max_context_length
        self.vector_store = get_vector_store()
        
        logger.info(f"Context agent initialized with top_k={top_k}, threshold={score_threshold}")
    
    def retrieve_context(self, 
                        user_id: str, 
                        query: str,
                        include_metadata: bool = True) -> Dict[str, Any]:
        """
        Retrieve relevant context chunks for a user query.
        
        Args:
            user_id: User identifier
            query: User's question/query
            include_metadata: Whether to include chunk metadata
            
        Returns:
            Dictionary containing retrieved context and metadata
        """
        try:
            logger.info(f"Retrieving context for user {user_id}, query: {query[:100]}...")
            
            # Search for similar chunks
            similar_chunks = self.vector_store.search_similar_chunks(
                user_id=user_id,
                query=query,
                top_k=self.top_k,
                score_threshold=self.score_threshold
            )
            
            if not similar_chunks:
                logger.warning(f"No relevant chunks found for user {user_id}")
                return {
                    "context_chunks": [],
                    "total_chunks": 0,
                    "total_length": 0,
                    "sources": [],
                    "retrieval_metadata": {
                        "query": query,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat(),
                        "search_successful": False,
                        "reason": "No relevant chunks found"
                    }
                }
            
            # Process and format chunks
            context_chunks = []
            sources = []
            total_length = 0
            
            for chunk in similar_chunks:
                # Extract content and metadata
                content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})
                score = chunk.get("score", 0.0)
                
                # Check if adding this chunk would exceed max length
                if total_length + len(content) > self.max_context_length:
                    logger.info(f"Reached max context length ({self.max_context_length}), stopping retrieval")
                    break
                
                # Format chunk for context
                chunk_data = {
                    "content": content,
                    "score": score,
                    "document_id": chunk.get("document_id"),
                    "chunk_index": chunk.get("chunk_index")
                }
                
                if include_metadata:
                    chunk_data["metadata"] = metadata
                
                context_chunks.append(chunk_data)
                total_length += len(content)
                
                # Track sources
                source = {
                    "document_id": chunk.get("document_id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "score": score,
                    "section": metadata.get("Header 1", "Unknown Section"),
                    "subsection": metadata.get("Header 2", "")
                }
                sources.append(source)
            
            logger.info(f"Retrieved {len(context_chunks)} context chunks, total length: {total_length}")
            
            return {
                "context_chunks": context_chunks,
                "total_chunks": len(context_chunks),
                "total_length": total_length,
                "sources": sources,
                "retrieval_metadata": {
                    "query": query,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "search_successful": True,
                    "top_k_requested": self.top_k,
                    "chunks_found": len(similar_chunks),
                    "chunks_returned": len(context_chunks),
                    "score_threshold": self.score_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {
                "context_chunks": [],
                "total_chunks": 0,
                "total_length": 0,
                "sources": [],
                "retrieval_metadata": {
                    "query": query,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "search_successful": False,
                    "error": str(e)
                }
            }
    
    def format_context_for_llm(self, context_result: Dict[str, Any]) -> str:
        """
        Format retrieved context for LLM consumption.
        
        Args:
            context_result: Result from retrieve_context method
            
        Returns:
            Formatted context string for LLM
        """
        try:
            context_chunks = context_result.get("context_chunks", [])
            
            if not context_chunks:
                return "No relevant portfolio context found."
            
            # Format context with clear sections
            formatted_context = "## Portfolio Report Context\n\n"
            
            for i, chunk in enumerate(context_chunks, 1):
                content = chunk.get("content", "")
                score = chunk.get("score", 0.0)
                metadata = chunk.get("metadata", {})
                
                # Add section header if available
                section_header = metadata.get("Header 1", "")
                subsection_header = metadata.get("Header 2", "")
                
                if section_header:
                    formatted_context += f"### {section_header}\n"
                if subsection_header:
                    formatted_context += f"#### {subsection_header}\n"
                
                # Add content
                formatted_context += f"{content}\n\n"
                
                # Add relevance score (for debugging)
                formatted_context += f"*[Relevance: {score:.3f}]*\n\n"
            
            # Add source information
            sources = context_result.get("sources", [])
            if sources:
                formatted_context += "## Sources\n\n"
                for source in sources:
                    formatted_context += f"- Document: {source.get('document_id', 'Unknown')}, "
                    formatted_context += f"Section: {source.get('section', 'Unknown')}, "
                    formatted_context += f"Score: {source.get('score', 0.0):.3f}\n"
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            return "Error formatting portfolio context."
    
    def get_user_document_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of available documents for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with document summary information
        """
        try:
            # Get user's documents
            document_ids = self.vector_store.get_user_documents(user_id)
            
            if not document_ids:
                return {
                    "user_id": user_id,
                    "total_documents": 0,
                    "document_ids": [],
                    "message": "No documents found for user"
                }
            
            # Get collection stats
            stats = self.vector_store.get_collection_stats()
            
            return {
                "user_id": user_id,
                "total_documents": len(document_ids),
                "document_ids": document_ids,
                "collection_stats": stats,
                "message": f"Found {len(document_ids)} documents for user"
            }
            
        except Exception as e:
            logger.error(f"Error getting user document summary: {e}")
            return {
                "user_id": user_id,
                "total_documents": 0,
                "document_ids": [],
                "error": str(e)
            }
    
    def clear_user_context(self, user_id: str) -> bool:
        """
        Clear all context documents for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.vector_store.delete_user_documents(user_id)
            if success:
                logger.info(f"Cleared all context documents for user {user_id}")
            else:
                logger.warning(f"Failed to clear context documents for user {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error clearing user context: {e}")
            return False


# Global context agent instance
_context_agent = None

def get_context_agent() -> ContextAgent:
    """Get the global context agent instance."""
    global _context_agent
    if _context_agent is None:
        _context_agent = ContextAgent()
    return _context_agent


# Convenience functions for easy integration
def retrieve_portfolio_context(user_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve portfolio context for a user query."""
    agent = get_context_agent()
    return agent.retrieve_context(user_id, query)


def format_context_for_chatbot(user_id: str, query: str) -> str:
    """Retrieve and format context for chatbot consumption."""
    agent = get_context_agent()
    context_result = agent.retrieve_context(user_id, query)
    return agent.format_context_for_llm(context_result)


if __name__ == "__main__":
    # Test the context agent
    agent = ContextAgent()
    
    # Test context retrieval
    test_user_id = "test_user"
    test_query = "What is the portfolio allocation strategy?"
    
    print(f"Testing context retrieval for user: {test_user_id}")
    print(f"Query: {test_query}")
    
    context_result = agent.retrieve_context(test_user_id, test_query)
    print(f"Retrieved {context_result['total_chunks']} chunks")
    
    if context_result['context_chunks']:
        formatted_context = agent.format_context_for_llm(context_result)
        print("\nFormatted context:")
        print(formatted_context[:500] + "..." if len(formatted_context) > 500 else formatted_context)
    else:
        print("No context found")
