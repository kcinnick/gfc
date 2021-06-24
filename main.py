import os
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

from models import Claimant, Claim

# TODO: create shell script for auto-creating DBs
engine = create_engine(
    f"postgresql+psycopg2://postgres:" +
    f"{os.getenv('POSTGRES_PASSWORD')}@127.0.0.1" +
    f":5432/gfc", poolclass=NullPool
)
Session = sessionmaker(bind=engine)
session = Session()


def get_api_key():
    API_KEY = os.getenv('API_KEY')
    if API_KEY is None:
        raise EnvironmentError(
            'Need API_KEY to be set to valid Google Fact Check Tools API key.\n'
        )

    return API_KEY


def process_claim(claim):
    claimant = Claimant(
        name=claim['claimant']
    )
    session.add(claimant)
    try:
        session.commit()
    except IntegrityError:
        print(f'Claimant "{claimant.name}" is already in the database.')
        session.rollback()
        claimant = session.query(Claimant).where(Claimant.name == claimant.name).first()

    claim = Claim(
        text=claim['text'],
        date=claim['claimDate'],
        claimant_id=claimant.id,
    )
    session.add(claim)
    try:
        session.commit()
    except IntegrityError:
        print(f'Claim "{claim.text}" is already in the database.')
        session.rollback()


def search_query(API_KEY):
    url =  (f'https://content-factchecktools.googleapis.com/v1alpha1/claims:search?' +
        f'pageSize=10&'
        f'query=biden&'
        f'maxAgeDays=30&'
        f'offset=0&languageCode=en-US&key={API_KEY}')
    r = requests.get(
       url,
        headers={
            'x-referer': 'https://explorer.apis.google.com',
        }
    )
    data = r.json()
    next_page_token = data.pop('nextPageToken')
    claims = data.pop('claims')
    #  process claims
    for claim in claims:
        process_claim(claim)


def main():
    API_KEY = get_api_key()
    search_query(API_KEY=API_KEY)


if __name__ == '__main__':
    main()
