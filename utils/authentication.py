from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import schemas.schemas as schemas
from datamanager.datamanager import SQLiteDataManager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "476304cf47812d40cad469ebb13701c441325cb0c6fe6d5358df867218055788"
ALGORITHM = "HS256"


def validate_users_rights_to_convo(user_id: int, convo_id: int):
    """Raise exception if non-existent convo_id or the user_id of the
    authenticated User isn't matching the foreign user_id in Convo"""
    convo = SQLiteDataManager().get_convo(convo_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Convo not found")
    if convo.user_id != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")


def validate_user_name(name: str):
    """Raise exception if name not matching here defined criteria"""
    if len(name) < 6:
        raise HTTPException(status_code=400,
                            detail="name too short, min length 6 characters")
    if SQLiteDataManager().retrieve_user_by_name(name) is not None:
        raise HTTPException(status_code=400,
                            detail="Name already registered")


def validate_pw(password: str):
    """Raise exception if password not matching here defined criteria"""
    if len(password) < 6:
        raise HTTPException(status_code=400,
                            detail="pw too short, min length 6 characters")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Depends(oauth2_scheme) is crucial.
    It is what protects a route (all the way up the dependency chain, through
    to the endpoint in app.py) which makes FastAPI expect an:
    Authorization header with a Bearer token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = SQLiteDataManager().retrieve_user_by_name(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
