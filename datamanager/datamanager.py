"""
Docstring
"""

from typing import Type, List, cast, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import literal, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from datamanager.models import Base, User, Convo, QAPair, Doc, Chunk, DocChunk
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

    def get_all_docs(self):
        """Retrieve all Docs"""
        docs = self.db_session.query(Doc).all()
        return docs

    def create_doc(self, title: str):
        """Store new Doc"""
        new_doc = Doc(title=title)
        self.db_session.add(new_doc)
        self.db_session.commit()
        self.db_session.refresh(new_doc)
        return new_doc

    def get_doc(self, doc_id: int):
        """Fetch single SQLite-stored Doc from the database."""
        doc = self.db_session.query(Doc).filter_by(
            id=doc_id).one()
        return doc

    def delete_doc(self, doc_id: int):
        """
        Remove a Doc from the SQLite database.
        But remove all related chunks and records of relation first.
        This is a conscious design oddity compared to the rest of the methods.
        NOTE: Though not necessary or more readable, it communicates that we
        never want to delete a doc and leave chunks floating about.
        """
        doc_chunks = self.get_all_doc_chunks(doc_id)
        for chunk in doc_chunks:
            self.delete_doc_chunk(doc_id, chunk.id)
            self.delete_chunk(chunk.id)
        self.db_session.delete(self.get_doc(doc_id))
        self.db_session.commit()

    def get_all_doc_chunks(self, doc_id: int):
        """Fetch all Chunk objects that match doc_id in the junction.
        We consult (!) DocChunk in order to fetch a [] of all Chunk (!)
        objects which are also registered in the junction table. Then we
        filter that joined list for doc_id matches."""
        doc_chunks_list = self.db_session.query(Chunk) \
            .join(DocChunk, Chunk.id == DocChunk.chunk_id) \
            .filter(DocChunk.doc_id == literal(doc_id)) \
            .all()
        return doc_chunks_list

    def create_doc_chunk(self, doc_id: int, chunk_id: int):
        """Add a new relation of a doc to a chunk"""
        new_relationship = DocChunk(doc_id=doc_id, chunk_id=chunk_id)
        self.db_session.add(new_relationship)
        self.db_session.commit()
        return new_relationship

    def delete_doc_chunk(self, doc_id: int, chunk_id: int):
        """Delete a relation of a doc to a chunk."""
        doc_chunk_to_delete = self.db_session.query(DocChunk) \
            .filter_by(doc_id=doc_id, chunk_id=chunk_id).first()
        self.db_session.delete(doc_chunk_to_delete)
        self.db_session.commit()

    def get_all_chunks(self):
        """Retrieve all chunks"""
        chunks = self.db_session.query(Chunk).all()
        return chunks

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

    def get_chunks_count(self):
        """Get the total len of all chunks"""
        return len(self.get_all_chunks())

    def delete_chunk(self, chunk_id: int):
        """Remove a Chunk from the SQLite database"""
        self.db_session.delete(self.get_chunk(chunk_id))
        self.db_session.commit()
