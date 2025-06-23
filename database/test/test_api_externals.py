from database import database_setup
from database import database_api

def setup_api(tmp_path, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    return database_api.restAPI(db_path)

def test_coffee(tmp_path):
    api = setup_api(tmp_path)

    message, code = api.handle_request('GET', '/pickle/coffee')
    assert code == 418