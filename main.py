import os

import requests

API_KEY = os.getenv('API_KEY')
if API_KEY is None:
    raise EnvironmentError(
        'Need API_KEY to be set to valid Google Fact Check Tools API key.\n'
    )

r = requests.get(
    f'https://content-factchecktools.googleapis.com/v1alpha1/claims:search?pageSize=10&query=biden&maxAgeDays=30&offset=0&languageCode=en-US&key={API_KEY}',
    headers={
        'x-referer': 'https://explorer.apis.google.com',
    }
)

print(r.json())
