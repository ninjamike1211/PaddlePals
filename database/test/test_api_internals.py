from database import database_setup
from database import database_api
import json

def setup_api(tmp_path, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    return database_api.restAPI(db_path)


def test_init(tmp_path):
    api = setup_api(tmp_path)
    assert api
    assert api.dbCon
    assert api.cursor

    # Check default user admin is the only user
    api.cursor.execute("SELECT user_id, username, valid, gamesPlayed, gamesWon, averageScore FROM users")
    users = api.cursor.fetchall()
    assert users == [(0, 'admin', 0, None, None, None)]

    # Check that games table is empty
    api.cursor.execute("SELECT COUNT(*) FROM games")
    game_count = api.cursor.fetchone()
    assert game_count == (0,)

    # Check that friends table is empty
    api.cursor.execute("SELECT COUNT(*) FROM friends")
    friend_count = api.cursor.fetchone()
    assert friend_count == (0,)


def test_user_admin(tmp_path):
    api = setup_api(tmp_path)
    
    request = api.APIRequest('GET', 'user', {'user_id':'0'})
    user, code = api.api_user(request)
    assert type(user) is str
    assert code == 404

    request = api.APIRequest('PUT', 'user', {'user_id':'0', 'username':'notAdmin'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 404

    request = api.APIRequest('DELETE', 'user', {'user_id':'0'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 404
    
    request = api.APIRequest('GET', 'user_id', {'username':'admin'})
    user, code = api.api_user_id(request)
    assert type(user) is str
    assert code == 400



def test_create_user(tmp_path):
    api = setup_api(tmp_path)

    request = api.APIRequest('POST', 'user', {'username':'createUserTest', 'password':'createUserPassword'})
    user_id, code = api.api_user(request)
    assert user_id == {'user_id':1}
    assert code == 200

    request = api.APIRequest('GET', 'user', {'user_id':1})
    user, code = api.api_user(request)
    assert user == {'username':'createUserTest', 'gamesPlayed':0, 'gamesWon':0, 'averageScore':0.0}
    assert code == 200

    request = api.APIRequest('GET', 'user_id', {'username':'createUserTest'})
    user_id, code = api.api_user_id(request)
    assert user_id == {'user_id':1}
    assert code == 200

    request = api.APIRequest('GET', 'user_auth', {'username':'createUserTest', 'password':'createUserPassword'})
    result, code = api.api_user_auth(request)
    assert result == {'success':True}
    assert code == 200


def test_create_bad_users(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass'})

    request = api.APIRequest('POST', 'user', {'username':'admin', 'password':'testPass'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 400

    request = api.APIRequest('POST', 'user', {'username':'deleted_user', 'password':'testPass'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 400

    request = api.APIRequest('POST', 'user', {'username':'testUser', 'password':'differentTestPass'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 403


def test_delete_user(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass'})

    request = api.APIRequest('GET', 'user', {'user_id':'1', 'objects':'username'})
    result, code = api.api_user(request)
    assert result == {'username':'testUser'}
    assert code == 200

    request = api.APIRequest('DELETE', 'user', {'user_id':'1'})
    result, code = api.api_user(request)
    assert result == {'success':True}
    assert code == 200

    request = api.APIRequest('GET', 'user', {'user_id':'1'})
    result, code = api.api_user(request)
    assert result == {'username':'deleted_user', 'gamesPlayed':None, 'gamesWon':None, 'averageScore':None}
    assert code == 200

    request = api.APIRequest('PUT', 'user', {'user_id':'1', 'username':'name'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 404

    request = api.APIRequest('GET', 'user_id', {'username':'testUser'})
    result, code = api.api_user_id(request)
    assert type(result) is str
    assert code == 404

    request = api.APIRequest('GET', 'user_id', {'username':'deleted_user'})
    result, code = api.api_user_id(request)
    assert type(result) is str
    assert code == 400

    request = api.APIRequest('GET', 'user_games', {'user_id':'1'})
    result, code = api.api_user_games(request)
    assert type(result) is str
    assert code == 404

    api.cursor.execute("SELECT * FROM users WHERE user_id=1")
    user = api.cursor.fetchall()
    assert user == [(1, 'deleted_user', None, None, 0, None, None, None)]


def test_modify_username(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass', 'testUser2':'electricBoogaloo'})

    request = api.APIRequest('GET', 'user', {'user_id':'1', 'objects':'username'})
    result, code = api.api_user(request)
    assert result == {'username':'testUser'}
    assert code == 200

    request = api.APIRequest('PUT', 'user', {'user_id':'1', 'username':'differentName'})
    result, code = api.api_user(request)
    assert result == {'success':True}
    assert code == 200

    request = api.APIRequest('GET', 'user', {'user_id':'1', 'objects':'username'})
    result, code = api.api_user(request)
    assert result == {'username':'differentName'}
    assert code == 200

    request = api.APIRequest('PUT', 'user', {'user_id':'1', 'username':'admin'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 400

    request = api.APIRequest('PUT', 'user', {'user_id':'1', 'username':'deleted_user'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 400

    request = api.APIRequest('PUT', 'user', {'user_id':'1', 'username':'testUser2'})
    result, code = api.api_user(request)
    assert type(result) is str
    assert code == 403

def test_post_game(tmp_path):
    api = setup_api(tmp_path, users={'userA':'passwordA', 'userB':'passwordB'})

    request = api.APIRequest('POST', 'game', {'winner_id':'1', 'loser_id':'2', 'winner_points':'11', 'loser_points':'7'})
    game_id, code = api.api_game(request)
    assert game_id == {'game_id':0}
    assert code == 200

    request = api.APIRequest('GET', 'game', {'game_id':'0'})
    game, code = api.api_game(request)
    assert game == {'game_id':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7}
    assert code == 200

    request = api.APIRequest('POST', 'game', {'winner_id':'2', 'loser_id':'1', 'winner_points':'12', 'loser_points':'10'})
    game_id, code = api.api_game(request)
    assert game_id == {'game_id':1}
    assert code == 200

    request = api.APIRequest('GET', 'game', {'game_id':'1'})
    game, code = api.api_game(request)
    assert game == {'game_id':1, 'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10}
    assert code == 200

    request = api.APIRequest('GET', 'user_games', {'user_id':'1'})
    gamesA, code = api.api_user_games(request)
    assert gamesA == {'game_ids':[0,1]}
    assert code == 200

    request = api.APIRequest('GET', 'user_games', {'user_id':'2'})
    gamesB, code = api.api_user_games(request)
    assert gamesA == {'game_ids':[0,1]}
    assert code == 200

    request = api.APIRequest('GET', 'user', {'user_id':'1', 'objects':'gamesPlayed,gamesWon,averageScore'})
    userA_data, code = api.api_user(request)
    assert userA_data == {'gamesPlayed':2, 'gamesWon':1, 'averageScore':10.5}
    assert code == 200

    request = api.APIRequest('GET', 'user', {'user_id':'2', 'objects':'gamesPlayed,gamesWon,averageScore'})
    userA_data, code = api.api_user(request)
    assert userA_data == {'gamesPlayed':2, 'gamesWon':1, 'averageScore':9.5}
    assert code == 200


def test_friends(tmp_path):
    api = setup_api(tmp_path, users={'userA':'passA', 'userB':'passB', 'userC':'passC'})

    request = api.APIRequest('GET', 'user_friends', {'user_id':'1'})
    friends, code = api.api_user_friends(request)
    assert not friends
    assert code == 200

    request = api.APIRequest('GET', 'user_friends', {'user_id':'2'})
    friends, code = api.api_user_friends(request)
    assert not friends
    assert code == 200

    request = api.APIRequest('GET', 'user_friends', {'user_id':'3'})
    friends, code = api.api_user_friends(request)
    assert not friends
    assert code == 200

    request = api.APIRequest('POST', 'user_friends', {'user_id':'1', 'friend_id':'2'})
    result, code = api.api_user_friends(request)
    assert result == {'success':True}
    assert code == 200

    request = api.APIRequest('POST', 'user_friends', {'user_id':'3', 'friend_username':'userB'})
    result, code = api.api_user_friends(request)
    assert result == {'success':True}
    assert code == 200

    request = api.APIRequest('POST', 'user_friends', {'user_id':'3', 'friend_username':'userA'})
    result, code = api.api_user_friends(request)
    assert result == {'success':True}
    assert code == 200

    request = api.APIRequest('DELETE', 'user_friends', {'user_id':'2', 'friend_id':'1'})
    result, code = api.api_user_friends(request)
    assert result == {'success':True}
    assert code == 200

    request = api.APIRequest('GET', 'user_friends', {'user_id':'1'})
    friends, code = api.api_user_friends(request)
    assert not {'user_id':2} in friends
    assert {'user_id':3} in friends
    assert code == 200

    request = api.APIRequest('GET', 'user_friends', {'user_id':'2'})
    friends, code = api.api_user_friends(request)
    assert not {'user_id':1} in friends
    assert {'user_id':3} in friends
    assert code == 200

    request = api.APIRequest('GET', 'user_friends', {'user_id':'3'})
    friends, code = api.api_user_friends(request)
    assert {'user_id':1} in friends
    assert {'user_id':2} in friends
    assert code == 200