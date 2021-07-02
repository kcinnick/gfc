import datetime
import os
from collections import defaultdict
from time import sleep

import requests
from sqlalchemy import create_engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from models import Claim, Claimant, claims, claimants


def create_db_session():
    engine = create_engine(
        f"postgresql+psycopg2://postgres:"
        + f"{os.getenv('POSTGRES_PASSWORD')}@127.0.0.1"
        + f":5432/gfc",
        poolclass=NullPool,
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    return session


def get_api_key():
    API_KEY = os.getenv("API_KEY")
    if API_KEY is None:
        raise EnvironmentError(
            "Need API_KEY to be set to valid Google Fact Check Tools API key.\n"
        )

    return API_KEY


def process_claim(claim, session):
    name = claim.get('claimant', 'Social media users').title()
    if 'social media' in name.lower():
        name = 'Social media users'
    try:
        claimant = Claimant(name=name)
    except KeyError:
        claimant = Claimant(name=name)
    session.add(claimant)
    try:
        session.commit()
    except IntegrityError:
        print(f'Claimant "{claimant.name}" is already in the database.')
        session.rollback()
        claimant = session.query(Claimant).where(Claimant.name == claimant.name).first()

    try:
        claim_date = datetime.datetime.strptime(claim["claimDate"][:-10], '%Y-%m-%d').date()
    except KeyError:
        claim_date = datetime.datetime.strptime(claim['claimReview'][0]["reviewDate"][:-10], '%Y-%m-%d').date()

    claim = Claim(
        text=claim["text"],
        date=claim_date,
        claimant=claimant
    )
    session.add(claim)
    try:
        session.commit()
    except IntegrityError:
        print(f'Claim "{claim.text}" is already in the database.')
        session.rollback()

    # TODO: parse claim reviews

    return claim


def search_query(API_KEY):
    offset = 0
    total_claims = []
    try:
        while True:
            url = (
                f"https://content-factchecktools.googleapis.com/v1alpha1/claims:search?"
                f"pageSize=10&"
                f"query=biden&"
                f"maxAgeDays=365&"
                f"offset={offset}&languageCode=en-US&key={API_KEY}"
            )
            print('Requesting URL ', url)
            r = requests.get(url, headers={"x-referer": "https://explorer.apis.google.com"})
            data = r.json()

            next_page_token = data.get("nextPageToken")
            print(next_page_token)
            try:
                claims = data.pop("claims")
                total_claims.extend(claims)
            except KeyError:
                print(data)
                if data['error']['status'] == 'PERMISSION_DENIED':
                    sleep(30)
                    continue
            offset += 10
            print(len(total_claims))
            sleep(5)
    except Exception as e:
        print(e)

    return total_claims


def main():
    API_KEY = get_api_key()
    claims = search_query(API_KEY=API_KEY)
    session = create_db_session()
    for claim in claims:
        process_claim(claim, session)


def source_of_claims(session):
    results = session.query(
        claims._columns['claimant_id'],  # id of claimant
        func.count(claims._columns['claimant_id'])  # number of claims claimant is responsible for
    ).group_by(
        claims._columns['claimant_id']
    ).all()  # returns tuple of claimant_id, # of instances

    parsed_results = defaultdict(list)
    for result in results:
        claimant = session.query(Claimant).get(ident=result[0])
        claims_ = session.query(Claim).where(Claim.claimant_id == claimant.id).all()
        parsed_results[claimant] = dict(claims=claims_, number_of_claims=len(claims_))

    for key, value in parsed_results.items():
        print('~~~')
        print(key)
        print(value)

    #  TODO: build claim result stuff
    return parsed_results


if __name__ == "__main__":
    main()
    session = create_db_session()
    source_of_claims(session=session)
