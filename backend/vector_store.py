"""
Vector Store for Portfolio Reports using Milvus Lite

This module handles the storage and retrieval of portfolio report chunks
using Milvus Lite for vector similarity search. It integrates with
LangChain's text splitters and embedding models.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# Milvus imports
from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema, DataType,
    utility, MilvusException
)

# LangChain imports
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioVectorStore:
    """
    Vector store for portfolio reports using Milvus Lite.
    
    Handles:
    - Document chunking using MarkdownHeaderTextSplitter
    - Embedding generation using SentenceTransformer
    - Vector storage and retrieval in Milvus
    - User-specific document isolation
    """
    
    def __init__(self, 
                 collection_name: str = "portfolio_reports",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the Milvus collection
            embedding_model: SentenceTransformer model name
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize components
        self.embedding_model = None
        self.collection = None
        self.text_splitter = None
        
        # Initialize Milvus connection and collection
        self._initialize_milvus()
        self._initialize_embedding_model()
        self._initialize_text_splitter()
    
    def _initialize_milvus(self):
        """Initialize Milvus connection and create collection if needed."""
        try:
            # Connect to Milvus Lite (embedded)
            connections.connect(
                alias="default",
                uri="./milvus_lite.db"  # Local file-based database
            )
            
            # Check if collection exists
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Connected to existing collection: {self.collection_name}")
            else:
                # Create collection
                self._create_collection()
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Milvus: {e}")
            raise
    
    def _create_collection(self):
        """Create the Milvus collection with proper schema."""
        try:
            # Define collection schema
            fields = [
                FieldSchema(
                    name="id", 
                    dtype=DataType.INT64, 
                    is_primary=True, 
                    auto_id=True
                ),
                FieldSchema(
                    name="user_id", 
                    dtype=DataType.VARCHAR, 
                    max_length=100
                ),
                FieldSchema(
                    name="document_id", 
                    dtype=DataType.VARCHAR, 
                    max_length=100
                ),
                FieldSchema(
                    name="chunk_index", 
                    dtype=DataType.INT64
                ),
                FieldSchema(
                    name="content", 
                    dtype=DataType.VARCHAR, 
                    max_length=65535
                ),
                FieldSchema(
                    name="metadata", 
                    dtype=DataType.VARCHAR, 
                    max_length=65535
                ),
                FieldSchema(
                    name="embedding", 
                    dtype=DataType.FLOAT_VECTOR, 
                    dim=384  # all-MiniLM-L6-v2 dimension
                )
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="Portfolio report chunks with embeddings"
            )
            
            # Create collection
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # Create index for vector search
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info("Collection created successfully with vector index")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model."""
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Embedding model loaded: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _initialize_text_splitter(self):
        """Initialize the markdown text splitter."""
        try:
            # Define headers to split on
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]
            
            self.text_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on,
                strip_headers=False
            )
            
            logger.info("Markdown text splitter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize text splitter: {e}")
            raise
    
    def add_document(self, 
                    user_id: str, 
                    document_id: str, 
                    markdown_content: str,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a markdown document to the vector store.
        
        Args:
            user_id: User identifier
            document_id: Document identifier (e.g., report_id)
            markdown_content: Markdown content to split and store
            metadata: Additional metadata for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Split markdown into chunks
            chunks = self._split_markdown(markdown_content)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document_id}")
                return False
            
            # Prepare data for insertion
            data_to_insert = []
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self._generate_embedding(chunk.page_content)
                
                # Prepare metadata
                chunk_metadata = {
                    "source": document_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {}),
                    **(chunk.metadata or {})
                }
                
                # Prepare record
                record = {
                    "user_id": user_id,
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk.page_content,
                    "metadata": json.dumps(chunk_metadata),
                    "embedding": embedding
                }
                
                data_to_insert.append(record)
            
            # Insert into Milvus
            self.collection.insert(data_to_insert)
            self.collection.flush()
            
            logger.info(f"Added {len(data_to_insert)} chunks for user {user_id}, document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def _split_markdown(self, markdown_content: str) -> List[Document]:
        """
        Split markdown content into chunks.
        
        Args:
            markdown_content: Raw markdown content
            
        Returns:
            List of Document objects
        """
        try:
            # Split by headers
            header_splits = self.text_splitter.split_text(markdown_content)
            
            # Further split large chunks if needed
            all_chunks = []
            for split in header_splits:
                if len(split.page_content) <= self.chunk_size:
                    all_chunks.append(split)
                else:
                    # Split large chunks further
                    from langchain_text_splitters import RecursiveCharacterTextSplitter
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                        length_function=len,
                    )
                    sub_chunks = text_splitter.split_documents([split])
                    all_chunks.extend(sub_chunks)
            
            return all_chunks
            
        except Exception as e:
            logger.error(f"Failed to split markdown: {e}")
            return []
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    def search_similar_chunks(self, 
                            user_id: str, 
                            query: str, 
                            top_k: int = 5,
                            score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar chunks based on query.
        
        Args:
            user_id: User identifier to filter results
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return []
            
            # Load collection into memory
            self.collection.load()
            
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Perform search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=f'user_id == "{user_id}"',  # Filter by user
                output_fields=["user_id", "document_id", "chunk_index", "content", "metadata"]
            )
            
            # Process results
            similar_chunks = []
            for hits in results:
                for hit in hits:
                    if hit.score >= score_threshold:
                        chunk_data = {
                            "id": hit.id,
                            "score": float(hit.score),
                            "content": hit.entity.get("content"),
                            "metadata": json.loads(hit.entity.get("metadata", "{}")),
                            "document_id": hit.entity.get("document_id"),
                            "chunk_index": hit.entity.get("chunk_index")
                        }
                        similar_chunks.append(chunk_data)
            
            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            return []
    
    def get_user_documents(self, user_id: str) -> List[str]:
        """
        Get all document IDs for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of document IDs
        """
        try:
            # Query for user's documents
            results = self.collection.query(
                expr=f'user_id == "{user_id}"',
                output_fields=["document_id"],
                limit=1000  # Reasonable limit
            )
            
            # Extract unique document IDs
            document_ids = list(set([result["document_id"] for result in results]))
            return document_ids
            
        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            return []
    
    def delete_user_documents(self, user_id: str) -> bool:
        """
        Delete all documents for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete all records for user
            self.collection.delete(
                expr=f'user_id == "{user_id}"'
            )
            self.collection.flush()
            
            logger.info(f"Deleted all documents for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user documents: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with collection stats
        """
        try:
            stats = self.collection.get_stats()
            return {
                "total_entities": stats.get("row_count", 0),
                "collection_name": self.collection_name,
                "is_loaded": self.collection.has_index()
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}


