import os

from sqlalchemy import Column, Integer, Text, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

engine = create_engine(
    f"postgresql+psycopg2://postgres:" +
    f"{os.getenv('POSTGRES_PASSWORD')}@127.0.0.1" +
    f":5432/gfc", poolclass=NullPool
)

Base = declarative_base()


class Claim(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    text = Column(Text, unique=True)
    date = Column(Date)
    claimant_id = Column(Integer, ForeignKey('claimants.id'))
    claimant = relationship("Claimant")


class Claimant(Base):
    __tablename__ = 'claimants'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


Base.metadata.create_all(engine)
