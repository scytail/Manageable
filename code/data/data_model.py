"""The data model for the database used by manageable."""

from sqlalchemy import create_engine, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase

engine = create_engine('sqlite:///data/database.db')


# pylint: disable-msg=R0903
class _Base(DeclarativeBase):
    """The base class implementation for data models."""


# pylint: disable-msg=R0903
class UserTable(_Base):
    """The table of Discord users."""
    __tablename__ = 'Users'

    User_Id = Column('User_Id', Integer, primary_key=True, nullable=False)
    Discord_Id = Column('Discord_Id', Integer, unique=True, nullable=False)
    Warnings = relationship('WarningTable', back_populates='User')
    Cookie = relationship('CookieTable', back_populates='User')


# pylint: disable-msg=R0903
class WarningTable(_Base):
    """The table of Discord user warnings."""
    __tablename__ = 'Warnings'

    Warning_Id = Column('Warning_Id',
                        Integer,
                        primary_key=True,
                        nullable=False)
    User_Id = Column('User_Id',
                     Integer,
                     ForeignKey('Users.User_Id'),
                     nullable=False)
    Warning_Stamp = Column('Warning_Stamp', DateTime, nullable=False)
    User = relationship('UserTable', back_populates='Warnings')


# pylint: disable-msg=R0903
class CookieTable(_Base):
    """The table of Discord user cookie hunt data."""
    __tablename__ = 'Cookies'

    User_Id = Column('User_Id',
                     Integer,
                     ForeignKey('Users.User_Id'),
                     primary_key=True,
                     nullable=False)
    Cookie_Count = Column('Cookie_Count', Integer, nullable=False)
    User = relationship('UserTable', back_populates='Cookie')


_Base.metadata.create_all(engine)
