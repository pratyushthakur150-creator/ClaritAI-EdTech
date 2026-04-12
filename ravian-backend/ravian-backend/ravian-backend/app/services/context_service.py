"""
Context Service Module
Provides business logic for conversation context management including:
- Context creation with initial messages
- Message addition with automatic trimming
- Context retrieval and deletion
- User context listing
- Usage statistics
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class ContextService:
    """Service for managing conversation contexts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.max_messages = 100  # Maximum messages per context
        self.max_message_length = 10000  # Maximum length per message
    
    async def create_context(
        self,
        user_id: str,
        context_type: str,
        tenant_id: str,
        initial_messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation context.
        
        Args:
            user_id: UUID of the user
            context_type: Type of context (chatbot, voice_agent, teaching_assistant)
            tenant_id: UUID of the tenant
            initial_messages: Optional list of initial messages
            metadata: Optional metadata dictionary
            
        Returns:
            Dict containing the created context details
            
        Raises:
            HTTPException: If validation fails or creation fails
        """
        try:
            # Validate context type
            valid_types = ["chatbot", "voice_agent", "teaching_assistant"]
            if context_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid context_type. Must be one of: {', '.join(valid_types)}"
                )
            
            # Validate initial messages
            if initial_messages:
                if len(initial_messages) > 10:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot have more than 10 initial messages"
                    )
                
                for msg in initial_messages:
                    if len(msg.get("content", "")) > self.max_message_length:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Message content exceeds maximum length of {self.max_message_length}"
                        )
            
            # Create context object
            context_id = uuid4()
            now = datetime.utcnow()
            
            messages = initial_messages or []
            for msg in messages:
                msg['timestamp'] = now.isoformat()
            
            context_data = {
                "context_id": context_id,
                "user_id": UUID(user_id),
                "tenant_id": UUID(tenant_id),
                "context_type": context_type,
                "messages": messages,
                "message_count": len(messages),
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now
            }
            
            logger.info(f"Created context {context_id} for user {user_id}")
            
            return context_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating context: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create context: {str(e)}"
            )
    
    async def add_message(
        self,
        context_id: str,
        role: str,
        content: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to an existing context.
        
        Args:
            context_id: UUID of the context
            role: Message role (user, assistant, system)
            content: Message content
            tenant_id: UUID of the tenant
            metadata: Optional message metadata
            
        Returns:
            Dict containing the added message details
            
        Raises:
            HTTPException: If validation fails or context not found
        """
        try:
            # Validate role
            valid_roles = ["user", "assistant", "system"]
            if role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                )
            
            # Validate content
            if not content or not content.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message content cannot be empty"
                )
            
            if len(content) > self.max_message_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Message content exceeds maximum length of {self.max_message_length}"
                )
            
            # Create message
            now = datetime.utcnow()
            message = {
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": now.isoformat()
            }
            
            # Mock context update (in real implementation, this would update the database)
            message_id = str(uuid4())
            
            result = {
                "message_id": message_id,
                "context_id": UUID(context_id),
                "role": role,
                "content": content,
                "timestamp": now,
                "context_message_count": 1  # Would be actual count from DB
            }
            
            logger.info(f"Added message to context {context_id}")
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add message: {str(e)}"
            )
    
    async def get_context(
        self,
        context_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve a conversation context.
        
        Args:
            context_id: UUID of the context
            tenant_id: UUID of the tenant
            
        Returns:
            Dict containing the context details
            
        Raises:
            HTTPException: If context not found
        """
        try:
            # Mock context retrieval
            context_data = {
                "context_id": UUID(context_id),
                "user_id": UUID("00000000-0000-0000-0000-000000000000"),
                "tenant_id": UUID(tenant_id),
                "context_type": "chatbot",
                "messages": [],
                "message_count": 0,
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            logger.info(f"Retrieved context {context_id}")
            
            return context_data
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Context not found: {context_id}"
            )
    
    async def delete_context(
        self,
        context_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Delete a conversation context.
        
        Args:
            context_id: UUID of the context
            tenant_id: UUID of the tenant
            
        Returns:
            Dict containing deletion confirmation
            
        Raises:
            HTTPException: If context not found
        """
        try:
            # Mock deletion
            result = {
                "success": True,
                "context_id": UUID(context_id),
                "message_count": 0,
                "deleted_at": datetime.utcnow()
            }
            
            logger.info(f"Deleted context {context_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting context: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Context not found: {context_id}"
            )
    
    async def get_user_contexts(
        self,
        user_id: str,
        tenant_id: str,
        context_type: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all contexts for a user.
        
        Args:
            user_id: UUID of the user
            tenant_id: UUID of the tenant
            context_type: Optional filter by context type
            limit: Maximum number of contexts to return
            
        Returns:
            Dict containing list of contexts
        """
        try:
            # Mock user contexts
            result = {
                "contexts": [],
                "total_count": 0,
                "user_id": UUID(user_id)
            }
            
            logger.info(f"Retrieved contexts for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving user contexts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user contexts: {str(e)}"
            )
    
    async def get_context_stats(
        self,
        tenant_id: str,
        date_from: datetime,
        date_to: datetime
    ) -> Dict[str, Any]:
        """
        Get context usage statistics.
        
        Args:
            tenant_id: UUID of the tenant
            date_from: Start date for statistics
            date_to: End date for statistics
            
        Returns:
            Dict containing usage statistics
        """
        try:
            # Mock statistics
            stats = {
                "total_contexts": 0,
                "total_messages": 0,
                "contexts_by_type": {
                    "chatbot": 0,
                    "voice_agent": 0,
                    "teaching_assistant": 0
                },
                "messages_by_role": {
                    "user": 0,
                    "assistant": 0,
                    "system": 0
                },
                "active_contexts_last_24h": 0,
                "active_contexts_last_7d": 0,
                "avg_messages_per_context": 0.0,
                "avg_context_duration_hours": 0.0,
                "date_from": date_from,
                "date_to": date_to
            }
            
            logger.info(f"Retrieved context statistics for tenant {tenant_id}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving context stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve context statistics: {str(e)}"
            )
