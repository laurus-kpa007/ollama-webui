from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they are registered with SQLAlchemy
from models.user import User
from models.session import ChatSession, SessionMetadata
from models.message import Message
from models.plugin import UserPreference

__all__ = ['db', 'User', 'ChatSession', 'SessionMetadata', 'Message', 'UserPreference']
