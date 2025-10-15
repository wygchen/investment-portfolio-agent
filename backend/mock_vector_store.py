"""
Mock Vector Store for Testing

This is a simplified in-memory vector store that mimics Milvus functionality
for testing the chatbot agent without requiring Docker or Milvus installation.
"""

import logging
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockVectorStore:
    """
    Mock vector store that stores documents in memory.
    
    This is a simplified implementation for testing purposes.
    In production, this would be replaced with actual Milvus operations.
    """
    
    def __init__(self):
        """Initialize the mock vector store."""
        self.documents = {}  # user_id -> list of documents
        self.embeddings = {}  # user_id -> list of embeddings
        self.collection_name = "portfolio_documents"
        
        logger.info("Mock vector store initialized")
    
    def add_documents(self, user_id: str, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            user_id: User identifier
            documents: List of document dictionaries
            
        Returns:
            True if successful
        """
        try:
            if user_id not in self.documents:
                self.documents[user_id] = []
                self.embeddings[user_id] = []
            
            for doc in documents:
                doc_id = str(uuid.uuid4())
                doc_with_id = {
                    **doc,
                    "id": doc_id,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                self.documents[user_id].append(doc_with_id)
                
                # Create mock embedding (random vector)
                import random
                mock_embedding = [random.random() for _ in range(384)]  # 384-dim vector
                self.embeddings[user_id].append(mock_embedding)
            
            logger.info(f"Added {len(documents)} documents for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def search(self, user_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search for similar documents.
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
            
        Returns:
            Dictionary containing search results
        """
        try:
            if user_id not in self.documents:
                return {
                    "total_chunks": 0,
                    "context_chunks": [],
                    "sources": []
                }
            
            # Simple keyword-based search for testing
            query_lower = query.lower()
            results = []
            
            for i, doc in enumerate(self.documents[user_id]):
                content = doc.get("content", "").lower()
                if any(word in content for word in query_lower.split()):
                    results.append({
                        "content": doc.get("content", ""),
                        "metadata": doc.get("metadata", {}),
                        "score": 0.8,  # Mock relevance score
                        "id": doc.get("id", "")
                    })
            
            # Sort by score and limit results
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:top_k]
            
            # Format sources
            sources = []
            for result in results:
                sources.append({
                    "section": result["metadata"].get("section", "Portfolio Report"),
                    "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                })
            
            return {
                "total_chunks": len(results),
                "context_chunks": results,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {
                "total_chunks": 0,
                "context_chunks": [],
                "sources": []
            }
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user."""
        return self.documents.get(user_id, [])
    
    def clear_user_documents(self, user_id: str) -> bool:
        """Clear all documents for a user."""
        try:
            if user_id in self.documents:
                del self.documents[user_id]
            if user_id in self.embeddings:
                del self.embeddings[user_id]
            logger.info(f"Cleared documents for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing documents: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        total_docs = sum(len(docs) for docs in self.documents.values())
        return {
            "total_users": len(self.documents),
            "total_documents": total_docs,
            "collection_name": self.collection_name
        }


# Global mock vector store instance
_mock_vector_store = None

def get_mock_vector_store() -> MockVectorStore:
    """Get the global mock vector store instance."""
    global _mock_vector_store
    if _mock_vector_store is None:
        _mock_vector_store = MockVectorStore()
    return _mock_vector_store


# Convenience functions that match the original vector_store.py interface
def add_portfolio_documents(user_id: str, documents: List[Dict[str, Any]]) -> bool:
    """Add portfolio documents to the vector store."""
    store = get_mock_vector_store()
    return store.add_documents(user_id, documents)

def search_portfolio_context(user_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
    """Search for portfolio context."""
    store = get_mock_vector_store()
    return store.search(user_id, query, top_k)

def get_vector_store_stats() -> Dict[str, Any]:
    """Get vector store statistics."""
    store = get_mock_vector_store()
    return store.get_stats()


if __name__ == "__main__":
    # Test the mock vector store
    print("Testing Mock Vector Store")
    print("=" * 30)
    
    # Create test documents
    test_docs = [
        {
            "content": "Portfolio allocation: 60% stocks, 30% bonds, 10% alternatives",
            "metadata": {"section": "Asset Allocation", "page": 1}
        },
        {
            "content": "Risk tolerance: Moderate with focus on long-term growth",
            "metadata": {"section": "Risk Assessment", "page": 2}
        },
        {
            "content": "Investment horizon: 10-15 years for retirement planning",
            "metadata": {"section": "Investment Goals", "page": 3}
        }
    ]
    
    # Test adding documents
    store = get_mock_vector_store()
    success = store.add_documents("test_user", test_docs)
    print(f"Added documents: {success}")
    
    # Test searching
    results = store.search("test_user", "portfolio allocation", top_k=2)
    print(f"Search results: {results['total_chunks']} chunks found")
    
    for i, chunk in enumerate(results['context_chunks']):
        print(f"Result {i+1}: {chunk['content'][:50]}...")
    
    # Test stats
    stats = store.get_stats()
    print(f"Stats: {stats}")

