"""
Database models for NeuralQuery application.
Defines User, Conversation, Message, and UploadedFile models using SQLAlchemy ORM.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import bcrypt

from config import Config

# Create SQLAlchemy base
Base = declarative_base()

# Create database engine
engine = create_engine(Config.DATABASE_URL, echo=Config.DEBUG)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Get database session.
    Use this in a context manager: with get_db() as db:
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    """
    User model for authentication and user management.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship('Conversation', back_populates='user', cascade='all, delete-orphan')
    uploaded_files = relationship('UploadedFile', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """
        Hash and set user password using bcrypt.
        
        Args:
            password: Plain text password to hash
        """
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        """
        Convert user object to dictionary (exclude password).
        
        Returns:
            Dictionary representation of user
        """
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Conversation(Base):
    """
    Conversation model to store chat sessions.
    """
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255))  # First line of query
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='conversations')
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')
    uploaded_files = relationship('UploadedFile', back_populates='conversation', cascade='all, delete-orphan')
    
    def to_dict(self, include_messages=False):
        """
        Convert conversation to dictionary.
        
        Args:
            include_messages: Whether to include all messages
            
        Returns:
            Dictionary representation of conversation
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages)
        }
        
        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages]
        
        return result


class Message(Base):
    """
    Message model to store individual chat messages.
    """
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum('user', 'assistant', name='message_role'), nullable=False)
    content = Column(Text, nullable=False)
    accuracy_score = Column(Integer)  # 0-100, only for assistant messages
    sources_count = Column(Integer)  # Number of sources used
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='messages')
    
    def to_dict(self):
        """
        Convert message to dictionary.
        
        Returns:
            Dictionary representation of message
        """
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'accuracy_score': self.accuracy_score,
            'sources_count': self.sources_count,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class UploadedFile(Base):
    """
    UploadedFile model to track user-uploaded documents.
    """
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='uploaded_files')
    conversation = relationship('Conversation', back_populates='uploaded_files')
    
    def to_dict(self):
        """
        Convert uploaded file to dictionary.
        
        Returns:
            Dictionary representation of uploaded file
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }


def init_db():
    """
    Initialize database by creating all tables.
    Run this once to set up the database schema.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def drop_db():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped!")


if __name__ == '__main__':
    # Initialize database when running this file directly
    print("Initializing NeuralQuery database...")
    init_db()
