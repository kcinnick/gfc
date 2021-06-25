import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from models import claimants, claims

parser = argparse.ArgumentParser()
parser.add_argument(
    "--drop",
    help="drops existing tables (if any) and recreates them.",
    action="store_true"
)
args = parser.parse_args()
database_url = (f"postgresql+psycopg2://postgres:"
                + f"{os.getenv('POSTGRES_PASSWORD')}@127.0.0.1"
                + f":5432/gfc")
engine = create_engine(
    database_url,
    poolclass=NullPool,
)
Base = declarative_base()
if args.drop:
    claims.drop(engine)
    claimants.drop(engine)

claimants.create(engine)
claims.create(engine)
