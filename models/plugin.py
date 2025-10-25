from models import db
from datetime import datetime
import uuid

class UserPreference(db.Model):
    """User preferences for UI and default settings"""
    __tablename__ = 'user_preferences'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # UI preferences
    theme = db.Column(db.String(20), default='dark')
    sidebar_collapsed = db.Column(db.Boolean, default=False)

    # Default settings
    default_model = db.Column(db.String(100))
    default_temperature = db.Column(db.Float, default=0.7)
    stream_mode = db.Column(db.Boolean, default=True)

    # Feature toggles
    autogen_enabled = db.Column(db.Boolean, default=False)
    mcp_enabled = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<UserPreference for user {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'theme': self.theme,
            'sidebar_collapsed': self.sidebar_collapsed,
            'default_model': self.default_model,
            'default_temperature': self.default_temperature,
            'stream_mode': self.stream_mode,
            'autogen_enabled': self.autogen_enabled,
            'mcp_enabled': self.mcp_enabled
        }
