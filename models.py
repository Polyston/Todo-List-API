from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

# SQLAlchemy model representing user data in the database
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Pydantic model used to validate data sent for user registration
class RegisterUser(BaseModel):
    name: str
    email: str
    password: str

# Pydantic model used to display the JWT token during each API response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# SQLAlchemy model representing to-do list data in the database
class TodoList(Base):
    __tablename__ = "todo-lists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    creatorOfEntry = Column(Integer, ForeignKey("users.id"))

# Pydantic model used to validate data sent for creating and updating an entry in the to-do list
class TodoItem(BaseModel):
    title: str
    description: str