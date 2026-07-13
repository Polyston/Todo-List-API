from datetime import datetime, timedelta, timezone
import os
from passlib.context import CryptContext
from jose import jwt, JWTError 
from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlalchemy.orm import Session
from database import get_db
from models import User
from dotenv import load_dotenv

load_dotenv()

# The secret key and algorithm are retrieved from .env and used to sign and verify JWT tokens with a specific algorithm to create the signatures
Secret_key = os.getenv("Secret_Key")
Algorithm = os.getenv("Algorithm")

# Bcrypt context is used to hash and verify user passwords
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Retrieves the JWT token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Dependency to get the current user based on the provided JWT token
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    # The payload from the JWT is extracted, if the token cannot be verified, a JWT error is returned
    try:
        # The payload is extracted from the JWT token and user information is stored in username and user_id. JWTError is raised if the token cannot be verified
        payload = jwt.decode(token, Secret_key, algorithms=Algorithm)
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        # If username or user_id do not store user information, the user cannot be authenticated
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        
        # If the payload has valid user information, the user in the payload is returned
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

# Authenticates a user by checking if their provided email and password match an existing entry inside the database
def authenticate_user(db: Session, email: str, password: str):
    # Stores a user object if the email passed by the user is found, None otherwise.
    user = db.query(User).filter(User.email == email).first()

    # Evaluates user
    if not user:
        return False
    
    # The salt of the hashed password in the users table is extracted and hashes the passed password and then both hashes are compared and evaluated to true if they match, false otherwise
    if not bcrypt_context.verify(password, user.password):
        return False
    
    # Returns authenticated user object
    return user

# Creates and returns the JWT token of a user
def createAccessToken(username: str, user_id: int, expires_delta: timedelta):
    # A dictionary of user data is created which is used as the JWT tokens payload
    encode = {'sub': username, 'id': user_id}

    # Stores the expiry time of the JWT token
    expires = datetime.now(timezone.utc) + expires_delta

    # 'expires' is added to the JWT payload
    encode.update({'exp': expires})

    # The JWT token is encoded with the 'encode' payload signed with secret key and returned
    return jwt.encode(encode, Secret_key, algorithm=Algorithm)

# Dependency is used to provide routes with access to a database session
db_dependency = Annotated[Session, Depends(get_db)]

# Dependency is used to provide routes with the authenticated user
user_dependency = Annotated[User, Depends(get_current_user)]