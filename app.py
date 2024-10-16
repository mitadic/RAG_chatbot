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
import utils.wrap as wrap
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
    """:return: List[Type[schemas.User]]. Does include hashed pw, but brief"""
    try:
        return data_manager.get_all_users()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users", status_code=status.HTTP_201_CREATED)
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
    """Delete a user by their id."""
    try:
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


@app.put("/users/me/change_password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        new_pw: str
):
    """Update user's password, authorized as user"""
    try:
        auth.validate_pw(new_pw)  # will raise HTTPException
        user.pw = auth.get_password_hash(new_pw)
        data_manager.update_user(user)
        return {"Password successfully updated."}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/me/change_name", status_code=status.HTTP_204_NO_CONTENT)
def change_username(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        new_name: str
):
    """Update username, authorized as user"""
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
        user_convos = data_manager.get_all_convos(user.id)
        print(f"Success fetching Convos for user with id <{user.id}>")
        return user_convos
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dashboard", status_code=status.HTTP_201_CREATED)
def create_convo(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo: schemas.ConvoCreate
):
    """Enforce title creation to start a Convo"""
    try:
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
        convo = data_manager.get_convo(convo_id)
        auth.validate_users_rights_to_convo(user.id, convo_id)  # will raise E

        qa_pairs = data_manager.get_all_qa_pairs(convo_id)
        return {"convo": convo, "qa_pairs": qa_pairs}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/dashboard/convo/{convo_id}")
def delete_convo(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int
):
    """Delete related QAPairs, then the Convo itself."""
    try:
        convo = data_manager.get_convo(convo_id)
        auth.validate_users_rights_to_convo(user.id, convo_id)  # will raise E

        qa_pairs = data_manager.get_all_qa_pairs(convo.id)
        for qa_pair in qa_pairs:
            data_manager.delete_qa_pair(qa_pair.id)
            print(f"QAPair with id <{qa_pair.id}> successfully deleted")
        data_manager.delete_convo(convo_id)
        print(f"Convo '{convo.title}' deleted for user '{user.name}'")

        return {f"Conversation '{convo.title}' deleted successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dashboard/convo/{convo_id}", status_code=status.HTTP_201_CREATED)
def submit_query(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        convo_id: int, qa_init: schemas.QAPairCreate
):
    """Initiate a QAPair by submitting a query, which, if successful will
    also fetch a response from the LLM API and store it."""
    try:
        auth.validate_users_rights_to_convo(user.id, convo_id)  # will raise E

        # create qa_pair
        qa_pair = data_manager.create_qa_pair(convo_id, qa_init.query)

        # wrap the LLM query in context, truths, etc.
        all_convo_qa_pairs = data_manager.get_all_qa_pairs(convo_id)
        wrapper = wrap.convo_thus_far(all_convo_qa_pairs,
                                      all_convo_qa_pairs[-1].id)

        # send query to LLM
        response = fetch_llm_response(wrapper + qa_pair.query)
        if not response:
            raise HTTPException(status_code=500, detail="LLM response fail")
        qa_pair.response = response.text
        data_manager.update_qa_pair(qa_pair)
        return {"query": qa_pair.query, "response": qa_pair.response}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/dashboard/qa/{qa_pair_id}/resubmit_query",
         status_code=status.HTTP_201_CREATED)
def resubmit_query(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        qa_pair_id: int, new_query: str
):
    """Refresh a QAPair by replacing the query, which, if successful will
    also fetch a new response from the LLM API and replace the old one, as
    well as delete subsequent QAPairs ChatGPT-style."""
    try:
        qa_pair = data_manager.get_qa_pair(qa_pair_id)
        if qa_pair is None:
            raise HTTPException(status_code=404, detail="Query not found")
        auth.validate_users_rights_to_convo(user.id, qa_pair.convo_id)  # E

        # Get all qa_pairs, then generate wrapper
        all_convo_qa_pairs = data_manager.get_all_qa_pairs(qa_pair.convo_id)
        wrapper = wrap.convo_thus_far(all_convo_qa_pairs, qa_pair_id)

        # update qa_pair
        qa_pair.query = new_query
        response = fetch_llm_response(wrapper + qa_pair.query)
        if not response:
            raise HTTPException(status_code=500, detail="LLM response fail")
        qa_pair.response = response.text
        data_manager.update_qa_pair(qa_pair)

        # delete all QAPairs chronologically after the updated one
        for other_qa in all_convo_qa_pairs:
            if other_qa.id > qa_pair.id:
                data_manager.delete_qa_pair(other_qa.id)
                print(f"QAPair with id <{other_qa.id}> successfully deleted")
        return {"query": qa_pair.query, "response": qa_pair.response}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/dashboard/qa/{qa_pair_id}/fetch_different_response",
         status_code=status.HTTP_201_CREATED)
def fetch_different_response(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        qa_pair_id: int
):
    """Refresh a QAPair by fetching a new response from LLM and storing it,
    as well as deleting subsequent QAPairs ChatGPT-style."""
    try:
        qa_pair = data_manager.get_qa_pair(qa_pair_id)
        if qa_pair is None:
            raise HTTPException(status_code=404, detail="Query not found")
        auth.validate_users_rights_to_convo(user.id, qa_pair.convo_id)

        # Get all qa_pairs, then generate wrapper
        all_convo_qa_pairs = data_manager.get_all_qa_pairs(qa_pair.convo_id)
        wrapper = wrap.convo_thus_far(all_convo_qa_pairs, qa_pair_id)

        # update qa_pair
        response = fetch_llm_response(wrapper + qa_pair.query)
        if not response:
            raise HTTPException(status_code=500, detail="LLM response fail")
        qa_pair.response = response.text
        data_manager.update_qa_pair(qa_pair)

        # delete all QAPairs chronologically after the updated one
        for other_qa in all_convo_qa_pairs:
            if other_qa.id > qa_pair.id:
                data_manager.delete_qa_pair(other_qa.id)
                print(f"QAPair with id <{other_qa.id}> successfully deleted")
        return {"query": qa_pair.query, "response": qa_pair.response}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/dashboard/qa/{qa_pair_id}")
def delete_qa_pair(
        user: Annotated[schemas.User, Depends(auth.get_current_active_user)],
        qa_pair_id: int
):
    """Delete QAPair and any chronologically subsequent QAPairs"""
    try:
        qa_pair = data_manager.get_qa_pair(qa_pair_id)
        if qa_pair is None:
            raise HTTPException(status_code=404, detail="Query not found")
        auth.validate_users_rights_to_convo(user.id, qa_pair.convo_id)

        # delete all QAPairs chronologically after the one being updated
        all_convo_qa_pairs = data_manager.get_all_qa_pairs(qa_pair.convo_id)
        for other_qa in all_convo_qa_pairs:
            if other_qa.id > qa_pair.id:
                data_manager.delete_qa_pair(other_qa.id)
                print(f"QAPair with id <{other_qa.id}> successfully deleted")
        data_manager.delete_qa_pair(qa_pair.id)
        return {f"QAPair with id <{qa_pair.id}> successfully deleted"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
