from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime

# Create a base class for declarative models, the parent for tables ("classes")
Base = declarative_base()


# Define the models
class User(Base):
    """
    The "class" (ORM) corresponds with the 'users' table.
    """
    __tablename__ = 'users'
    # The id assignment will automatically be done by SQLAlchemy when commit()
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), unique=True, nullable=False)
    pw = Column(String(80), unique=False, nullable=False)


class Convo(Base):
    """
    The "class" (ORM) corresponds with the 'convos' table basically.
    By convention, __tablename__ should be lower-cased, plural of class name.
    Class properties in a "table class" map to table columns.
    """
    __tablename__ = 'convos'
    # The id assignment will automatically be done by SQLAlchemy when commit()
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    title = Column(String(120), nullable=False)
    is_active = Column(Boolean, nullable=False)


class QAPair(Base):
    """
    Question-Answer paradigm chunk. Has:
    - query (question)
    - response (answer, nullable)
    - timestamp => to sort them in a convo each time
    """
    __tablename__ = 'qa_pairs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    convo_id = Column(ForeignKey('convos.id'), nullable=False)
    query = Column(String, nullable=False)
    response = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)


# class Token(Base):
#     """
#     Token as a string, relates to a user_id.
#     """
#     __tablename__ = 'tokens'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     token = Column(String, unique=True)
#     user_id = Column(Integer, ForeignKey('users.id'))
#     expires_at = Column(DateTime, nullable=True)
