# gfc

gfc is a Python library for working with the [Google Fact Check API](https://developers.google.com/fact-check/tools/api/).

## Installation

This package isn't on pip yet.  To use it, just clone it down and set the environment variables `API_KEY` and `POSTGRES_PASSWORD`.

## Usage

```
>>> python utils/recreate_database.py --drop
>>> python main.py
Claimant "Social media users" is already in the database.
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)