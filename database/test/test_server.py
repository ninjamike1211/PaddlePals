import time
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
    with setup_server(tmp_path, users={'testUserA':'t3stUserP@ssA', 'testUserB':'t3stUserP@ssB'}) as server:

        # Verify we can't access without authentication
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':1})
        assert response.status_code == 401
        assert 'Authentication required, please obtain an API key through pickle/user/auth' in response.text

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2})
        assert response.status_code == 401
        assert 'Authentication required, please obtain an API key through pickle/user/auth' in response.text

        # Set api token timeout for later testing
        server.api.API_KEY_TIMEOUT = 1 * 60

        # Get api tokens for all users
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'root'})
        root_key = response.json()['apiKey']
        root_renew = response.json()['renewalKey']

        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'testUserA', 'password':'t3stUserP@ssA'})
        userA_key = response.json()['apiKey']
        userA_renew = response.json()['renewalKey']

        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'testUserB', 'password':'t3stUserP@ssB'})
        userB_key = response.json()['apiKey']
        userB_renew = response.json()['renewalKey']

        # Record timestamp after last api key is registered
        before_time = time.time()

        # Check user view permissions
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {root_key}'})
        assert response.status_code == 200
        assert all(i in response.json() for i in ('1', '2'))

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':1}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200
        assert '1' in response.json()

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 403

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':1}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 403

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 200
        assert '2' in response.json()

        # Make users friends, check view permissions
        response = requests.post("http://localhost:8080/pickle/user/addFriend", json={'user_id':1, 'friend_id':2}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 200
        assert all(i in response.json() for i in ('1', '2'))

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 200
        assert all(i in response.json() for i in ('1', '2'))

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

        # Wait for timeout
        time.sleep(time.time() - before_time + server.api.API_KEY_TIMEOUT)

        # Check that all keys are expired
        response = requests.post("http://localhost:8080/pickle/user/id", json={'username':'newTestUserB'}, headers={'Authorization':f'Bearer {root_key}'})
        assert response.status_code == 498
        
        response = requests.post("http://localhost:8080/pickle/user/id", json={'username':'newTestUserB'}, headers={'Authorization':f'Bearer {userA_key}'})
        assert response.status_code == 498

        response = requests.post("http://localhost:8080/pickle/user/id", json={'username':'newTestUserB'}, headers={'Authorization':f'Bearer {userB_key}'})
        assert response.status_code == 498

        # Renew all keys
        response = requests.post("http://localhost:8080/pickle/user/auth_renew", json={'apiKey':root_key, 'renewalKey':root_renew})
        assert response.status_code == 200
        new_root_key = response.json()['apiKey']
        new_root_renew = response.json()['renewalKey']
        assert root_key != new_root_key
        assert root_renew != new_root_renew
        
        response = requests.post("http://localhost:8080/pickle/user/auth_renew", json={'apiKey':userA_key, 'renewalKey':userA_renew})
        assert response.status_code == 200
        new_userA_key = response.json()['apiKey']
        new_userA_renew = response.json()['renewalKey']
        assert userA_key != new_userA_key
        assert userA_renew != new_userA_renew

        response = requests.post("http://localhost:8080/pickle/user/auth_renew", json={'apiKey':userB_key, 'renewalKey':userB_renew})
        assert response.status_code == 200
        new_userB_key = response.json()['apiKey']
        new_userB_renew = response.json()['renewalKey']
        assert userB_key != new_userB_key
        assert userB_renew != new_userB_renew

        # Check that new keys work
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':[1,2]}, headers={'Authorization':f'Bearer {new_root_key}'})
        assert response.status_code == 200
        assert all(i in response.json() for i in ('1', '2'))

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':1}, headers={'Authorization':f'Bearer {new_userA_key}'})
        assert response.status_code == 200
        assert '1' in response.json()

        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2}, headers={'Authorization':f'Bearer {new_userB_key}'})
        assert response.status_code == 200
        assert '2' in response.json()
