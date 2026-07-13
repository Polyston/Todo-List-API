from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm

from auth import authenticate_user, createAccessToken, db_dependency, user_dependency, bcrypt_context
from models import RegisterUser, TodoItem, TodoList, TokenResponse, User

# Stores routes related to user registration/login
auth_router = APIRouter()

# Stores routes related to to-do list CRUD
todo_router = APIRouter()



# Endpoint used for user registration to create new users
@auth_router.post("/register", response_model=TokenResponse ,status_code=status.HTTP_201_CREATED)
async def register_user(registerUser: RegisterUser, db: db_dependency):

    # Stores a User object if the email passed by the user in registration exists
    user = db.query(User).filter(User.email == registerUser.email).first()

    # An error is raised if user is not none
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # create_user_model stores an instance of the User model with the registered users information
    create_user_model = User(
        name=registerUser.name,
        email=registerUser.email,
        password=bcrypt_context.hash(registerUser.password)
    )

    # The create_user_model is added to the current SQLAlchemy session
    db.add(create_user_model)

    # The object from the SQLAlchemy session is saved to the database in the users table
    db.commit()

    # Updates create_user_model by adding the automatically generated ID from the database
    db.refresh(create_user_model)

    # Stores the JWT access token 
    token = createAccessToken(create_user_model.name, create_user_model.id, timedelta(minutes=20))

    # Returns the details of the registered user
    return {"token_type": "bearer", "access_token": token}



# Endpoint used to authenticate the user and generate a token
@auth_router.post("/login", response_model=TokenResponse)
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):

    # Stores a User object if the login details are correct
    user = authenticate_user(db, form_data.username, form_data.password)

    # If the login details are incorrect, user contains None and therefore, invokes an error
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Stores the JWT access token 
    token = createAccessToken(user.name, user.id, timedelta(minutes=20))

    # The JWT access token is returned
    return {"token_type": "bearer", "access_token": token}



# CREATE operation to add a new to-do list item
@todo_router.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_entry(create_entry: TodoItem, current_user: user_dependency, db: db_dependency):

    # todo_model stores an instance of the TodoList model with the title and description passed by the user
    todo_model = TodoList(
        title = create_entry.title,
        description = create_entry.description,
        creatorOfEntry = current_user["id"]
    )

    # The todo_model is added to the current SQLAlchemy session
    db.add(todo_model)

    # The object from the SQLAlchemy session is saved to the database in the users table
    db.commit()

    # Updates todo_model by adding the automatically generated ID from the database
    db.refresh(todo_model)

    # Returns the details of the todo list entry
    return {"id": todo_model.id, "title": todo_model.title, "description": todo_model.description}



# READ operation to generate a list of to-do items
@todo_router.get("/todos")
async def get_entries(current_user: user_dependency, db: db_dependency, page: int=1, limit: int=10):

    # Stores a query which selects the todo list entries which belong to the currently authenticated user
    todoQuery = db.query(TodoList).filter(TodoList.creatorOfEntry == current_user["id"])
   
    # Stores the number of entries created by the currently authenticated user
    total = todoQuery.count()

    # offset stores the calculated number of rows to skip before returning results
    offset = (page - 1) * limit

    # todos stores the entries retrieved from the desired page
    todos = todoQuery.offset(offset).limit(limit).all()

    # Returns a list of to-do items along with the pagination details
    return {
        "data": [
            {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description
            }
            for todo in todos
        ],
        "page": page,
        "limit": limit,
        "total": total
    }



# UPDATE operation to alter an existing to-do list item
@todo_router.put("/todos/{id}")
async def update_entry(id: int, updated_todo: TodoItem, current_user: user_dependency, db: db_dependency):
     
     # Stores a TodoList object if the id passed by the user matches an existing todo list entry id.
     todo = db.query(TodoList).filter(TodoList.id == id).first()

     # If the id passed does not exist, todo contains None and therefore, invokes an error
     if not todo:
         raise HTTPException(
             status_code=status.HTTP_404_BAD_REQUEST,
             detail="todo not found"
         )
    
    # If the user id stored for the todo list entry does not match the id of the user accessing the entry, an authorization error is invoked.
     if todo.creatorOfEntry != current_user["id"]:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="User not authorized"
         )
     
     # The todo list entry has a new title and description assinged 
     todo.title = updated_todo.title
     todo.description = updated_todo.description

     # The changes are saved to the database in the todo-lists table
     db.commit()

     # Updates todo with the values from the database to show the changes made when returned 
     db.refresh(todo)
     
     # Returns the details of the todo list entry
     return {"id": todo.id, "title": todo.title, "description": todo.description}



# DELETE operation to remove an existing to-do list item
@todo_router.delete("/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(id: int, current_user: user_dependency, db: db_dependency):

    # Stores a TodoList object if the id passed by the user matches an existing todo list entry id.
    todo = db.query(TodoList).filter(TodoList.id == id).first()

    # If the id passed does not exist, todo contains None and therefore, invokes an error
    if not todo:
        raise HTTPException(
             status_code=status.HTTP_404_BAD_REQUEST,
             detail="todo not found"
        )

    # If the user id stored for the todo list entry does not match the id of the user accessing the entry, an authorization error is invoked.
    if todo.creatorOfEntry != current_user["id"]:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="User not authorized"
         )

    # The todo object is selected for deletion
    db.delete(todo)

    # The deletion of the todo object from the database is saved
    db.commit()

    # A 204 HTTP code is returned to indicate the todo object was deleted from the database successfully
    return status.HTTP_204_NO_CONTENT