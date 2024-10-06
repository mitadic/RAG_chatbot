"""
RAG Chatbot Application.
This module provides endpoints for CRUD operations on DA.
It uses SQLite + SQLAlchemy.orm for storage, FastAPI for the server, OAuth2
with JWT Tokens for authentication, Gemini 1.5 API for generating responses.
"""

import logging
import uvicorn
from typing import Annotated
from datetime import timedelta
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
# from fastapi.responses import RedirectResponse  # no Frontend ==> no Redir
from sqlalchemy.exc import SQLAlchemyError
import schemas.schemas as schemas
import utils.authentication as auth
from datamanager.datamanager import SQLiteDataManager
from utils.response_fetcher import fetch_llm_response

logging.basicConfig(level=logging.INFO)
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

data_manager = SQLiteDataManager()

app = FastAPI()

ACCESS_TOKEN_EXPIRE_MINUTES = 30


@app.post("/token")
async def token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Over in authentication.py, OAuth2PasswordBearer() specifies tokenUrl=.
    What it specifies is the name of this here endpoint. So even though
    logging in via payload on this endpoint won't authenticate the Swagger
    session, it is still utilized indirectly when the lock symbol is clicked.
    """
    # authenticate sheer name+pw match: obsolete since using OAuth2?
    user = data_manager.retrieve_user_by_name(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="No user with that name",
                            headers={"WWW-Authenticate": "Bearer"})
    if not auth.verify_password(form_data.password, user.pw):
        raise HTTPException(status_code=400, detail="Incorrect password",
                            headers={"WWW-Authenticate": "Bearer"})

    # create Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


@app.get("/users")
def list_users():
    """:return: List[Type[schemas.User]]"""
    try:
        return data_manager.get_all_users()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users")
def create_user(user: schemas.UserCreate):
    """
    schemas.UserCreate should confirm that "name" and "pw" are in payload
        else, it will raise error 422
    schemas.User should confirm that "id" is part of the Response Model
        else, error 422?
    Not returning schemas.User because it contains the password
        obsolete attribute: response_model=schemas.User
    """
    try:
        # these functions raise HTTPExceptions
        auth.validate_user_name(user.name)
        auth.validate_pw(user.pw)

        # hash the pw before storing it in the DB
        user.pw = auth.get_password_hash(user.pw)
        new_user = data_manager.create_user(user=user)
        print(f"User '{user.name}' added successfully!")
        return {"name": new_user.name, "id": str(new_user.id)}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users")
def delete_user(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)]
):
    """Delete a user by their id.
    :Args: user_id: int
    :Raises: HTTPException: If the recipe with the specified ID is not found.
    Returns: dict: A status message indicating successful deletion and user_id.
    """
    try:
        # OBSOLETE due to authentication Depends()
        # user = data_manager.get_user(user.id)
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        user_convos = data_manager.get_all_convos(user.id)
        for convo in user_convos:
            qa_pairs = data_manager.get_all_qa_pairs(convo.id)
            for qa_pair in qa_pairs:
                data_manager.delete_qa_pair(qa_pair.id)
                print(f"QAPair with id <{qa_pair.id}> successfully deleted")
            data_manager.delete_convo(convo.id)
            print(f"Convo '{convo.title}' deleted for user '{user.name}'")
        data_manager.delete_user(user.id)
        print(f"User '{user.name}' successfully deleted")
        return {f"User '{user.name}' successfully deleted"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/me", response_model=schemas.User)
async def who_am_i(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)]
):
    return user


@app.put("/users/me/change_password")
def change_password(
        new_pw: str,
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)]
):
    """Update user's password, authorized as user"""
    try:
        auth.validate_pw(new_pw)  # will raise HTTPException
        user.pw = auth.get_password_hash(new_pw)
        data_manager.update_user(user)
        return {"Password successfully updated."}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/me/change_name")
def change_username(
        new_name: str,
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)]
):
    """Update user's password, authorized as user"""
    try:
        auth.validate_user_name(new_name)  # will raise HTTPException
        user.name = new_name
        data_manager.update_user(user)
        return {"Username successfully updated."}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
def load_convos(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)]
):
    """Fetch List of Convo objects which belong to this user"""
    try:
        # if not data_manager.retrieve_user(user_id):
        #     raise HTTPException(status_code=404, detail="Bad user ID")
        user_convos = data_manager.get_all_convos(user.id)
        print(f"Success fetching Convos for user with id <{user.id}>")
        return user_convos
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dashboard", status_code=status.HTTP_201_CREATED)
def create_convo(
        convo: schemas.ConvoCreate,
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)]
):
    """Enforce title creation to start a Convo"""
    try:
        if not data_manager.get_user(user.id):
            raise HTTPException(status_code=404, detail="Bad user ID")
        convo = data_manager.create_convo(user.id, convo)
        print(f"New Convo created for user_id <{user.id}>: '{convo.title}'")
        return convo
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/convo/{convo_id}")
def load_convo(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int
):
    """Retrieve the conversation as a composite of:
        (1) Convo object which regards the user_id
        (2) The QAPair objects with the appropriate convo_id"""
    try:
        if not data_manager.get_user(user.id):
            raise HTTPException(status_code=404, detail="User not found")
        convo = data_manager.get_convo(convo_id)
        if not convo or convo.user_id != user.id:
            raise HTTPException(status_code=404, detail="Convo not found")

        qa_pairs = data_manager.get_all_qa_pairs(convo_id)
        # they seem sorted anyway, this is a temporary safeguard
        qa_pairs = sorted(qa_pairs, key=lambda x: x.id)
        return {"convo": convo, "qa_pairs": qa_pairs}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/dashboard/convo/{convo_id}")
