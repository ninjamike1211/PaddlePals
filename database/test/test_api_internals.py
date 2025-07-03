from database import database_setup
from database import database_api
import json

def setup_api(tmp_path, useAuth=False, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    return database_api.restAPI(db_path, useAuth)


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
    
    user, code = api.api_user_get({'user_id':0})
    assert type(user) is str
    assert code == 404

    result, code = api.api_user_set({'user_id':0, 'username':'notAdmin'})
    assert type(result) is str
    assert code == 404

    result, code = api.api_user_delete({'user_id':0})
    assert type(result) is str
    assert code == 404
    
    user, code = api.api_user_delete({'username':'admin'})
    assert type(user) is str
    assert code == 400



def test_create_user(tmp_path):
    api = setup_api(tmp_path)

    user_id, code = api.api_user_create({'username':'createUserTest', 'password':'createUserPassword'})
    assert user_id == {'user_id':1}
    assert code == 200

    user, code = api.api_user_get({'user_id':1})
    assert user == {'username':'createUserTest', 'gamesPlayed':0, 'gamesWon':0, 'averageScore':0.0}
    assert code == 200

    user_id, code = api.api_user_id({'username':'createUserTest'})
    assert user_id == {'user_id':1}
    assert code == 200

    result, code = api.api_user_auth({'username':'createUserTest', 'password':'createUserPassword'})
    assert result['success'] == True
    assert result['apiKey']
    assert code == 200


def test_create_bad_users(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass'})

    result, code = api.api_user_create({'username':'admin', 'password':'testPass'})
    assert type(result) is str
    assert code == 400

    result, code = api.api_user_create({'username':'deleted_user', 'password':'testPass'})
    assert type(result) is str
    assert code == 400

    result, code = api.api_user_create({'username':'testUser', 'password':'differentTestPass'})
    assert type(result) is str
    assert code == 403


def test_delete_user(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass'})

    result, code = api.api_user_get({'user_id':1, 'objects':['username']})
    assert result == {'username':'testUser'}
    assert code == 200

    result, code = api.api_user_delete({'user_id':1})
    assert result == {'success':True}
    assert code == 200

    result, code = api.api_user_get({'user_id':1})
    assert result == {'username':'deleted_user', 'gamesPlayed':None, 'gamesWon':None, 'averageScore':None}
    assert code == 200

    result, code = api.api_user_set({'user_id':1, 'username':'name'})
    assert type(result) is str
    assert code == 404

    result, code = api.api_user_id({'username':'testUser'})
    assert type(result) is str
    assert code == 404

    result, code = api.api_user_id({'username':'deleted_user'})
    assert type(result) is str
    assert code == 400

    result, code = api.api_user_games({'user_id':1})
    assert type(result) is str
    assert code == 404

    api.cursor.execute("SELECT * FROM users WHERE user_id=1")
    user = api.cursor.fetchall()
    assert user == [(1, 'deleted_user', None, None, 0, None, None, None)]


def test_modify_username(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass', 'testUser2':'electricBoogaloo'})

    result, code = api.api_user_get({'user_id':1, 'objects':['username']})
    assert result == {'username':'testUser'}
    assert code == 200

    result, code = api.api_user_set({'user_id':1, 'username':'differentName'})
    assert result == {'success':True}
    assert code == 200

    result, code = api.api_user_get({'user_id':1, 'objects':['username']})
    assert result == {'username':'differentName'}
    assert code == 200

    result, code = api.api_user_set({'user_id':1, 'username':'admin'})
    assert type(result) is str
    assert code == 400

    result, code = api.api_user_set({'user_id':1, 'username':'deleted_user'})
    assert type(result) is str
    assert code == 400

    result, code = api.api_user_set({'user_id':1, 'username':'testUser2'})
    assert type(result) is str
    assert code == 403

def test_post_game(tmp_path):
    api = setup_api(tmp_path, users={'userA':'passwordA', 'userB':'passwordB'})

    game_id, code = api.api_game_register({'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7})
    assert game_id == {'game_id':0}
    assert code == 200

    game, code = api.api_game_get({'game_id':0})
    assert game == {'game_id':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7}
    assert code == 200

    game_id, code = api.api_game_register({'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10})
    assert game_id == {'game_id':1}
    assert code == 200

    game, code = api.api_game_get({'game_id':1})
    assert game == {'game_id':1, 'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10}
    assert code == 200

    gamesA, code = api.api_user_games({'user_id':1})
    assert gamesA == {'game_ids':[0,1]}
    assert code == 200

    gamesB, code = api.api_user_games({'user_id':2})
    assert gamesB == {'game_ids':[0,1]}
    assert code == 200

    userA_data, code = api.api_user_get({'user_id':1, 'objects':['gamesPlayed', 'gamesWon', 'averageScore']})
    assert userA_data == {'gamesPlayed':2, 'gamesWon':1, 'averageScore':10.5}
    assert code == 200

    userA_data, code = api.api_user_get({'user_id':2, 'objects':['gamesPlayed', 'gamesWon', 'averageScore']})
    assert userA_data == {'gamesPlayed':2, 'gamesWon':1, 'averageScore':9.5}
    assert code == 200


def test_friends(tmp_path):
    api = setup_api(tmp_path, users={'userA':'passA', 'userB':'passB', 'userC':'passC'})

    friends, code = api.api_user_friends({'user_id':1})
    assert not friends
    assert code == 200

    friends, code = api.api_user_friends({'user_id':2})
    assert not friends
    assert code == 200

    friends, code = api.api_user_friends({'user_id':3})
    assert not friends
    assert code == 200

    result, code = api.api_user_addFriend({'user_id':1, 'friend_id':2})
    assert result == {'success':True}
    assert code == 200

    result, code = api.api_user_addFriend({'user_id':3, 'friend_username':'userB'})
    assert result == {'success':True}
    assert code == 200

    result, code = api.api_user_addFriend({'user_id':3, 'friend_username':'userA'})
    assert result == {'success':True}
    assert code == 200

    result, code = api.api_user_removeFriend({'user_id':2, 'friend_id':1})
    assert result == {'success':True}
    assert code == 200

    friends, code = api.api_user_friends({'user_id':1})
    assert not {'user_id':2} in friends
    assert {'user_id':3} in friends
    assert code == 200

    friends, code = api.api_user_friends({'user_id':2})
    assert not {'user_id':1} in friends
    assert {'user_id':3} in friends
    assert code == 200

    friends, code = api.api_user_friends({'user_id':3})
    assert {'user_id':1} in friends
    assert {'user_id':2} in friends
    assert code == 200