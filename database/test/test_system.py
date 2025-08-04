import pytest
import requests

from database import database_setup
from database import database_server
from database.database_api import restAPI

def setup_server(tmp_path, users=None, auth=True):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    api = restAPI(db_path, useAuth=auth)
    return database_server.PickleServer(api, 8080)


def test_login_root(tmp_path):
    with setup_server(tmp_path):
        # Attempt login with incorrect password
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'wrongPassword'})
        assert response.status_code == 401

        # Attempt login with correct password
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'root'})
        assert response.status_code == 200
        assert 'apiKey' in response.json()
        assert 'renewalKey' in response.json()

def test_create_user(tmp_path):
    with setup_server(tmp_path):
        # Test invalid passwords
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'tooShort'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'123password123'})
        assert response.status_code == 400

        # Test invalid usernames
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'test', 'password':'9*GTfRWQqjFFGcJS8pcK$O!M'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'admin', 'password':'9*GTfRWQqjFFGcJS8pcK$O!M'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'deleted_user', 'password':'9*GTfRWQqjFFGcJS8pcK$O!M'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'unknown_user', 'password':'9*GTfRWQqjFFGcJS8pcK$O!M'})
        assert response.status_code == 400

        # Create valid user
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'9*GTfRWQqjFFGcJS8pcK$O!M'})
        assert response.status_code == 200

        # Authenticate user
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'testUser', 'password':'9*GTfRWQqjFFGcJS8pcK$O!M'})
        assert 'apiKey' in response.json()
        assert 'renewalKey' in response.json()

        # Attempt to create duplicate user
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'qUzu0pes^hs0b1EhRmfZdve5'})
        assert response.status_code == 403

def test_friends(tmp_path):
    with setup_server(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'}):
        # log in with userA
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'userA', 'password':'test_pass101A'})
        assert response.status_code == 200
        apiKey = response.json()['apiKey']

        # Verify userA can't access users B/C
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':3}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403

        # Verify no friends
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert response.json() == {}

        # Befriend userB
        response = requests.post("http://localhost:8080/pickle/user/addFriend", json={'user_id':1, 'friend_username':'userB'}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert response.json() == {'2':{'username':'userB', 'gamesPlayed':0, 'winRate':None}}

        # Check that we can access userB
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2, 'objects':['username']}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert '2' in response.json()

        # Check that we still can't access userC
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':3, 'objects':['username']}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403

        # Befriend userC
        response = requests.post("http://localhost:8080/pickle/user/addFriend", json={'user_id':1, 'friend_id':3}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert response.json() == {'2':{'username':'userB', 'gamesPlayed':0, 'winRate':None}, '3':{'username':'userC', 'gamesPlayed':0, 'winRate':None}}

        # Remove userB
        response = requests.post("http://localhost:8080/pickle/user/removeFriend", json={'user_id':1, 'friend_id':2}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert response.json() == {'3':{'username':'userC', 'gamesPlayed':0, 'winRate':None}}

        # Verify we can no longer access userB
        response = requests.post("http://localhost:8080/pickle/user/getStats", json={'user_id':2}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403
        

def test_coffee(tmp_path):
    with setup_server(tmp_path):
        # Check if server can brew coffee
        response = requests.post("http://localhost:8080/pickle/coffee", json={})
        assert response.status_code == 418