# Global vector store instance
_vector_store = None

def get_vector_store() -> PortfolioVectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = PortfolioVectorStore()
    return _vector_store


# Convenience functions for easy integration
def add_portfolio_report(user_id: str, report_id: str, markdown_content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Add a portfolio report to the vector store."""
    store = get_vector_store()
    return store.add_document(user_id, report_id, markdown_content, metadata)


def search_portfolio_context(user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for relevant portfolio context."""
    store = get_vector_store()
    return store.search_similar_chunks(user_id, query, top_k)


def clear_user_reports(user_id: str) -> bool:
    """Clear all reports for a user."""
    store = get_vector_store()
    return store.delete_user_documents(user_id)


if __name__ == "__main__":
    # Test the vector store
    store = PortfolioVectorStore()
    
    # Test markdown splitting
    test_markdown = """
# Investment Portfolio Analysis

## Executive Summary
This is a test portfolio report.

### Risk Analysis
The portfolio has moderate risk.

## Portfolio Allocation
- 60% Stocks
- 40% Bonds
"""
    
    # Test adding document
    success = store.add_document(
        user_id="test_user",
        document_id="test_report",
        markdown_content=test_markdown,
        metadata={"report_type": "test"}
    )
    
    print(f"Document added: {success}")
    
    # Test search
    results = store.search_similar_chunks("test_user", "portfolio allocation", top_k=3)
    print(f"Search results: {len(results)} chunks found")
    
    for result in results:
        print(f"Score: {result['score']:.3f}, Content: {result['content'][:100]}...")
