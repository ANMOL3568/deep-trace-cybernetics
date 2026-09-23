from sqlalchemy.engine import make_url
from app.config import Settings


def test_split_database_settings_encode_password(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    config = Settings(_env_file=None, db_host='localhost', db_port=5432,
                      db_name='DeepTrace', db_user='postgres', db_password='p@ss:/?#% word')
    url = make_url(config.database_url)
    assert url.database == 'DeepTrace'
    assert url.username == 'postgres'
    assert url.password == 'p@ss:/?#% word'
    assert url.host == 'localhost' and url.port == 5432


def test_explicit_database_url_takes_precedence():
    config = Settings(_env_file=None, database_url='sqlite://', db_name='unused')
    assert config.database_url == 'sqlite://'
