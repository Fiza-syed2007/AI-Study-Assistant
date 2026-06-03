from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class History(Base):

    __tablename__ = "history"

    id = Column(Integer, primary_key=True)

    user_input = Column(String)

    output = Column(String)

    feature = Column(String)