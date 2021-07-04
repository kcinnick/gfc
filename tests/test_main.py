import datetime
import os
import random
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import NullPool

from main import get_api_key, search_query, process_claim, search_query_via_toolbox, create_db_session, \
    process_claim_from_toolbox, source_of_claims
from models import Claimant, Claim


class TestSearchQuery(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            'sqlite:///gfc.db', echo=False,
            poolclass=NullPool,
        )
        Base = declarative_base()
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_get_api_key(self):
        API_KEY = get_api_key()
        assert API_KEY == os.getenv("API_KEY")

    def test_search_query(self):
        API_KEY = os.getenv("API_KEY")
        query = 'Biden'

        claims = search_query(API_KEY, page_size=10, query=query, max_age=7)
        assert type(claims) == list
        assert len(claims) >= 1


class TestProcessClaims(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            'sqlite:///gfc.db', echo=False,
            poolclass=NullPool,
        )
        Base = declarative_base()
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

        self.session.add(Claimant(name='Cristian'))
        self.session.commit()

    def test_process_claims(self):
        example_claim = {
            'text': 'An image shows President Joe Biden sleeping at G-7 summit',
            'claimant': 'Social media users',
            'claimDate': '2021-06-16T00:00:00Z',
            'claimReview': [
                {'publisher': {'name': 'USA Today', 'site': 'usatoday.com'},
                 'url': 'https://www.usatoday.com/story/news/factcheck/2021/06/20/fact-check-'
                        'photo-biden-sleeping-g-7-summit-altered/7729133002/',
                 'title': 'Fact check: Image claiming to show Joe Biden sleeping at G-7 ...',
                 'reviewDate': '2021-06-20T21:41:07Z',
                 'textualRating': 'Altered',
                 'languageCode': 'en'}
            ]
        }
        processed_claim = process_claim(example_claim, self.session)
        assert processed_claim.text == 'An image shows President Joe Biden sleeping at G-7 summit'
        assert processed_claim.date == datetime.date(2021, 6, 16)
        assert processed_claim.claimant.name == 'Social media users'

    def test_add_claim_to_database(self):
        return

    def test_create_db_session(self):
        create_db_session()

    def tearDown(self):
        user = self.session.query(Claimant).where(Claimant.name == 'Cristian')
        user.delete()
        self.session.commit()
        pass


class TestToolboxQueries(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            'sqlite:///gfc.db', echo=False,
            poolclass=NullPool,
        )
        Base = declarative_base()
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_search_query_via_toolbox(self):
        claims_response = search_query_via_toolbox()
        assert len(claims_response) == 10

    def test_process_claim_from_toolbox(self):
        for claim in search_query_via_toolbox():
            process_claim_from_toolbox(claim, self.session)

    def tearDown(self) -> None:
        objects = Claim.__table__.delete()
        self.session.execute(objects)
        self.session.commit()


class TestSourceOfClaims(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            'sqlite:///gfc.db', echo=False,
            poolclass=NullPool,
        )
        Base = declarative_base()
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()
        claimant = Claimant(name='this is a claimant', id=9)
        claim = Claim(text='this is a claim', claimant_id=claimant.id)
        self.session.add(claim)
        self.session.add(claimant)
        another_claim = Claim(text='this is another claim', claimant_id=claimant.id)
        self.session.add(another_claim)
        self.session.commit()

    def test_source_of_claims(self):
        parsed_results = source_of_claims(self.session)
        self.assertIn('this is a claimant', [i.name for i in parsed_results])
        self.assertIn('this is a claimant', [i.name for i in parsed_results])

    def tearDown(self) -> None:
        objects = Claim.__table__.delete()
        self.session.execute(objects)
        self.session.commit()
        objects = Claimant.__table__.delete()
        self.session.execute(objects)
        self.session.commit()