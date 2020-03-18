from sqlalchemy import create_engine, Column, Integer, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

engine = create_engine('sqlite:///Data/database.db')
_Base = declarative_base(bind=engine)


class UserTable(_Base):
    __tablename__ = 'Users'

    User_Id = Column('User_Id', Integer, primary_key=True, nullable=False)
    Discord_Id = Column('Discord_Id', Integer, unique=True, nullable=False)
    Warnings = relationship("WarningTable", back_populates="User")


class WarningTable(_Base):
    __tablename__ = 'Warnings'

    Warning_Id = Column('Warning_Id', Integer, primary_key=True, nullable=False)
    User_Id = Column('User_Id', Integer, ForeignKey('Users.User_Id'), nullable=False)
    Warning_Stamp = Column('Warning_Stamp', DateTime, nullable=False)
    User = relationship("UserTable", back_populates="Warnings")


_Base.metadata.create_all()
