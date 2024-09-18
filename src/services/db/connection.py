import os
from dotenv import load_dotenv
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

# Cargar las variables de entorno
load_dotenv()

# Definir las variables de la base de datos
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_sslmode = os.getenv('DB_SSLMODE')

# Crear la URL de la base de datos
db_url = f"cockroachdb://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"

# Crear el motor y la sesión
engine = create_engine(db_url)
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

# Definir la base declarativa
Base = declarative_base()

# Definir todos los modelos
class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    phone = Column(String, unique=True)
    flows = relationship('Flow', back_populates='user')
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())

class Flow(Base):
    __tablename__ = 'flows'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    flowId = Column(String)
    name = Column(String)
    userId = Column(String, ForeignKey('users.id'))
    user = relationship('User', back_populates='flows')
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())

class Message(Base):
    __tablename__ = 'messages'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    role = Column(String)
    text = Column(String)
    createdAt = Column(DateTime, default=func.now())
    conversationId = Column(String, ForeignKey('conversations.id'))
    conversation = relationship('Conversation', back_populates='messages')

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    phone = Column(String, unique=True)
    messages = relationship('Message', back_populates='conversation', cascade="all, delete")
    createdAt = Column(DateTime, default=func.now())

class Product(Base):
    __tablename__ = 'products'
    id = Column(String, primary_key=True, default=uuid.uuid4)
    name = Column(String)
    price = Column(Float)
    image = Column(String)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())
"""    
class MessageEvaluated(Base):
    __tablename__ = 'message_evaluated'
    id = Column(String, primary_key=True)
    is_welcome = Column(Boolean)
    want_to_buy = Column(Boolean)
    is_giving_thanks = Column(Boolean)
    is_account_information = Column(Boolean)
    is_orders = Column(Boolean)
    catalog = Column(String)

class Product(Base):
    __tablename__ = 'product'
    id = Column(String, primary_key=True)
    name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
"""

# Crear todas las tablas en la base de datos
Base.metadata.create_all(bind=engine)
