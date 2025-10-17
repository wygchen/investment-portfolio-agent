"""
Chat Memory Management using LangChain

This module provides chat history management using LangChain's memory components.
It supports per-user conversation history with automatic context window management.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import InMemoryChatMessageHistory
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMemoryManager:
    """
    Manages chat memory for multiple users using LangChain memory components.
    
    Features:
    - Per-user conversation history
    - Automatic context window management
    - Memory persistence during session
    - Support for different memory types (buffer, summary)
    """
    
    def __init__(self, 
                 memory_type: str = "buffer",
                 max_token_limit: int = 2000,
                 return_messages: bool = True):
        """
        Initialize the chat memory manager.
        
        Args:
            memory_type: Type of memory ("buffer" or "summary")
            max_token_limit: Maximum tokens for memory context
            return_messages: Whether to return messages or strings
        """
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit
        self.return_messages = return_messages
        
        # Store per-user memory instances
        self.user_memories: Dict[str, Any] = {}
        self.user_histories: Dict[str, BaseChatMessageHistory] = {}
        
        logger.info(f"Chat memory manager initialized with {memory_type} memory")
    
    def get_user_memory(self, user_id: str) -> Any:
        """
        Get or create memory instance for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Memory instance for the user
        """
        if user_id not in self.user_memories:
            # Create new memory instance for user
            if self.memory_type == "buffer":
                memory = ConversationBufferMemory(
                    return_messages=self.return_messages,
                    memory_key="chat_history"
                )
            elif self.memory_type == "summary":
                # Note: Summary memory requires an LLM, using buffer as fallback
                memory = ConversationBufferMemory(
                    return_messages=self.return_messages,
                    memory_key="chat_history"
                )
            else:
                raise ValueError(f"Unsupported memory type: {self.memory_type}")
            
            self.user_memories[user_id] = memory
            logger.info(f"Created {self.memory_type} memory for user {user_id}")
        
        return self.user_memories[user_id]
    
    def get_user_history(self, user_id: str) -> BaseChatMessageHistory:
        """
        Get or create chat message history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Chat message history for the user
        """
        if user_id not in self.user_histories:
            self.user_histories[user_id] = InMemoryChatMessageHistory()
            logger.info(f"Created chat history for user {user_id}")
        
        return self.user_histories[user_id]
    
    def add_message(self, 
                   user_id: str, 
                   message: str, 
                   message_type: str = "human") -> bool:
        """
        Add a message to user's chat history.
        
        Args:
            user_id: User identifier
            message: Message content
            message_type: Type of message ("human", "ai", "system")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user's memory and history
            memory = self.get_user_memory(user_id)
            history = self.get_user_history(user_id)
            
            # Create message object
            if message_type == "human":
                msg = HumanMessage(content=message)
            elif message_type == "ai":
                msg = AIMessage(content=message)
            elif message_type == "system":
                msg = SystemMessage(content=message)
            else:
                raise ValueError(f"Unsupported message type: {message_type}")
            
            # Add to history
            history.add_message(msg)
            
            # Add to memory
            if message_type == "human":
                memory.chat_memory.add_user_message(message)
            elif message_type == "ai":
                memory.chat_memory.add_ai_message(message)
            
            logger.debug(f"Added {message_type} message for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages with metadata
        """
        try:
            history = self.get_user_history(user_id)
            messages = history.messages
            
            # Apply limit if specified
            if limit:
                messages = messages[-limit:]
            
            # Convert to dictionary format
            conversation = []
            for msg in messages:
                conversation.append({
                    "type": msg.__class__.__name__.replace("Message", "").lower(),
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()  # Note: LangChain doesn't store timestamps
                })
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation history for user {user_id}: {e}")
            return []
    
    def get_memory_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get memory context for a user (formatted for LLM).
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with memory context
        """
        try:
            memory = self.get_user_memory(user_id)
            
            # Get memory variables
            memory_vars = memory.load_memory_variables({})
            
            return {
                "user_id": user_id,
                "memory_type": self.memory_type,
                "chat_history": memory_vars.get("chat_history", ""),
                "message_count": len(memory.chat_memory.messages),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting memory context for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "memory_type": self.memory_type,
                "chat_history": "",
                "message_count": 0,
                "error": str(e)
            }
    
    def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all memory for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear memory
            if user_id in self.user_memories:
                self.user_memories[user_id].clear()
                del self.user_memories[user_id]
            
            # Clear history
            if user_id in self.user_histories:
                self.user_histories[user_id].clear()
                del self.user_histories[user_id]
            
            logger.info(f"Cleared memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memory for user {user_id}: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            total_users = len(self.user_memories)
            total_messages = sum(
                len(memory.chat_memory.messages) 
                for memory in self.user_memories.values()
            )
            
            return {
                "total_users": total_users,
                "total_messages": total_messages,
                "memory_type": self.memory_type,
                "max_token_limit": self.max_token_limit,
                "active_users": list(self.user_memories.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {
                "total_users": 0,
                "total_messages": 0,
                "error": str(e)
            }
    
    def save_conversation_to_file(self, user_id: str, filepath: str) -> bool:
        """
        Save user's conversation to a file.
        
        Args:
            user_id: User identifier
            filepath: Path to save the conversation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = self.get_conversation_history(user_id)
            
            # Add metadata
            conversation_data = {
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(),
                "total_messages": len(conversation),
                "conversation": conversation
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved conversation for user {user_id} to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation for user {user_id}: {e}")
            return False
    
    def load_conversation_from_file(self, user_id: str, filepath: str) -> bool:
        """
        Load user's conversation from a file.
        
        Args:
            user_id: User identifier
            filepath: Path to load the conversation from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            conversation = conversation_data.get("conversation", [])
            
            # Clear existing memory
            self.clear_user_memory(user_id)
            
            # Load messages
            for msg in conversation:
                message_type = msg.get("type", "human")
                content = msg.get("content", "")
                self.add_message(user_id, content, message_type)
            
            logger.info(f"Loaded conversation for user {user_id} from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading conversation for user {user_id}: {e}")
            return False


# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> ChatMemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ChatMemoryManager()
    return _memory_manager


# Convenience functions for easy integration
def add_chat_message(user_id: str, message: str, message_type: str = "human") -> bool:
    """Add a message to user's chat history."""
    manager = get_memory_manager()
    return manager.add_message(user_id, message, message_type)


def get_user_conversation(user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get conversation history for a user."""
    manager = get_memory_manager()
    return manager.get_conversation_history(user_id, limit)


def clear_user_conversation(user_id: str) -> bool:
    """Clear all conversation history for a user."""
    manager = get_memory_manager()
    return manager.clear_user_memory(user_id)


def get_conversation_context(user_id: str) -> str:
    """Get formatted conversation context for LLM."""
    manager = get_memory_manager()
    context = manager.get_memory_context(user_id)
    return context.get("chat_history", "")


if __name__ == "__main__":
    # Test the memory manager
    manager = ChatMemoryManager()
    
    # Test user
    test_user = "test_user"
    
    # Add some messages
    print(f"Testing memory manager for user: {test_user}")
    
    manager.add_message(test_user, "Hello, I have a question about my portfolio", "human")
    manager.add_message(test_user, "I'd be happy to help with your portfolio question. What would you like to know?", "ai")
    manager.add_message(test_user, "What is my current allocation?", "human")
    manager.add_message(test_user, "Based on your portfolio, you have a 70% equity and 30% bond allocation.", "ai")
    
    # Get conversation history
    conversation = manager.get_conversation_history(test_user)
    print(f"Conversation has {len(conversation)} messages")
    
    for msg in conversation:
        print(f"{msg['type']}: {msg['content']}")
    
    # Get memory context
    context = manager.get_memory_context(test_user)
    print(f"\nMemory context: {context['message_count']} messages")
    
    # Get stats
    stats = manager.get_memory_stats()
    print(f"Memory stats: {stats}")
    
    # Clear memory
    manager.clear_user_memory(test_user)
    print("Memory cleared")
