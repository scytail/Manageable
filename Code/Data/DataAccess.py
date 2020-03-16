from sqlalchemy.orm import sessionmaker
from Code.Data.DataModel import engine
from Code.Base.Decorator import Decorator


SessionObject = sessionmaker(bind=engine)


class DatabaseMethod(Decorator):
    session = SessionObject()

    def run(self, *args, **kwargs):
        session = SessionObject()  # Init a new sql session
        kwargs['session'] = session  # inject the session as a keyword argument into the decorated method
        try:
            super(DatabaseMethod, self).run(*args, **kwargs)  # Execute the method
            session.commit()
        except:
            # Error occurred at some point when running the decorated method, roll back the database and throw an error
            session.rollback()
            raise
        finally:
            session.close()
