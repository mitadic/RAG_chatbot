"""
Docstring
"""

from typing import Type, List, cast, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import literal, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from datamanager.models import Base, User, Convo, QAPair
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


class SQLiteDataManager():
    def __init__(self):
        self.db_session = Session()  # Create a session instance

    def get_all_users(self) -> List[Type[schemas.User]]:
        """Return a [] of User objects"""
        return self.db_session.query(User).all()

    def create_user(self, user: schemas.UserCreate):
        """Register a new user"""
        new_user = User(email=user.email, pw=user.pw)
        self.db_session.add(new_user)
        # SQLAlchemy will now automatically generate a unique ID when commit()
        self.db_session.commit()
        self.db_session.refresh(new_user)  # new addition
        return new_user

    def delete_user(self, user_id: int):
        """Remove a user from the database"""
        existing_user = self.db_session.query(User).filter_by(
            id=user_id).first()
        self.db_session.delete(existing_user)
        self.db_session.commit()

    def retrieve_user(self, user_id: int) -> Optional[Type[User]]:
        """Return User if user_id present in 'users' table, else None"""
        existing_user = self.db_session.query(User).filter_by(
            id=user_id).first()
        return existing_user  # will be None if not found

    def is_available_email(self, email: str) -> bool:
        """Return True if email (case-insensitive) not taken."""
        # .first() ensures that None is returned for no match, unlike .all()
        existing_user = self.db_session.query(User).filter_by(
            email=email).first()
        if existing_user:
            return False
        return True

    def get_convos(self, user_id: int) -> List[Type[Convo]]:
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

    def load_convo(self, convo_id: int) -> Type[schemas.Convo]:
        """Fetch single Convo object from the database."""
        convo = self.db_session.query(Convo).filter_by(
            id=convo_id).first()
        return convo

    def delete_convo(self, convo_id: int):
        """Remove a convo from the database"""
        existing_convo = self.db_session.query(Convo).filter_by(
            id=convo_id).first()
        self.db_session.delete(existing_convo)
        self.db_session.commit()

    def init_qa_pair(self, convo_id: int, query: str):
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

    def update_qa_pair(self, qa_pair: schemas.QAPair):
        """Update QAPair. Sometimes the .response will be a string, sometimes
        None."""
        self.db_session.query(QAPair).filter_by(id=qa_pair.id).update({
            'response': qa_pair.response,
            'query': qa_pair.query,
            'timestamp': qa_pair.timestamp
        })
        self.db_session.commit()
        self.db_session.refresh(qa_pair)  # do I dare? Ain't an SQLAlch object

    def delete_qa_pair(self, qa_pair_id: int):
        """Delete QAPair."""
        existing_qa_pair = self.db_session.query(QAPair).filter_by(
            id=qa_pair_id).first()
        self.db_session.delete(existing_qa_pair)
        self.db_session.commit()

    def get_qa_pairs(self, convo_id: int):
        qa_pairs = self.db_session.query(QAPair) \
            .filter(QAPair.convo_id == literal(convo_id)).all()
        return qa_pairs

#######################################

    # def add_movie(self, name: str, director: str, year: int, rating: float,
    #               poster: str) -> int:
    #     """Add movie to DB, return the auto-incremented movie.id"""
    #     new_movie = Movie(name=name, director=director, year=year,
    #                       rating=rating, poster=poster)
    #     self.db_session.add(new_movie)
    #     self.db_session.commit()  # this is where new_movie.id gets created
    #     print(f"Movie '{name}' added successfully!")
    #     return cast(int, new_movie.id)  # redundant cast bc PyCharm typechecks
    #
    # def add_user_movie(self, user_id: int, movie_id: int):
    #     """Add a new relation of a usr to a mov. The ids are sure to exist"""
    #
    #     # obtain 'movie' and 'user' names
    #     movie_object = self.db_session.query(Movie) \
    #         .filter(Movie.id == movie_id) \
    #         .one()
    #     movie = movie_object.name
    #     user_object = self.db_session.query(User) \
    #         .filter(User.id == user_id) \
    #         .one()
    #     user = user_object.name
    #
    #     # Verify that the relationship doesn't already exist in 'user_movies'
    #     existing_relationship = self.db_session.query(UserMovie).filter_by(
    #         user_id=user_id, movie_id=movie_id).first()
    #     if existing_relationship:
    #         print(f"User {user} already has the movie {movie}!")
    #         return
    #
    #     # Add a new relationship entry to 'user_movies'
    #     new_relationship = UserMovie(user_id=user_id, movie_id=movie_id)
    #     self.db_session.add(new_relationship)
    #     self.db_session.commit()
    #     print(f"Movie {movie} successfully added for {user}!")
    #
    # def get_movie_from_id(self, movie_id) -> Movie:
    #     """Query 'movies' table for movie_id match, return Movie object"""
    #     mov = self.db_session.query(Movie).filter(Movie.id == movie_id).one()
    #     # the redundant cast necessary to appease PyCharm's typechecker
    #     return cast(Movie, mov)
    #
    # def get_username_from_id(self, user_id) -> String:
    #     """Query 'users' table for user_id match, return username"""
    #     user = self.db_session.query(User).filter(User.id == user_id).one()
    #     # the redundant cast necessary to appease PyCharm's typechecker
    #     return cast(String, user.name)
    #
    # @staticmethod
    # def create_movie_object(movie_id: int, name: str, director: str, year: int,
    #                         rating: float, poster: str) -> Movie:
    #     """Bundle parameters into a Movie object"""
    #     movie = Movie(id=movie_id, name=name, director=director, year=year,
    #                   rating=rating, poster=poster)
    #     return movie
    #
    # def update_movie(self, movie: Movie):
    #     self.db_session.query(Movie).filter(Movie.id == movie.id).update(
    #         {'name': movie.name,
    #          'director': movie.director,
    #          'year': movie.year,
    #          'rating': movie.rating,
    #          'poster': movie.poster}
    #     )
    #     self.db_session.commit()
    #
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
    #
    # def delete_user(self, user_id: int):
    #     """Remove user. app ensures that all related movie entries are
    #     deleted first."""
    #     user_to_del = self.db_session.query(User) \
    #         .filter(User.id == literal(user_id)).one()
    #     self.db_session.delete(user_to_del)
    #     self.db_session.commit()
    #     print(f"User with id <{user_id}> successfully deleted.")
