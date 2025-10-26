from models import db
from datetime import datetime
import uuid

class ChatSession(db.Model):
    """Chat session model for managing conversation history"""
    __tablename__ = 'chat_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='New Chat')
    model_name = db.Column(db.String(100))  # e.g., 'llama2', 'qwen2.5:7b'
    mode = db.Column(db.String(50), default='chat')  # 'chat', 'image_gen', 'img2img'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived = db.Column(db.Boolean, default=False)
    pinned = db.Column(db.Boolean, default=False)

    # Relationships
    messages = db.relationship('Message', backref='session', lazy='dynamic',
                              cascade='all, delete-orphan', order_by='Message.created_at')
    session_metadata = db.relationship('SessionMetadata', backref='session', uselist=False,
                                      cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ChatSession {self.id} - {self.title}>'

    def to_dict(self, include_messages=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'model_name': self.model_name,
            'mode': self.mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'archived': self.archived,
            'pinned': self.pinned,
            'message_count': self.messages.count()
        }

        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages.limit(50)]

        return result


class SessionMetadata(db.Model):
    """Metadata for chat sessions including settings and statistics"""
    __tablename__ = 'session_metadata'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)

    # Session settings
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer)
    system_prompt = db.Column(db.Text)

    # Statistics
    total_messages = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)

    # Enabled features (JSON stored as strings)
    enabled_plugins = db.Column(db.JSON)  # List of enabled plugin IDs
    enabled_tools = db.Column(db.JSON)  # List of enabled tool names
    enabled_agents = db.Column(db.JSON)  # List of enabled agent names

    def __repr__(self):
        return f'<SessionMetadata for session {self.session_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'system_prompt': self.system_prompt,
            'total_messages': self.total_messages,
            'total_tokens': self.total_tokens,
            'enabled_plugins': self.enabled_plugins or [],
            'enabled_tools': self.enabled_tools or [],
            'enabled_agents': self.enabled_agents or []
        }
