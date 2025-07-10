import pytest
from database import database_setup
from database.database_api import restAPI

def setup_api(tmp_path, useAuth=False, users=None):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    return restAPI(db_path, useAuth)


def test_init(tmp_path):
    api = setup_api(tmp_path)
    assert api
    assert api._database
    assert api._dbCursor

    # Check default user admin is the only user
    api._dbCursor.execute("SELECT user_id, username, valid, gamesPlayed, gamesWon, averageScore FROM users")
    users = api._dbCursor.fetchall()
    assert users == [(0, 'admin', 0, None, None, None)]

    # Check that games table is empty
    api._dbCursor.execute("SELECT COUNT(*) FROM games")
    game_count = api._dbCursor.fetchone()
    assert game_count == (0,)

    # Check that friends table is empty
    api._dbCursor.execute("SELECT COUNT(*) FROM friends")
    friend_count = api._dbCursor.fetchone()
    assert friend_count == (0,)


def test_user_admin(tmp_path):
    api = setup_api(tmp_path)
    
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_get({'user_id':0})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_set({'user_id':0, 'username':'notAdmin'})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':0})
    assert apiError.value.code == 404
    
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'username':'admin'})
    assert apiError.value.code == 400


def test_user_get(tmp_path):
    api = setup_api(tmp_path, users={'userA':'testPass101A', 'userB':'testPass101B'})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':8})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':13, 'loser_points':11})

    # Valid test cases
    userA = api._api_user_get({'user_id':1})
    userB = api._api_user_get({'user_id':2})

    assert userA == {1:{'username':'userA', 'gamesPlayed':3, 'gamesWon':1, 'averageScore':10.0}}
    assert userB == {2:{'username':'userB', 'gamesPlayed':3, 'gamesWon':2, 'averageScore':9.0}}

    users = api._api_user_get({'user_id':[1,2]})
    assert users == {
        1:{'username':'userA', 'gamesPlayed':3, 'gamesWon':1, 'averageScore':10.0},
        2:{'username':'userB', 'gamesPlayed':3, 'gamesWon':2, 'averageScore':9.0}
    }

    user = api._api_user_get({'user_id':[1,2], 'objects':['username']})
    assert user == {1:{'username':'userA'},
                    2:{'username':'userB'}}

    user = api._api_user_get({'user_id':[1,2], 'objects':['gamesPlayed']})
    assert user == {1:{'gamesPlayed':3},
                    2:{'gamesPlayed':3}}

    user = api._api_user_get({'user_id':[1,2], 'objects':['gamesWon']})
    assert user == {1:{'gamesWon':1},
                    2:{'gamesWon':2}}

    user = api._api_user_get({'user_id':[1,2], 'objects':['averageScore']})
    assert user == {1:{'averageScore':10.0},
                    2:{'averageScore':9.0}}

    api._api_user_delete({'user_id':2})
    user = api._api_user_get({'user_id':2})
    assert user == {2:{'username':'deleted_user', 'gamesPlayed':None, 'gamesWon':None, 'averageScore':None}}

    # Error test cases
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_get({})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_get({'user_id':0})
    assert apiError.value.code == 404


    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_get({'user_id':[0,1]})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_get({'user_id':1, 'objects':['notAnObject']})
    assert apiError.value.code == 400


def test_create_user(tmp_path):
    api = setup_api(tmp_path)

    user_id = api._api_user_create({'username':'createUserTest', 'password':'createUserPassword'})
    assert user_id == {'user_id':1}

    user = api._api_user_get({'user_id':1})
    assert user == {1: {'username':'createUserTest', 'gamesPlayed':0, 'gamesWon':0, 'averageScore':0.0}}

    user_id = api._api_user_id({'username':'createUserTest'})
    assert user_id == {'createUserTest': 1}

    result = api._api_user_auth({'username':'createUserTest', 'password':'createUserPassword'})
    assert result['success'] == True
    assert result['apiKey']