def delete_convo(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int
):
    try:
        if not data_manager.get_user(user.id):
            raise HTTPException(status_code=404, detail="User not found")
        convo = data_manager.get_convo(convo_id)
        if not convo or convo.user_id != user.id:
            raise HTTPException(status_code=404, detail="Convo not found")

        data_manager.delete_convo(convo_id)
        print(f"Conversation '{convo.title}' deleted for user_id {user.id}")
        return {f"Conversation '{convo.title}' deleted successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/dashboard/convo/{convo_id}",
    status_code=status.HTTP_201_CREATED
)
def submit_query(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int, qa_init: schemas.QAPairCreate
):
    """Initiate a QAPair by submitting a query, which, if successful will
    also fetch a response from the LLM API and store it.
    :return: Type[schemas.QAPair]"""
    try:
        if not data_manager.get_user(user.id):
            raise HTTPException(status_code=404, detail="User not found")
        convo = data_manager.get_convo(convo_id)
        if not convo or convo.user_id != user.id:
            raise HTTPException(status_code=404, detail="Convo not found")

        qa_pair = data_manager.create_qa_pair(convo_id, qa_init.query)
        # here: wrap query in context, truths, etc.
        response = fetch_llm_response(qa_pair.query)
        if not response:
            raise HTTPException(status_code=500, detail="LLM response fail")
        qa_pair.response = response.text
        data_manager.update_qa_pair(qa_pair)
        return qa_pair
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/dashboard/convo/{convo_id}/query")
def update_qa_pair(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int, qa_pair: schemas.QAPair
):
    """Refresh a QAPair by replacing the query, which, if successful will
    also fetch a new response from the LLM API and replace the old one.
    :return: Type[schemas.QAPair]"""
    # TODO add storing of new query, fetching of new response, del of following
    try:
        if not data_manager.get_user(user.id):
            raise HTTPException(status_code=404, detail="User not found")
        convo = data_manager.get_convo(convo_id)
        if not convo or convo.user_id != user.id:
            raise HTTPException(status_code=404, detail="Convo not found")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/dashboard/convo/{convo_id}/query")
def delete_qa_pair(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int, qa_pair: schemas.QAPair
):
    """"""
    # TODO add storing of new query, fetching of new response, del of following


# @app.post("/recipes", status_code=status.HTTP_201_CREATED)
# def create_recipe(recipe: Recipe):
#     """Create a new recipe.
#
#     Args:
#         recipe (Recipe): The recipe details to create.
#
#     Returns:
#         dict: The created recipe.
#     """
#     logger.info("entered @app.post")
#     recipes = load_recipes()
#     recipe_id = max((recipe["id"] for recipe in recipes), default=0) + 1
#     recipe.id = recipe_id
#     # .model_dump() serializes the pydantic BaseModel into Python dict
#     recipes.append(recipe.model_dump())
#     save_recipes(recipes)
#     logger.info("recipes saved in @app.post")
#     return recipe, 201
#
#
# @app.get("/recipes/{recipe_id}")
# def read_recipe(recipe_id: int):
#     """Retrieve a single recipe by its ID.
#
#     Args:
#         recipe_id (int): ID of the recipe to retrieve.
#
#     Raises:
#         HTTPException: If the recipe with the specified ID is not found.
#
#     Returns:
#         dict: The requested recipe.
#     """
#     recipes = load_recipes()
#     recipe = next((recipe for recipe in recipes if recipe["id"] == recipe_id), None)
#     if recipe is None:
#         raise HTTPException(status_code=404, detail="Recipe not found")
#     return recipe
#
#
# @app.put("/recipes/{recipe_id}")
# def update_recipe(recipe_id: int, updated_recipe: Recipe):
#     """Update a recipe by its ID.
#
#     Args:
#         recipe_id (int): ID of the recipe to update.
#         updated_recipe (Recipe): New details for the recipe.
#
#     Raises:
#         HTTPException: If the recipe with the specified ID is not found.
#
#     Returns:
#         dict: The updated recipe.
#     """
#     recipes = load_recipes()
#     recipe_index = next((index for index, r in enumerate(recipes) if r["id"] == recipe_id), None)
#
#     if recipe_index is None:
#         raise HTTPException(status_code=404, detail="Recipe not found")
#
#     updated_recipe.id = recipe_id
#     recipes[recipe_index] = updated_recipe.model_dump()
#     save_recipes(recipes)
#     return updated_recipe
#
#
# @app.delete("/recipes/{recipe_id}")
# def delete_recipe(recipe_id: int):
#     """Delete a recipe by its ID.
#
#     Args:
#         recipe_id (int): ID of the recipe to delete.
#
#     Raises:
#         HTTPException: If the recipe with the specified ID is not found.
#
#     Returns:
#         dict: A status message indicating successful deletion.
#     """
#     recipes = load_recipes()
#     recipe_index = next((index for index, r in enumerate(recipes) if r["id"] == recipe_id), None)
#
#     if recipe_index is None:
#         raise HTTPException(status_code=404, detail="Recipe not found")
#
#     del recipes[recipe_index]
#     save_recipes(recipes)
#     return {"status": "success", "message": "Recipe deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
