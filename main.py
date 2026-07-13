from fastapi import FastAPI
from database import Base, Engine
from routes import auth_router, todo_router

# A FASTAPI instance is created
app = FastAPI()

# The database tables defined by the SQLAlchemy models are created in the database
Base.metadata.create_all(bind=Engine)

# The routers for user authentication and the todo list are added to the FastAPI instance
app.include_router(auth_router)
app.include_router(todo_router)