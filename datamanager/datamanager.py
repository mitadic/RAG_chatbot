"""
Docstring
"""

from typing import Type, List, cast, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import literal, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from datamanager.models import Base, User, Convo, QAPair, Chunk
import schemas.schemas as schemas


SQL_FILEPATH = 'sqlite:///data/chatbot_service_db.sqlite'

# Create the database engine/connection with a unique quirk 4 SQLite/FastAPI
engine = create_engine(
    SQL_FILEPATH, connect_args={"check_same_thread": False}
)
# Create a session factory
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create the tables (if not yet created). Must be done below 'Base' usages
Base.metadata.create_all(engine)


class SQLiteDataManager:
    def __init__(self):
        self.db_session = Session()  # Create a session instance

    def get_all_users(self) -> List[Type[schemas.User]]:
        """Return a [] of User objects"""
        return self.db_session.query(User).all()

    def create_user(self, user: schemas.UserCreate):
        """Register a new user via schema, return with id assigned"""
        new_user = User(name=user.name, pw=user.pw)
        self.db_session.add(new_user)
        # SQLAlchemy will now automatically generate a unique ID when commit()
        self.db_session.commit()
        self.db_session.refresh(new_user)  # new addition
        return new_user

    def get_user(self, user_id: int) -> Optional[Type[User]]:
        """Return User if user_id present in 'users' table, else None"""
        existing_user = self.db_session.query(User).filter_by(
            id=user_id).first()
        return existing_user  # will be None if not found

    def update_user(self, user: schemas.User):
        """Update user"""
        self.db_session.query(User).filter_by(id=user.id).update({
            'name': user.name,
            'pw': user.pw
        })
        self.db_session.commit()
        # self.db_session.refresh(user)  # No, this ain't a SQLAlchemy object

    def delete_user(self, user_id: int):
        """Remove a user from the database"""
        self.db_session.delete(self.get_user(user_id))
        self.db_session.commit()

    def retrieve_user_by_name(self, name: str) -> Optional[Type[User]]:
        """Return User object if name found, else None"""
        # .first() ensures that None is returned for no match, unlike .all()
        existing_user = self.db_session.query(User).filter_by(
            name=name).first()
        return existing_user

    def get_all_convos(self, user_id: int) -> List[Type[Convo]]:
        """
        Return a [] of Convo objects associated with user_id
        """
        convo_objects_list = self.db_session.query(Convo) \
            .filter(Convo.user_id == literal(user_id)) \
            .all()
        return convo_objects_list

    def create_convo(self, user_id: int, convo: schemas.ConvoCreate):
        new_convo = Convo(user_id=user_id, title=convo.title,
                          is_active=True)
        self.db_session.add(new_convo)
        self.db_session.commit()
        self.db_session.refresh(new_convo)
        return new_convo

    def get_convo(self, convo_id: int) -> Type[schemas.Convo]:
        """Fetch single Convo object from the database."""
        convo = self.db_session.query(Convo).filter_by(
            id=convo_id).first()
        return convo

    # TODO update convo? (only the title obviously)

    def delete_convo(self, convo_id: int):
        """Delete the Convo"""
        self.db_session.delete(self.get_convo(convo_id))
        self.db_session.commit()

    def get_all_qa_pairs(self, convo_id: int):
        qa_pairs = self.db_session.query(QAPair) \
            .filter(QAPair.convo_id == literal(convo_id)).all()
        # they seem sorted anyway, this is a temporary safeguard
        qa_pairs = sorted(qa_pairs, key=lambda x: x.id)
        return qa_pairs

    def create_qa_pair(self, convo_id: int, query: str):
        """
        Initialise a QA pair by storing just the query first.
        !!! (No, upd) Return: id of the initialised qa_pair after the commit
        Return: the QAPair object, which after the commit will have its id
        """
        timestamp = datetime.now()
        new_qa = QAPair(query=query, convo_id=convo_id, timestamp=timestamp)
        self.db_session.add(new_qa)
        self.db_session.commit()
        self.db_session.refresh(new_qa)
        return new_qa

    def get_qa_pair(self, qa_pair_id: int):
        """Fetch a single qa_pair, not used by the App, just by 'delete'."""
        qa_pair = self.db_session.query(QAPair).filter_by(
            id=qa_pair_id).first()
        return qa_pair

    def update_qa_pair(self, qa_pair: schemas.QAPair):
        """Update QAPair. Sometimes the .response will be a string, sometimes
        None."""
        self.db_session.query(QAPair).filter_by(id=qa_pair.id).update({
            'response': qa_pair.response,
            'query': qa_pair.query,
            # 'timestamp': qa_pair.timestamp
        })
        self.db_session.commit()
        # self.db_session.refresh(qa_pair)  # do I dare? Ain't a SQLAlch obj

    def delete_qa_pair(self, qa_pair_id: int):
        """Delete QAPair."""
        self.db_session.delete(self.get_qa_pair(qa_pair_id))
        self.db_session.commit()

    def get_all_chunks(self):
        """Retrieve all chunks"""
        chunks = self.db_session.query(Chunk).all()
        return chunks

    def get_chunks_count(self):
        """Get the total len of all chunks"""
        return len(self.get_all_chunks())

    def create_chunk(self, text: str):
        """Store new chunk"""
        new_chunk = Chunk(text=text)
        self.db_session.add(new_chunk)
        self.db_session.commit()
        self.db_session.refresh(new_chunk)
        return new_chunk

    def get_chunk(self, chunk_id: int):
        """Fetch single SQLite-stored Chunk from the database."""
        chunk = self.db_session.query(Chunk).filter_by(
            id=chunk_id).one()
        return chunk

    def delete_chunk(self, chunk_id: int):
        """Remove a Chunk from the SQLite database"""
        self.db_session.delete(self.get_chunk(chunk_id))
        self.db_session.commit()

    # def delete_movie(self, user_id: int, movie_id: int):
    #     """Remove the user-movie relationship entry, remove movie entry"""
    #     relationship_to_del = self.db_session.query(UserMovie). \
    #         filter(UserMovie.user_id == user_id,
    #                UserMovie.movie_id == movie_id).one()
    #     movie_to_del = self.db_session.query(Movie) \
    #         .filter(Movie.id == literal(movie_id)).one()
    #     self.db_session.delete(relationship_to_del)
    #     self.db_session.delete(movie_to_del)
    #     self.db_session.commit()
    #     print(f"Movie with id <{movie_id}> successfully deleted.")
