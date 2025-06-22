from database import database_setup
from database import database_api

def setup_api(tmp_path, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    return database_api.restAPI(db_path)


def test_init(tmp_path):
    api = setup_api(tmp_path)
    assert api
    assert api.dbCon
    assert api.cursor


def test_get_admin_user(tmp_path):
    api = setup_api(tmp_path)
    
    request = api.APIRequest('GET', 'user', {'user_id':'0'})
    user, code = api.api_user(request)

    assert code == 200
    assert user == ('admin', 0, 0, 0.0)