from sqlalchemy import create_engine, Column, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///Data/database.db')
_Base = declarative_base(bind=engine)


class UserTable(_Base):
    __tablename__ = 'Users'

    User_Id = Column('User_Id', Integer, primary_key=True, nullable=False)
    Discord_Id = Column('Discord_Id', Integer, unique=True, nullable=False)


class WarningTable(_Base):
    __tablename__ = 'Warnings'

    Warning_Id = Column('Warning_Id', Integer, primary_key=True, nullable=False)
    User_Id = Column('User_Id', Integer, ForeignKey('Users'), nullable=False)
    Warning_Stamp = Column('Warning_Stamp', DateTime, nullable=False)


_Base.metadata.create_all()
