from pydantic import BaseModel
from datetime import datetime


class UserBase(BaseModel):
	"""We use this model when assigning the email to user."""
	email: str


class UserCreate(UserBase):
	"""UserCreate is sure to already have the email through inheritance."""
	pw: str

	class Config:
		extra = "forbid"  # makes FastAPI reject unsolicited payload extras


class User(UserCreate):
	"""User is sure to already have email and password through inheritance."""
	id: int

	class Config:
		from_attributes = True  # 'orm_mode' has since been renamed to this


class ConvoCreate(BaseModel):
	"""
	Trying out: skip BaseConvo and create Convo directly
	Note: I don't need the payload to have the "is_active" info, in creation I
	automatically set that to True.
	"""
	title: str

	class Config:
		extra = "forbid"  # makes FastAPI reject unsolicited payload extras


class Convo(ConvoCreate):
	"""
	FastAPI documentation is suggesting ForeignKey addition at this step/schema
	This makes sense in my case, because I'm having user_id in the URL rather
	than expecting it in the payload.
	"""
	id: int
	user_id: int
	is_active: bool

	class Config:
		from_attributes = True  # 'orm_mode' has since been renamed to this


class QAPairCreate(BaseModel):
	"""Don't need convo_id here, by virtue of having it in the URL"""
	query: str

	class Config:
		extra = "forbid"  # makes FastAPI reject unsolicited payload extras


class QAPair(QAPairCreate):
	"""
	The rest of the QAPair - the full picture.
	"""
	id: int
	convo_id: int
	response: str | None = None
	timestamp: datetime

	class Config:
		from_attributes = True  # 'orm_mode' has since been renamed to this


class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: str | None
