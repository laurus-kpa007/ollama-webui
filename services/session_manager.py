from typing import List, Optional, Dict
from models import db
from models.session import ChatSession, SessionMetadata
from models.message import Message
from models.user import User
from datetime import datetime, timedelta
import redis

class SessionManager:
    """Manages chat session operations with optional Redis caching"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize session manager

        Args:
            redis_client: Optional Redis client for caching
        """
        self.redis = redis_client

    def create_session(self, user_id: str, model_name: str, mode: str = 'chat', title: str = None) -> ChatSession:
        """Create a new chat session

        Args:
            user_id: User ID
            model_name: Model name to use
            mode: Session mode ('chat', 'image_gen', 'img2img')
            title: Optional custom title

        Returns:
            Created ChatSession object
        """
        session = ChatSession(
            user_id=user_id,
            model_name=model_name,
            mode=mode,
            title=title or self._generate_title()
        )
        db.session.add(session)

        # Create metadata
        metadata = SessionMetadata(session_id=session.id)
        db.session.add(metadata)

        db.session.commit()

        # Cache in Redis for fast access
        if self.redis:
            self._cache_session(session)

        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve session with caching

        Args:
            session_id: Session ID

        Returns:
            ChatSession object or None
        """
        # Try Redis first
        if self.redis:
            cached = self._get_cached_session(session_id)
            if cached:
                return cached

        # Fallback to database
        session = ChatSession.query.get(session_id)
        if session and self.redis:
            self._cache_session(session)

        return session

    def add_message(self, session_id: str, role: str, content: str,
                   image_url: Optional[str] = None,
                   tool_calls: Optional[dict] = None,
                   agent_name: Optional[str] = None,
                   tokens_used: Optional[int] = None) -> Message:
        """Add a message to session

        Args:
            session_id: Session ID
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            image_url: Optional image URL
            tool_calls: Optional tool call data
            agent_name: Optional agent name that generated this message
            tokens_used: Optional token count

        Returns:
            Created Message object
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            image_url=image_url,
            tool_calls=tool_calls,
            agent_name=agent_name,
            tokens_used=tokens_used
        )
        db.session.add(message)

        # Update session
        session = self.get_session(session_id)
        if session:
            session.updated_at = datetime.utcnow()

            # Auto-generate title from first user message
            if role == 'user' and session.title == 'New Chat':
                session.title = self._generate_title_from_content(content)

            # Update metadata
            if session.metadata:
                session.metadata.total_messages += 1
                if tokens_used:
                    session.metadata.total_tokens += tokens_used

        db.session.commit()

        # Invalidate cache
        if self.redis:
            self.redis.delete(f"session:{session_id}")

        return message

    def get_session_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
        """Get messages from session

        Args:
            session_id: Session ID
            limit: Maximum number of messages to retrieve
            offset: Offset for pagination

        Returns:
            List of Message objects
        """
        return Message.query.filter_by(session_id=session_id)\
                           .order_by(Message.created_at.asc())\
                           .offset(offset)\
                           .limit(limit)\
                           .all()

    def list_user_sessions(self, user_id: str, include_archived: bool = False) -> List[ChatSession]:
        """List all sessions for a user

        Args:
            user_id: User ID
            include_archived: Whether to include archived sessions

        Returns:
            List of ChatSession objects
        """
        query = ChatSession.query.filter_by(user_id=user_id)

        if not include_archived:
            query = query.filter_by(archived=False)

        return query.order_by(ChatSession.updated_at.desc()).all()

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """Rename a session

        Args:
            session_id: Session ID
            new_title: New title

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.title = new_title
            session.updated_at = datetime.utcnow()
            db.session.commit()

            # Invalidate cache
            if self.redis:
                self.redis.delete(f"session:{session_id}")

            return True
        return False

    def archive_session(self, session_id: str) -> bool:
        """Archive a session

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.archived = True
            session.updated_at = datetime.utcnow()
            db.session.commit()

            # Invalidate cache
            if self.redis:
                self.redis.delete(f"session:{session_id}")

            return True
        return False

    def unarchive_session(self, session_id: str) -> bool:
        """Unarchive a session

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.archived = False
            session.updated_at = datetime.utcnow()
            db.session.commit()

            # Invalidate cache
            if self.redis:
                self.redis.delete(f"session:{session_id}")

            return True
        return False

    def toggle_pin_session(self, session_id: str) -> bool:
        """Toggle pin status of a session

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.pinned = not session.pinned
            session.updated_at = datetime.utcnow()
            db.session.commit()

            # Invalidate cache
            if self.redis:
                self.redis.delete(f"session:{session_id}")

            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            db.session.delete(session)
            db.session.commit()

            if self.redis:
                self.redis.delete(f"session:{session_id}")

            return True
        return False

    def search_sessions(self, user_id: str, query: str) -> List[ChatSession]:
        """Search sessions by title or content

        Args:
            user_id: User ID
            query: Search query

        Returns:
            List of matching ChatSession objects
        """
        # Search in session titles
        title_matches = ChatSession.query.filter(
            ChatSession.user_id == user_id,
            ChatSession.title.ilike(f'%{query}%')
        ).all()

        # Search in message content
        content_matches = db.session.query(ChatSession)\
            .join(Message)\
            .filter(
                ChatSession.user_id == user_id,
                Message.content.ilike(f'%{query}%')
            )\
            .distinct()\
            .all()

        # Combine and deduplicate
        all_matches = {s.id: s for s in title_matches + content_matches}
        return list(all_matches.values())

    def get_or_create_default_user(self, username: str = 'default') -> User:
        """Get or create default user for single-user mode

        Args:
            username: Username

        Returns:
            User object
        """
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=f'{username}@localhost')
            db.session.add(user)
            db.session.commit()
        return user

    def _generate_title(self) -> str:
        """Generate default title with timestamp"""
        return f"Chat - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

    def _generate_title_from_content(self, content: str, max_length: int = 50) -> str:
        """Generate title from message content

        Args:
            content: Message content
            max_length: Maximum title length

        Returns:
            Generated title
        """
        # Simple truncation - could use LLM for better titles in future
        if len(content) <= max_length:
            return content
        return content[:max_length-3] + "..."

    def _cache_session(self, session: ChatSession):
        """Cache session in Redis

        Args:
            session: ChatSession object
        """
        if self.redis:
            try:
                key = f"session:{session.id}"
                # Store session ID with 1 hour expiration
                self.redis.setex(key, timedelta(hours=1), session.id)
            except Exception as e:
                print(f"Redis cache error: {e}")

    def _get_cached_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session from Redis cache

        Args:
            session_id: Session ID

        Returns:
            ChatSession object or None
        """
        if self.redis:
            try:
                if self.redis.exists(f"session:{session_id}"):
                    return ChatSession.query.get(session_id)
            except Exception as e:
                print(f"Redis cache error: {e}")
        return None

    def update_session_metadata(self, session_id: str, **kwargs) -> bool:
        """Update session metadata

        Args:
            session_id: Session ID
            **kwargs: Metadata fields to update

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session or not session.metadata:
            return False

        metadata = session.metadata
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        db.session.commit()

        # Invalidate cache
        if self.redis:
            self.redis.delete(f"session:{session_id}")

        return True
