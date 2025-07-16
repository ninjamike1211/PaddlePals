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

def convert_response(response:requests.Response):
    response_str = response.content.decode('utf-8')
    return json.loads(response_str)


def test_login_root(tmp_path):
    with setup_server(tmp_path):
        # Attempt login with incorrect password
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'wrongPassword'})
        assert response.status_code == 401

        # Attempt login with correct password
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'admin', 'password':'root'})
        assert response.status_code == 200
        response_dict = convert_response(response)
        assert response_dict['success'] == True
        assert response_dict['apiKey']

def test_create_user(tmp_path):
    with setup_server(tmp_path):
        # Test invalid passwords
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'tooShort'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'123password123'})
        assert response.status_code == 400

        # Test invalid usernames
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'test', 'password':'bui9b20asdfh0'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'admin', 'password':'bui9b20asdfh0'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'deleted_user', 'password':'bui9b20asdfh0'})
        assert response.status_code == 400

        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'unknown_user', 'password':'bui9b20asdfh0'})
        assert response.status_code == 400

        # Create valid user
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'bui9b20asdfh0'})
        assert response.status_code == 200

        # Authenticate user
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'testUser', 'password':'bui9b20asdfh0'})
        response_dict = convert_response(response)
        assert response_dict['success'] == True
        assert response_dict['apiKey']

        # Attempt to create duplicate user
        response = requests.post("http://localhost:8080/pickle/user/create", json={'username':'testUser', 'password':'different_pass'})
        assert response.status_code == 403

def test_friends(tmp_path):
    with setup_server(tmp_path, users={'userA':'testingPassA', 'userB':'testingPassB', 'userC':'testingPassC'}):
        # log in with userA
        response = requests.post("http://localhost:8080/pickle/user/auth", json={'username':'userA', 'password':'testingPassA'})
        assert response.status_code == 200
        apiKey = convert_response(response)['apiKey']

        # Verify userA can't access users B/C
        response = requests.post("http://localhost:8080/pickle/user/id", json={'username':'userB'}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403
        response = requests.post("http://localhost:8080/pickle/user/id", json={'username':'userC'}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403

        # Verify no friends
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert convert_response(response) == {}

        # Befriend userB
        response = requests.post("http://localhost:8080/pickle/user/addFriend", json={'user_id':1, 'friend_username':'userB'}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert convert_response(response) == {'2':{'username':'userB', 'gamesPlayed':0, 'winRate':None}}

        # Check that we can access userB
        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':2, 'objects':['username']}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert convert_response(response) == {'2':{'username':'userB'}}

        # Check that we still can't access userC
        response = requests.post("http://localhost:8080/pickle/user/get", json={'user_id':3, 'objects':['username']}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403

        # Befriend userC
        response = requests.post("http://localhost:8080/pickle/user/addFriend", json={'user_id':1, 'friend_id':3}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert convert_response(response) == {'2':{'username':'userB', 'gamesPlayed':0, 'winRate':None}, '3':{'username':'userC', 'gamesPlayed':0, 'winRate':None}}

        # Remove userB
        response = requests.post("http://localhost:8080/pickle/user/removeFriend", json={'user_id':1, 'friend_id':2}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        response = requests.post("http://localhost:8080/pickle/user/friends", json={'user_id':1}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 200
        assert convert_response(response) == {'3':{'username':'userC', 'gamesPlayed':0, 'winRate':None}}

        # Verify we can no longer access userB
        response = requests.post("http://localhost:8080/pickle/user/id", json={'username':'userB'}, headers={'Authorization':f'Bearer {apiKey}'})
        assert response.status_code == 403
        

def test_coffee(tmp_path):
    with setup_server(tmp_path):
        # Check if server can brew coffee
        response = requests.post("http://localhost:8080/pickle/coffee", json={})
        assert response.status_code == 418