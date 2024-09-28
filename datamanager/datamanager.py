"""
For better or for worse, I've come to the following conclusion:
I should define the models in the same file where I'm creating and binding
the engine. I'm sure some basic importing can make Base accessible elsewhere,
however I decided to keep things simple and focus on achieving better control
of sqlalchemy.orm rather than of the python importing game.

Furthermore, I'm choosing to work with strings as arguments of most methods,
in order to cut out the necessity for any additional layers of control.
"""

from typing import Type, List, cast
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Time, literal
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import relationship, backref

SQL_FILEPATH = 'sqlite:///data/chatbot_service_db.sqlite'

# Create the database engine/connection
engine = create_engine(SQL_FILEPATH)
# Create a session factory
Session = sessionmaker(bind=engine)
# Create a base class for declarative models, the parent for tables ("classes")
Base = declarative_base()


# Define the 'users' table model
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
    The "class" (ORM) corresponds with the 'movies' table basically.
    By convention, __tablename__ should be lower-cased, plural of class name.
    Class properties in a table class map to table columns.
    """
    __tablename__ = 'convos'
    # The id assignment will automatically be done by SQLAlchemy when commit()
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(120), nullable=False)
    body = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status_active = Column(Boolean, nullable=False)


class QAPair(Base):
    """
    Docstring
    """
    __tablename__ = 'qa_pairs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    convo_id = Column(Integer, ForeignKey('convos.id'), nullable=False)
    query = Column(String, nullable=False)
    response = Column(String, nullable=True)
    timestamp = Column(Time, nullable=False)


# Create the tables (if not yet created). Must be done below 'Base' usages
Base.metadata.create_all(engine)


class SQLiteDataManager():
    def __init__(self):
        self.db_session = Session()  # Create a session instance

    def get_all_users(self) -> List[Type[User]]:
        """Return a [] of User objects"""
        return self.db_session.query(User).all()

    def get_all_convos(self) -> List[Type[Convo]]:
        """
        Useless?
        Return a [] of Convo objects
        """
        return self.db_session.query(Convo).all()

    def get_user_convos(self, user_id: int) -> List[Type[Convo]]:
        """
        Return a [] of Convo objects associated with user_id
        """
        convo_objects_list = self.db_session.query(Convo) \
            .filter(Convo.user_id == literal(user_id)) \
            .all()
        return convo_objects_list

    def add_user(self, user: str):
        new_user = User(name=user)
        self.db_session.add(new_user)
        # SQLAlchemy will now automatically generate a unique ID when commit()
        self.db_session.commit()
        print(f"User '{user}' added successfully!")

    def is_available_username(self, user: str) -> bool:
        """Return True if username (case-insensitive) not taken."""
        # .first() ensures that None is returned for no match, unlike .all()
        existing_user = self.db_session.query(User).filter_by(
            name=user).first()
        if existing_user:
            return False
        return True

    def user_id_exists(self, user_id: int) -> bool:
        """Return True if user_id present in 'users' table"""
        existing_user = self.db_session.query(User).filter_by(
            id=user_id).first()
        if existing_user:
            return True
        return False

    def init_qa_pair(self, query: str, convo_id: int) -> int:
        """
        Initialise a QA pair by storing just the query first.
        Return: id of the initialised qa_pair after the commit
        """
        timestamp = datetime.now()
        new_q = QAPair(query=query, convo_id=convo_id, timestamp=timestamp,
                       response=None)
        self.db_session.add(new_q)
        self.db_session.commit()
        return cast(int, new_q.id)

    def update_qa_pair(self, qa_pair_id: int, response: str):
        """
        Finalise or update the qa_pair by storing the response @ the id
        """
        self.db_session.query(QAPair).filter(QAPair.id == qa_pair_id).update(
            {'response': response}
        )
        self.db_session.commit()

#######################################

    def add_movie(self, name: str, director: str, year: int, rating: float,
                  poster: str) -> int:
        """Add movie to DB, return the auto-incremented movie.id"""
        new_movie = Movie(name=name, director=director, year=year,
                          rating=rating, poster=poster)
        self.db_session.add(new_movie)
        self.db_session.commit()  # this is where new_movie.id gets created
        print(f"Movie '{name}' added successfully!")
        return cast(int, new_movie.id)  # redundant cast bc PyCharm typechecks

    def add_user_movie(self, user_id: int, movie_id: int):
        """Add a new relation of a usr to a mov. The ids are sure to exist"""

        # obtain 'movie' and 'user' names
        movie_object = self.db_session.query(Movie) \
            .filter(Movie.id == movie_id) \
            .one()
        movie = movie_object.name
        user_object = self.db_session.query(User) \
            .filter(User.id == user_id) \
            .one()
        user = user_object.name

        # Verify that the relationship doesn't already exist in 'user_movies'
        existing_relationship = self.db_session.query(UserMovie).filter_by(
            user_id=user_id, movie_id=movie_id).first()
        if existing_relationship:
            print(f"User {user} already has the movie {movie}!")
            return

        # Add a new relationship entry to 'user_movies'
        new_relationship = UserMovie(user_id=user_id, movie_id=movie_id)
        self.db_session.add(new_relationship)
        self.db_session.commit()
        print(f"Movie {movie} successfully added for {user}!")

    def get_movie_from_id(self, movie_id) -> Movie:
        """Query 'movies' table for movie_id match, return Movie object"""
        mov = self.db_session.query(Movie).filter(Movie.id == movie_id).one()
        # the redundant cast necessary to appease PyCharm's typechecker
        return cast(Movie, mov)

    def get_username_from_id(self, user_id) -> String:
        """Query 'users' table for user_id match, return username"""
        user = self.db_session.query(User).filter(User.id == user_id).one()
        # the redundant cast necessary to appease PyCharm's typechecker
        return cast(String, user.name)

    @staticmethod
    def create_movie_object(movie_id: int, name: str, director: str, year: int,
                            rating: float, poster: str) -> Movie:
        """Bundle parameters into a Movie object"""
        movie = Movie(id=movie_id, name=name, director=director, year=year,
                      rating=rating, poster=poster)
        return movie

    def update_movie(self, movie: Movie):
        self.db_session.query(Movie).filter(Movie.id == movie.id).update(
            {'name': movie.name,
             'director': movie.director,
             'year': movie.year,
             'rating': movie.rating,
             'poster': movie.poster}
        )
        self.db_session.commit()

    def delete_movie(self, user_id: int, movie_id: int):
        """Remove the user-movie relationship entry, remove movie entry"""
        relationship_to_del = self.db_session.query(UserMovie). \
            filter(UserMovie.user_id == user_id,
                   UserMovie.movie_id == movie_id).one()
        movie_to_del = self.db_session.query(Movie) \
            .filter(Movie.id == literal(movie_id)).one()
        self.db_session.delete(relationship_to_del)
        self.db_session.delete(movie_to_del)
        self.db_session.commit()
        print(f"Movie with id <{movie_id}> successfully deleted.")

    def delete_user(self, user_id: int):
        """Remove user. app ensures that all related movie entries are
        deleted first."""
        user_to_del = self.db_session.query(User) \
            .filter(User.id == literal(user_id)).one()
        self.db_session.delete(user_to_del)
        self.db_session.commit()
        print(f"User with id <{user_id}> successfully deleted.")
