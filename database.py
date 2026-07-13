
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Stores the URL to the SQLite database file.
dbURL = "sqlite:///./todo.db"

# The SQLAlchemy engine is created to allow python to communicate with SQLite
Engine = create_engine(dbURL, connect_args={"check_same_thread": False})

# Used to create sessions which allow routes to interact with the database
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# The Base class is used to tell SQLAlchemy that a model is a table
Base = declarative_base()

# Dependency for endpoints which creates a database session for them.
def get_db():
    db = sessionLocal()

    # 'yield' creates a temporary db session that is closed after the endpoint call is completed
    try:
        yield db
    finally:
        db.close()