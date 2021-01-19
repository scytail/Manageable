from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.query import Query
from Code.Data.DataModel import engine, UserTable, WarningTable
from Code.Base.Decorator import Decorator

SessionObject = sessionmaker(bind=engine)


class DatabaseMethod(Decorator):
    """A decorator class to abstract away session management from the data layer.

    By declaring the method with this class decorator, it will determine whether or not it needs to generate a new
    session or whether one has already been generated and passed in. It will then take the session (either the new one
    or the passed in one), and place it in the method's keyword args as the named argument `session`.

    This session instance can be utilized by the contained method by accessing the keyword args and grabbing the
    `session` key:
    ```
    @DatabaseMethod
    def example_method(some, args, **kwargs):
        session = kwargs['session']
        # utilize session here
    ```

    Further, this session object can be safely passed to sub-methods as well, where it will be automatically utilized,
    by setting the sub-method's keyword args with a `session` key:
    ```
    @DatabaseMethod
    def parent_method(some, args, **kwargs):
        s = kwargs['session']

        sub_method(session=s)

    @DatabaseMethod
    def sub_method(**kwargs):
        s = kwargs['session']
        # session operations performed here will be on the same session as the parent method
    ```

    The session will then only do an automatic commit and close when the parent method is called.

    Class Variables
    ---------------
    session:    sqlalchemy.orm.Session  A Session class object that can be used for session initialization of a session.

    Methods
    -------
    run     Overrides the base class method to handle session operations.
    """

    session = SessionObject()

    def run(self, *args, **kwargs):
        """Overrides the base class method to handle session operations.

        The method will create a session if one is not already found in the method's keyword arguments. After the
        decorated method is complete, this method will handle committing (or rolling back on fail) and closing the
        session, unless the session was passed in externally.

        Parameters
        ----------
        args:   list    The argument list of the contained method.
        kwargs: dict    The keyword argument list of the contained method.

        Returns
        -------
        object  The data that the contained method returned.
        """

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
        except Exception as N:
            # Error occurred at some point, roll back the database and throw an error
            if not external_session:
                session.rollback()
            raise
        finally:
            if not external_session:
                session.close()

        return return_data


def _get_session(kwargs: dict) -> Session:
    """Gets the session from the dictionary provided.

    Parameters
    ----------
    kwargs: dict    The dictionary to grab the session instance from.

    Returns
    -------
    sqlalchemy.orm.Session  The session instance stored in the dictionary.
    """

    return kwargs['session']


@DatabaseMethod
def find_user_id_by_discord_id(discord_id: int, **kwargs) -> int:
    """Finds the database's user id in the database by the unique discord id. If it can't be found, it will add a new
    row to the database

    Parameters
    ----------
    discord_id: int     The discord id to search for
    kwargs:     dict    Keyword arguments for the method, must include a `session` argument.

    Returns
    -------
    int     The database's user id key.
    """

    session = _get_session(kwargs)

    user_row = session.query(UserTable).filter(UserTable.Discord_Id == discord_id).first()

    if user_row is None:
        return add_user(discord_id, session=session)
    else:
        return user_row.User_Id


@DatabaseMethod
def add_user(discord_id: int, **kwargs) -> int:
    """Adds a user to the database.

    Parameters
    ----------
    discord_id: int     The unique discord id to add to the database.
    kwargs:     dict    Keyword arguments for the method, must include a `session` argument.

    Returns
    -------
    int     The user id primary key in the database.
    """

    session = _get_session(kwargs)

    new_user = UserTable(Discord_Id=discord_id)
    session.add(new_user)

    session.flush()

    return session.query(UserTable).filter(UserTable.Discord_Id == discord_id).first().User_Id


@DatabaseMethod
def lookup_warnings_by_discord_id(discord_id: int, **kwargs) -> Query:
    """Find all the warning database rows for the given discord id.

    Parameters
    ----------
    discord_id: int     The unique discord id to look for in the database.
    kwargs:     dict    Keyword arguments for the method, must include a `session` argument.

    Returns
    -------
    sqlalchemy.orm.query.Query  A query object containing all the warning table rows related to the provided ID.
    """

    session = _get_session(kwargs)

    warning_rows = session.query(WarningTable). \
        select_from(UserTable). \
        outerjoin(UserTable.Warnings). \
        filter(UserTable.Discord_Id == discord_id)

    return warning_rows


@DatabaseMethod
def lookup_warning_by_warning_id(warning_id: int, **kwargs) -> Query:
    session = _get_session(kwargs)

    warning_row = session.query(WarningTable). \
        select_from(WarningTable). \
        filter(WarningTable.Warning_Id == warning_id).first()

    return warning_row


@DatabaseMethod
def add_warning(user_id: int, **kwargs) -> int:
    """

    Parameters
    ----------
    user_id:    int     The user table primary key related to the discord member to add a warning to.
    kwargs:     dict    Keyword arguments for the method, must include a `session` argument.

    Returns
    -------
    int     The warning table primary ID of the warning we just added.
    """

    session = _get_session(kwargs)

    new_warning = WarningTable(User_Id=user_id, Warning_Stamp=datetime.now())
    session.add(new_warning)

    session.flush()

    return session.query(WarningTable). \
        filter(WarningTable.User_Id == user_id). \
        order_by(WarningTable.Warning_Stamp.desc()).first().Warning_Id


@DatabaseMethod
def delete_warning_by_discord_id(discord_id: int, remove_newest: bool = False, **kwargs):
    """Deletes a warning from the specified discord member.

    Parameters
    ----------
    discord_id:     int     The unique Discord ID of the user to delete a warning from
    remove_newest:  bool    Toggles whether to remove the newest warning, rather than the oldest (defaults to False)
    kwargs:         dict    Keyword arguments for the method, must include a `session` argument.
    """

    session = _get_session(kwargs)

    warning_list = lookup_warnings_by_discord_id(discord_id, session=session)

    if remove_newest:
        warning_to_remove = warning_list.order_by(WarningTable.Warning_Stamp.desc()).first()
    else:
        warning_to_remove = warning_list.order_by(WarningTable.Warning_Stamp.asc()).first()

    if warning_to_remove is not None:
        session.delete(warning_to_remove)


@DatabaseMethod
def delete_warning(warning_id: int, **kwargs):
    """Deletes a warning with the specified warning ID

    Parameters
    ----------
    warning_id:     int     The unique warning ID to delete
    kwargs:         dict    Keyword arguments for the method, must include a `session` argument.
    """

    session = _get_session(kwargs)

    warning_to_remove = lookup_warning_by_warning_id(warning_id, session=session)

    if warning_to_remove is not None:
        session.delete(warning_to_remove)
