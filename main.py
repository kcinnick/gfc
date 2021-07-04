import ast
import datetime
import os
from time import sleep

import requests
from sqlalchemy import create_engine, func
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from models import Claim, Claimant, claims


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

    claimant = add_claimant_to_database(session, name)
    try:
        claim_date = datetime.datetime.strptime(claim["claimDate"][:-10], '%Y-%m-%d').date()
    except KeyError:
        claim_date = datetime.datetime.strptime(claim['claimReview'][0]["reviewDate"][:-10], '%Y-%m-%d').date()

    claim = add_claim_to_database(session, context={
        'claim_text': claim['text'],
        'claim_date': claim_date,
        'claimant': claimant
    })
    # TODO: parse claim reviews

    return claim


def search_query(API_KEY, page_size, query, max_age, language_code='en-US'):
    """

    :type API_KEY: str, Google Fact Check API key
    :type page_size: int, number of results to return per page
    :type query: str, query to be searched
    :type max_age: int, maximum age of fact check
    """
    offset = 0
    total_claims = []
    while True:
        url = (
            f"https://content-factchecktools.googleapis.com/v1alpha1/claims:search?"
            f"pageSize={page_size}&"
            f"query={query}&"
            f"maxAgeDays={max_age}&"
            f"offset={offset}&"
            f"languageCode={language_code}&"
            f"key={API_KEY}"
        )
        print('Requesting URL ', url)
        r = requests.get(url, headers={
            "x-referer": "https://explorer.apis.google.com",
        })
        data = r.json()

        if not data:
            # results have stopped being returned.
            # exit the loop and return the results for processing.
            break

        try:
            claims = data.pop("claims")
            total_claims.extend(claims)
        except KeyError:
            if data['error']['status'] == 'PERMISSION_DENIED':
                print('hit permission denied error')
                sleep(30)
                continue

        offset += 10
        if data.get('error'):
            print('There was an error:')
            print(data)
            raise InterruptedError()

        print('Total claims: ', len(total_claims))
        sleep(5)

    return total_claims


def main(page_size, query, max_age):
    API_KEY = get_api_key()
    claims = search_query(API_KEY=API_KEY, page_size=page_size, query=query, max_age=max_age)
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

    parsed_results = {}
    for result in results:
        claimant = session.query(Claimant).get(ident=result[0])
        claims_ = session.query(Claim).where(Claim.claimant_id == claimant.id).all()
        parsed_results[claimant] = dict(claims=claims_, number_of_claims=len(claims_))

    #  TODO: build claim result stuff
    return parsed_results


def search_query_via_toolbox():
    """
    The 'content-factchecktools' URL doesn't seem to support the same kind of filters
    like `recent` or `site` that the are mentioned here: https://toolbox.google.com/factcheck/about#fce-included.
    This implementation is an attempt to allow programmatic access to them
    in the same way that regular query searches can be handled.
    :return:
    """
    url = 'https://toolbox.google.com/factcheck/api/search?hl=en&num_results=10&query=list%3Arecent&force=false&offset=0'
    print('Requesting URL ', url)
    r = requests.get(url, headers={
        "x-referer": "https://explorer.apis.google.com",
    })
    raw_response = str(r.content).replace(r'\\', '').replace(' "', ' \\"').replace('" ', '\\" ').replace('""', '\"')
    processed_response = ast.literal_eval(raw_response[11:-1].replace('null', str("None")))[
        0]  # there are no other items in this list

    # it looks like index 1 is where the actual claim data is held.
    # index 0 is just a str and index 2 is a list of topics
    claims_response = processed_response[1]
    topics = processed_response[2]  # need to find out what this actually is

    return claims_response


def add_claimant_to_database(session, name):
    claimant = Claimant(name=name)
    session.add(claimant)
    try:
        session.commit()
        print(f'Claimant "{claimant.name}" has been added to the database.')
    except IntegrityError:
        print(f'Claimant "{claimant.name}" is already in the database.')
        session.rollback()

    claimant = session.query(Claimant).where(Claimant.name == claimant.name).first()
    return claimant


def add_claim_to_database(session, context):
    claim = Claim(
        text=context['claim_text'],
        date=context['claim_date'],
        claimant=context['claimant'],
    )
    session.add(claim)
    try:
        session.commit()
        print(f'Claim "{claim.text}" has been added to the database.')
    except IntegrityError:
        print(f'Claim "{claim.text}" is already in the database.')
        session.rollback()
    except StatementError:
        session.rollback()
        year, day, month = context['claim_date'].split('-')
        context['claim_date'] = datetime.date(int(year), int(day), int(month))
        claim = Claim(
            text=context['claim_text'],
            date=context['claim_date'],
            claimant=context['claimant'],
        )
        session.add(claim)

    return claim


def process_claim_from_toolbox(claim_toolbox_object, session):
    claim_data = claim_toolbox_object[0]
    claim_text = claim_data.pop(0)
    name = claim_data.pop(0)[0]
    claim_date = claim_data.pop(0)  # this is a UNIX timestamp of the claim date
    try:
        claim_date = datetime.datetime.utcfromtimestamp(claim_date).strftime("%Y-%m-%d")
    except TypeError:
        claim_date = None
    print(claim_date)
    claim_review_source_data = claim_data.pop(0)[0][0]  # TODO: address later when we actually handle claim review stuff
    if 'social media' in name.lower():
        name = 'Social media users'
    claimant = add_claimant_to_database(session, name)
    claim = add_claim_to_database(
        session, context={'claim_text': claim_text,
                          'claim_date': claim_date,
                          'claimant': claimant
                          })

    # TODO: parse claim reviews

    return


if __name__ == "__main__":
    # main(page_size=10, query='biden', max_age=14)
    session = create_db_session()
    # source_of_claims(session=session)
    claims_response = search_query_via_toolbox()
    for claim in claims_response:
        process_claim_from_toolbox(claim, session)
