import datetime
import os

from main import get_api_key, search_query, process_claim, create_db_session


def test_get_api_key():
    API_KEY = get_api_key()
    assert API_KEY == os.getenv("API_KEY")


def test_search_query():
    API_KEY = os.getenv("API_KEY")
    claims = search_query(API_KEY)
    assert type(claims) == list
    assert len(claims) == 10


def test_process_claims():
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
    session = create_db_session()
    processed_claim = process_claim(example_claim, session)
    assert processed_claim.text == 'An image shows President Joe Biden sleeping at G-7 summit'
    assert processed_claim.date == datetime.date(2021, 6, 16)
    assert processed_claim.claimant.name == 'Social media users'
