from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.query import Query
from Code.Data.DataModel import engine, UserTable, WarningTable
from Code.Base.Decorator import Decorator

SessionObject = sessionmaker(bind=engine)


class DatabaseMethod(Decorator):
    session = SessionObject()

    def run(self, *args, **kwargs):
        if ('session' in kwargs) and (isinstance(kwargs['session'], Session)):
            external_session = True
            session = kwargs['session']  # user manually passed in a session, so use that instead of making our own
        else:
            external_session = False
            session = SessionObject()  # Init a new sql session
            kwargs['session'] = session  # inject the session as a keyword argument into the decorated method

        try:
            return_data = super(DatabaseMethod, self).run(*args, **kwargs)  # Execute the method
            if not external_session:
                session.commit()
        except:
            # Error occurred at some point, roll back the database and throw an error
            if not external_session:
                session.rollback()
            raise
        finally:
            if not external_session:
                session.close()

        return return_data


def _get_session(kwargs: dict) -> Session:
    return kwargs['session']


@DatabaseMethod
def find_user_id_by_discord_id(discord_id: int, **kwargs) -> int:
    session = _get_session(kwargs)

    user_row = session.query(UserTable).filter(UserTable.Discord_Id == discord_id).first()

    if user_row is None:
        return add_user(discord_id, session=session)
    else:
        return user_row.User_Id


@DatabaseMethod
def add_user(discord_id: int, **kwargs) -> int:
    session = _get_session(kwargs)

    new_user = UserTable(Discord_Id=discord_id)
    session.add(new_user)

    session.flush()

    return session.query(UserTable).filter(UserTable.Discord_Id == discord_id).first().User_Id


@DatabaseMethod
def lookup_warnings_by_discord_id(discord_id: int, **kwargs) -> Query:
    session = _get_session(kwargs)

    warning_rows = session.query(WarningTable). \
        select_from(UserTable). \
        outerjoin(UserTable.Warnings). \
        filter(UserTable.Discord_Id == discord_id)

    return warning_rows


@DatabaseMethod
def add_warning(user_id: int, **kwargs) -> int:
    session = _get_session(kwargs)

    new_warning = WarningTable(User_Id=user_id, Warning_Stamp=datetime.now())
    session.add(new_warning)

    session.flush()

    return session.query(WarningTable). \
        filter(WarningTable.User_Id == user_id). \
        order_by(WarningTable.Warning_Stamp.desc()).first().Warning_Id


@DatabaseMethod
def delete_warning(discord_id: int, remove_newest: bool = False, **kwargs):
    session = _get_session(kwargs)

    warning_list = lookup_warnings_by_discord_id(discord_id, session=session)

    if remove_newest:
        warning_to_remove = warning_list.order_by(WarningTable.Warning_Stamp.desc()).first()
    else:
        warning_to_remove = warning_list.order_by(WarningTable.Warning_Stamp.asc()).first()

    session.delete(warning_to_remove)
