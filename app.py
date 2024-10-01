"""
RAG Chatbot Application.

This module provides endpoints for CRUD operations on DA.
It uses SQLite + SQLAlchemy.orm for storage, and FastAPI for the server.
"""

import os
import sys
import logging
from datamanager.datamanager import SQLiteDataManager
import uvicorn
from fastapi import FastAPI, HTTPException
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
if not find_dotenv():
    print("Error: .env file not found. Consult README.md")
    sys.exit(1)
import schemas.schemas as schemas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data_manager = SQLiteDataManager()
app = FastAPI()

load_dotenv()
API_KEY = os.getenv('API_KEY')
genai.configure(api_key=os.environ.get(API_KEY))
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
# response = model.generate_content("Explain how AI works")
# print(response.text)


@app.post("/login")
def login(username: str, pw: str):
    """Attempt login."""
    pass


@app.get("/users/")
def list_users():
    """:return: List[Type[schemas.User]]"""
    return data_manager.get_all_users()


@app.post("/users/")
def create_user(user: schemas.UserCreate):
    """
    schemas.UserCreate should confirm that "email" and "pw" are in payload
        else, it will raise error 422
    schemas.User should confirm that "id" is part of the Response Model
        else, error 422?
    Not returning schemas.User because it contains the password
        obsolete attribute: response_model=schemas.User
    """
    if not data_manager.is_available_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        new_user = data_manager.create_user(user=user)
        return {"email": new_user.email, "id": str(new_user.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user by their id.
    Args: user_id: int
    Raises: HTTPException: If the recipe with the specified ID is not found.
    Returns: dict: A status message indicating successful deletion and user_id.
    """
    user = data_manager.retrieve_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data_manager.delete_user(user_id)
    return {f"User '{user.email}' deleted successfully"}


@app.get("/users/{user_id}/convos")
def user_homepage(user_id: int):
    """Fetch List of Convo objects which belong to this user"""
    if not data_manager.retrieve_user(user_id):
        raise HTTPException(status_code=404, detail="Bad user ID")
    user_convos = data_manager.get_convos(user_id)
    return user_convos


@app.post("/users/{user_id}/convos/")
def create_convo(user_id: int, convo: schemas.ConvoCreate):
    if not data_manager.retrieve_user(user_id):
        raise HTTPException(status_code=404, detail="Bad user ID")
    try:
        convo = data_manager.create_convo(user_id, convo)
        return convo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/convos/{convo_id}")
def load_convo(user_id: int, convo_id: int):
    if not data_manager.retrieve_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    convo = data_manager.load_convo(user_id, convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Convo not found")
    qa_pairs = data_manager.load_qa_pairs(convo_id)
    # sorted(qa_pairs, key=qa_pairs.)
    return {"convo": convo, "qa_pairs": qa_pairs}


@app.post("/users/{user_id}/convos/{convo_id}")
def submit_query(user_id: int, convo_id: int, qa_pair: schemas.QAPairCreate):
    if not data_manager.retrieve_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if not data_manager.load_convo(user_id, convo_id):
        raise HTTPException(status_code=404, detail="Convo not found")
    qa_pair = data_manager.init_qa_pair(convo_id, qa_pair.query)
    return qa_pair


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
