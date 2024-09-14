from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    phone = Column(String, unique=True)
    flows = relationship('Flow', back_populates='user')
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())

class Flow(Base):
    __tablename__ = 'flows'
    id = Column(String, primary_key=True)
    flowId = Column(String)
    name = Column(String)
    userId = Column(String, ForeignKey('users.id'))
    user = relationship('User', back_populates='flows')
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())

class Message(Base):
    __tablename__ = 'messages'
    id = Column(String, primary_key=True)
    role = Column(String)
    text = Column(String)
    createdAt = Column(DateTime, default=func.now())
    conversationId = Column(String, ForeignKey('conversations.id'))
    conversation = relationship('Conversation', back_populates='messages')

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String, primary_key=True)
    phone = Column(String, unique=True)
    messages = relationship('Message', back_populates='conversation', cascade="all, delete")
    createdAt = Column(DateTime, default=func.now())

class Product(Base):
    __tablename__ = 'products'
    id = Column(String, primary_key=True)
    name = Column(String)
    price = Column(Float)
    image = Column(String)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())