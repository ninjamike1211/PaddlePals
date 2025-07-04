import pytest
from database import database_setup
from database.database_api import restAPI

def setup_api(tmp_path, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    return restAPI(db_path, useAuth=False)

def test_coffee(tmp_path):
    api = setup_api(tmp_path)

    with pytest.raises(restAPI.APIError) as apiError:
        api.handle_request('/pickle/coffee', None)
    assert apiError.value.code == 418