def test_create_bad_users(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass101'})

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'admin', 'password':'testPass101'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_create({'username':'deleted_user', 'password':'testPass101'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_create({'username':'testUser', 'password':'differentTestPass'})
    assert apiError.value.code == 403


def test_delete_user(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass101'})

    result = api._api_user_get({'user_id':1, 'objects':['username']})
    assert result == {1: {'username':'testUser'}}

    result = api._api_user_delete({'user_id':1})
    assert result == {'success':True}

    result = api._api_user_get({'user_id':1})
    assert result == {1: {'username':'deleted_user', 'gamesPlayed':None, 'gamesWon':None, 'averageScore':None}}

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_set({'user_id':1, 'username':'name'})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_id({'username':'testUser'})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_id({'username':'deleted_user'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_games({'user_id':1})
    assert apiError.value.code == 404

    api._dbCursor.execute("SELECT * FROM users WHERE user_id=1")
    user = api._dbCursor.fetchall()
    assert user == [(1, 'deleted_user', None, None, 0, None, None, None)]


def test_modify_username(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'testPass101', 'testUser2':'electricBoogaloo'})

    result = api._api_user_get({'user_id':1, 'objects':['username']})
    assert result == {1: {'username':'testUser'}}

    result = api._api_user_set({'user_id':1, 'username':'differentName'})
    assert result == {'success':True}

    result = api._api_user_get({'user_id':1, 'objects':['username']})
    assert result == {1: {'username':'differentName'}}

    result = api._api_user_id({'username':'differentName'})
    assert result == {'differentName': 1}

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_set({'user_id':1, 'username':'admin'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_set({'user_id':1, 'username':'deleted_user'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_set({'user_id':1, 'username':'testUser2'})
    assert apiError.value.code == 403

def test_post_game(tmp_path):
    api = setup_api(tmp_path, users={'userA':'testPass101A', 'userB':'testPass101B'})

    game_id = api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7})
    assert game_id == {'game_id':0}

    game = api._api_game_get({'game_id':0})
    assert game == {0: {'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7}}

    game_id = api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10})
    assert game_id == {'game_id':1}

    game = api._api_game_get({'game_id':1})
    assert game == {1: {'timestamp':0, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10}}

    gamesA = api._api_user_games({'user_id':1})
    assert gamesA == {'game_ids':[0,1]}

    gamesB = api._api_user_games({'user_id':2})
    assert gamesB == {'game_ids':[0,1]}

    userA_data = api._api_user_get({'user_id':[1,2], 'objects':['gamesPlayed', 'gamesWon', 'averageScore']})
    assert userA_data == {1: {'gamesPlayed':2, 'gamesWon':1, 'averageScore':10.5},
                          2: {'gamesPlayed':2, 'gamesWon':1, 'averageScore':9.5}}


def test_friends(tmp_path):
    api = setup_api(tmp_path, users={'userA':'testPass101A', 'userB':'testPass101B', 'userC':'testPass101C'})

    friends = api._api_user_friends({'user_id':1})
    assert not friends

    friends = api._api_user_friends({'user_id':2})
    assert not friends

    friends = api._api_user_friends({'user_id':3})
    assert not friends

    result = api._api_user_addFriend({'user_id':1, 'friend_id':2})
    assert result == {'success':True}

    result = api._api_user_addFriend({'user_id':3, 'friend_username':'userB'})
    assert result == {'success':True}

    result = api._api_user_addFriend({'user_id':3, 'friend_username':'userA'})
    assert result == {'success':True}

    result = api._api_user_removeFriend({'user_id':2, 'friend_id':1})
    assert result == {'success':True}

    friends = api._api_user_friends({'user_id':1})
    assert not 2 in friends
    assert 3 in friends

    friends = api._api_user_friends({'user_id':2})
    assert not 1 in friends
    assert 3 in friends

    friends = api._api_user_friends({'user_id':3})
    assert 1 in friends
    assert 2 in friends


def test_game_stats(tmp_path):
    api = setup_api(tmp_path, users={'userA':'testPass101A', 'userB':'testPass101B'})
    
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':8})

    result = api._api_game_registerStats({'user_id':1, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_min':10, 'swing_max':20, 'swing_avg':13.467, 'hit_modeX':0.5, 'hit_modeY':0.0, 'hit_avgX':0.412, 'hit_avgY':-0.142})
    assert result == {'success':True}

    result = api._api_game_registerStats({'user_id':2, 'game_id':0, 'swing_count':139, 'swing_hits':83, 'swing_min':11, 'swing_max':25, 'swing_avg':17.395, 'hit_modeX':0.0, 'hit_modeY':-0.5, 'hit_avgX':0.112, 'hit_avgY':-0.442})
    assert result == {'success':True}

    result = api._api_game_registerStats({'user_id':1, 'game_id':1, 'swing_count':161, 'swing_hits':101, 'swing_min':9, 'swing_max':19, 'swing_avg':11.767, 'hit_modeX':-0.5, 'hit_modeY':0.0, 'hit_avgX':-0.398, 'hit_avgY':0.042})
    assert result == {'success':True}

    result = api._api_game_stats({'game_id':0, 'user_id':1})
    assert result == {'swing_count':150, 'swing_hits':90, 'hit_percentage':0.6, 'swing_min':10, 'swing_max':20, 'swing_avg':13.467, 'hit_modeX':0.5, 'hit_modeY':0.0, 'hit_avgX':0.412, 'hit_avgY':-0.142}

    result = api._api_game_stats({'game_id':0, 'user_id':2})
    assert result == {'swing_count':139, 'swing_hits':83, 'hit_percentage':0.5971223021582733, 'swing_min':11, 'swing_max':25, 'swing_avg':17.395, 'hit_modeX':0.0, 'hit_modeY':-0.5, 'hit_avgX':0.112, 'hit_avgY':-0.442}

    result = api._api_game_stats({'game_id':1, 'user_id':1})
    assert result == {'swing_count':161, 'swing_hits':101, 'hit_percentage':0.6273291925465838, 'swing_min':9, 'swing_max':19, 'swing_avg':11.767, 'hit_modeX':-0.5, 'hit_modeY':0.0, 'hit_avgX':-0.398, 'hit_avgY':0.042}