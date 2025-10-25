from models import db
from datetime import datetime
import uuid

class Message(db.Model):
    """Message model for storing chat messages"""
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)

    # Image support
    image_url = db.Column(db.String(500))

    # Tool/Agent metadata
    tool_calls = db.Column(db.JSON)  # Store tool invocations
    tool_results = db.Column(db.JSON)  # Store tool results
    agent_name = db.Column(db.String(100))  # Which agent generated this

    # Token usage tracking
    tokens_used = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited = db.Column(db.Boolean, default=False)

    # For message regeneration/branching
    parent_message_id = db.Column(db.String(36), db.ForeignKey('messages.id'))
    children = db.relationship('Message', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f'<Message {self.id} - {self.role}>'

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'image_url': self.image_url,
            'tool_calls': self.tool_calls,
            'tool_results': self.tool_results,
            'agent_name': self.agent_name,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'edited': self.edited,
            'parent_message_id': self.parent_message_id
        }
