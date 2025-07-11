import pytest
import requests

from database import database_setup
from database import database_server
from database.database_api import restAPI

def setup(tmp_path, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    api = restAPI(db_path, useAuth=False)
    return database_server.PickleServer(api, 8080)

def test_coffee(tmp_path):
    server = setup(tmp_path)

    with server:
        response = requests.post("http://localhost:8080/pickle/coffee", json={})
        assert response.status_code == 418