import pytest
import requests
import json

from database import database_setup
from database import database_server
from database.database_api import restAPI

def setup_server(tmp_path, users=None, auth=False):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    api = restAPI(db_path, useAuth=auth)
    return database_server.PickleServer(api, 8080)

def test_login_root(tmp_path):
    server = setup_server(tmp_path, auth=True)

    with server:
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'root'})
        assert response.status_code == 200

        response_str = response.content.decode('utf-8')
        response_dict = json.loads(response_str)
        assert response_dict['success'] == True
        assert response_dict['apiKey']

def test_coffee(tmp_path):
    server = setup_server(tmp_path)

    with server:
        response = requests.post("http://localhost:8080/pickle/coffee", json={})
        assert response.status_code == 418