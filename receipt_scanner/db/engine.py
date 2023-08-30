from contextlib import contextmanager

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session, sessionmaker


class DBConnectionFactory:
    @classmethod
    def get_engine(cls, db_uri):
        """Create and return a db engine using the config"""
        return create_engine(
            db_uri,
            pool_pre_ping=True,
            execution_options={},
        )

    @classmethod
    def get_sessionmaker(cls, engine):
        """Return a sessionmaker object"""
        return sessionmaker(bind=engine, class_=Session, autoflush=False, future=True)

    @classmethod
    @contextmanager
    def connection(cls, db_uri):
        engine = cls.get_engine(db_uri)
        sess_maker = cls.get_sessionmaker(engine)
        yield sess_maker
        sess_maker.close_all()
