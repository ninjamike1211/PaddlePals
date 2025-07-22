import pytest
import requests
import json

from database import database_setup
from database import database_server
from database.database_api import restAPI

def setup_server(tmp_path, users=None, auth=True):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    api = restAPI(db_path, useAuth=auth)
    return database_server.PickleServer(api, 8080)


def test_bad_json(tmp_path):
    with setup_server(tmp_path):
        # verify invalid json is caught by server
        response = requests.post("http://localhost:8080/pickle/user/auth", data=b'{{asdf:65,}')
        assert response.status_code == 400
        assert 'Error, improperly formatted JSON:' in response.text

def test_bad_data_type(tmp_path):
    with setup_server(tmp_path, auth=False):
        # Verify invalid data type is reported by server
        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':'asdjfij', 'username':'asdfhe'})
        assert response.status_code == 400
        assert 'Type Error:' in response.text

def test_bad_url(tmp_path):
    with setup_server(tmp_path, auth=False):
        # Verify base endpoint must be pickle/
        response = requests.post("http://localhost:8080/notPickle", json={})
        assert response.status_code == 404
        assert 'Base endpoint must be "pickle/"' in response.text

        # Check invalid endpoints
        response = requests.post("http://localhost:8080/pickle/notAnEndpoint", json={})
        assert response.status_code == 404
        assert 'Endpoint not found:' in response.text

        response = requests.post("http://localhost:8080/pickle/user/notAnEndpoint", json={})
        assert response.status_code == 404
        assert 'Endpoint not found:' in response.text

def test_auth(tmp_path):
    with setup_server(tmp_path, users={'testUserA':'t3stUserP@ssA', 'testUserB':'t3stUserP@ssB'}):
        # Verify we can't access without authentication
        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':1})
        assert response.status_code == 401
        assert 'Authentication required, please obtain an API key through pickle/user/auth' in response.text

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':2})
        assert response.status_code == 401
        assert 'Authentication required, please obtain an API key through pickle/user/auth' in response.text

        # Get api tokens for all users
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'root'})
        root_key = response.json()['apiKey']

        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'testUserA', 'password':'t3stUserP@ssA'})
        userA_key = response.json()['apiKey']

        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'testUserB', 'password':'t3stUserP@ssB'})
        userB_key = response.json()['apiKey']

        # Check user view permissions
        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {root_key}'})
        assert response.status_code == 200
        assert all(i in response.json().keys() for i in ('1', '2'))

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':1}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200
        assert '1' in response.json().keys()

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':2}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 403

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':1}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 403

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':2}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 200
        assert '2' in response.json().keys()

        # Make users friends, check view permissions
        response = requests.post("http://localhost:8080/pickle/user/addFriend", json={'user_id':1, 'friend_id':2}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200
        assert all(i in response.json().keys() for i in ('1', '2'))

        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 200
        assert all(i in response.json().keys() for i in ('1', '2'))

        # Check edit permissions
        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':1, 'username':'newUserA'}, headers={'Authorization':f'Bearer {root_key}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':2, 'username':'newUserB'}, headers={'Authorization':f'Bearer {root_key}'})
        assert response.status_code == 200

        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':1, 'username':'newTestUserA'}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200

        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':2, 'username':'userB'}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 403

        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':1, 'username':'userA'}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 403

        response = requests.post("http://localhost:8080/pickle/user/set", json={'user_id':2, 'username':'newTestUserB'}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 200