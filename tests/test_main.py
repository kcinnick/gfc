import os

from main import get_api_key, search_query


def test_get_api_key():
    API_KEY = get_api_key()
    assert API_KEY == os.getenv('API_KEY')


def test_search_query():
    API_KEY = os.getenv('API_KEY')
    search_query(API_KEY)
