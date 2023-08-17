from sqlalchemy import create_engine, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase

engine = create_engine('sqlite:///data/database.db')


class _Base(DeclarativeBase):
    pass


class UserTable(_Base):
    __tablename__ = 'Users'

    User_Id = Column('User_Id', Integer, primary_key=True, nullable=False)
    Discord_Id = Column('Discord_Id', Integer, unique=True, nullable=False)
    Warnings = relationship('WarningTable', back_populates='User')
    Cookie = relationship('CookieTable', back_populates='User')


class WarningTable(_Base):
    __tablename__ = 'Warnings'

    Warning_Id = Column('Warning_Id', Integer, primary_key=True, nullable=False)
    User_Id = Column('User_Id', Integer, ForeignKey('Users.User_Id'), nullable=False)
    Warning_Stamp = Column('Warning_Stamp', DateTime, nullable=False)
    User = relationship('UserTable', back_populates='Warnings')


class CookieTable(_Base):
    __tablename__ = 'Cookies'

    User_Id = Column('User_Id', Integer, ForeignKey('Users.User_Id'), primary_key=True, nullable=False)
    Cookie_Count = Column('Cookie_Count', Integer, nullable=False)
    User = relationship('UserTable', back_populates='Cookie')


_Base.metadata.create_all(engine)
