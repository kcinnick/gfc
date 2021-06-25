from sqlalchemy import Column, Date, ForeignKey, Integer, MetaData, Table, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
metadata = MetaData()


class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True)
    text = Column(Text, unique=True)
    date = Column(Date)
    claimant_id = Column(Integer, ForeignKey("claimants.id"))
    claimant = relationship("Claimant")

    def __str__(self):
        return f"{self.text}"

    def __repr__(self):
        return f"{self.text}"


class Claimant(Base):
    __tablename__ = "claimants"
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)

    def __str__(self):
        return f"{self.name}"


claims = Table(
    "claims", metadata,
    Column('id', Integer, primary_key=True),
    Column('text', Text, unique=True),
    Column('date', Date),
    Column('claimant_id', Integer, ForeignKey('claimants.id')),
)

claimants = Table(
    "claimants", metadata,
    Column('id', Integer, primary_key=True),
    Column('name', Text, unique=True)
)
