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

    # Verify the correct tables are present
    api._dbCursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = api._dbCursor.fetchall()
    print(tables)
    assert tables == [('users',), ('games',), ('user_game_stats',), ('friends',)]

    # Check default user admin is the only user
    api._dbCursor.execute("SELECT user_id, username, valid, gamesPlayed, gamesWon, averageScore FROM users")
    users = api._dbCursor.fetchall()
    assert users == [(0, 'admin', 0, None, None, None)]

    # Check that games table is empty
    api._dbCursor.execute("SELECT COUNT(*) FROM games")
    game_count = api._dbCursor.fetchone()
    assert game_count == (0,)

    # Check that game stats table is empty
    api._dbCursor.execute("SELECT COUNT(*) FROM user_game_stats")
    game_count = api._dbCursor.fetchone()
    assert game_count == (0,)

    # Check that friends table is empty
    api._dbCursor.execute("SELECT COUNT(*) FROM friends")
    friend_count = api._dbCursor.fetchone()
    assert friend_count == (0,)


def test_check_username(tmp_path):
    api = setup_api(tmp_path)

    # Check valid usernames
    assert api._check_username('ThisIsAValidUsername')
    assert api._check_username('nc84nvqw04873xnb0nzfg0284')
    assert api._check_username('five5')
    assert api._check_username('using_underscores')
    assert api._check_username('!"#$%&\'()*+,-./:;<=>?@')
    assert api._check_username('[\]^_`{|}~')

    # Check invalid usernames
    assert not api._check_username('four')
    assert not api._check_username('twenty-six-characters-long')
    assert not api._check_username('admin')
    assert not api._check_username('deleted_user')
    assert not api._check_username('unknown_user')
    assert not api._check_username(' ')
    assert not api._check_username('space username')
    assert not api._check_username('non\nprintable')
    assert not api._check_username('emoji😀')
    assert not api._check_username('£latin¤supplement')
    assert not api._check_username('ハハ負け犬')

def test_check_password(tmp_path):
    api = setup_api(tmp_path)

    # Check valid passwords
    assert api._check_password('Ju$TeN0ugh')
    assert api._check_password('@lm0st_BUT_n0t_qu1t3_l0ng_3nough_tO_c@uS3_1ssu3s__')
    assert api._check_password('9sW$S9YHIFaC7EGk75RtD&gj')
    assert api._check_password('3A0IO9VfSdLIDYjC!Z%knj@u')
    assert api._check_password('&t@EuAt%^iW5eAxA9tm&mp@B')

    # Check invalid passwords
    assert not api._check_password('t0Oshort!')
    assert not api._check_password('w@y_wAy_way_way_way_way_way_way_way_way_way_T00L0ng')
    assert not api._check_password('non\nprintable')
    assert not api._check_password('emoji😀')
    assert not api._check_password('£latin¤supplement')
    assert not api._check_password('ハハ負け犬')
    assert not api._check_password('aGoodP@ssword!bUtnod!g!ts')
    assert not api._check_password('5729!#%&8~%&@#973@')
    assert not api._check_password('l0w3rc@se0n1y')
    assert not api._check_password('UPP3RC@SE_0N1Y')
    assert not api._check_password('N0punctuiation101')
    assert not api._check_password('password')
    assert not api._check_password('query')
    assert not api._check_password('123456789')
    assert not api._check_password('123456')
    assert not api._check_password('secret')
    assert not api._check_password('secret')

def test_is_username_existing(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test usernames that do exist
    assert api._is_username_existing('admin')
    assert api._is_username_existing('userA')
    assert api._is_username_existing('userB')

    # Test usernames that do not exist
    assert not api._is_username_existing('userC')
    assert not api._is_username_existing('not_a_user')
    assert not api._is_username_existing('user')

def test_is_user_account_valid(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Check existing users
    assert not api._is_user_account_valid(-1)
    assert not api._is_user_account_valid(0)
    assert api._is_user_account_valid(1)
    assert api._is_user_account_valid(2)

    # Delete user and check valid
    api._api_user_delete({'user_id':2})
    assert api._is_user_account_valid(1)
    assert not api._is_user_account_valid(2)

def test_is_user_id_valid(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Check valid IDs
    assert api._is_user_id_valid(-1)
    assert not api._is_user_id_valid(0)
    assert api._is_user_id_valid(1)
    assert api._is_user_id_valid(2)

    # Delete user and check valid
    api._api_user_delete({'user_id':2})
    assert api._is_user_account_valid(1)
    assert not api._is_user_account_valid(2)

def test_is_user_deleted(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Check existing users
    assert not api._is_user_deleted(0)
    assert not api._is_user_deleted(1)
    assert not api._is_user_deleted(2)

    # Delete user and check valid
    api._api_user_delete({'user_id':2})
    assert not api._is_user_deleted(1)
    assert api._is_user_deleted(2)

def test_are_users_friends(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})

    # Make 2 users friends
    api._api_user_addFriend({'user_id':1, 'friend_id':2})

    # Test who is friends
    assert api._are_users_friends(1, 2)
    assert api._are_users_friends(2, 1)
    assert not api._are_users_friends(1, 3)
    assert not api._are_users_friends(3, 1)
    assert not api._are_users_friends(0, 1)
    assert not api._are_users_friends(0, 2)
    assert not api._are_users_friends(0, 3)

def test_user_canView(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})

    # Make 2 users friends
    api._api_user_addFriend({'user_id':1, 'friend_id':2})

    # Check valid permissions
    assert api._user_canView(0, 1)
    assert api._user_canView(0, 2)
    assert api._user_canView(0, 3)
    assert api._user_canView(1, 1)
    assert api._user_canView(2, 2)
    assert api._user_canView(3, 3)
    assert api._user_canView(1, 2)
    assert api._user_canView(2, 1)

    # Check invalid permissions
    assert not api._user_canView(None, 1)
    assert not api._user_canView(None, 2)
    assert not api._user_canView(None, 3)
    assert not api._user_canView(1, 3)
    assert not api._user_canView(3, 1)
    assert not api._user_canView(1, 0)
    assert not api._user_canView(2, 0)
    assert not api._user_canView(3, 0)

def test_user_canEdit(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})

    # Make 2 users friends
    api._api_user_addFriend({'user_id':1, 'friend_id':2})

    # Check valid permissions
    assert api._user_canEdit(0, 1)
    assert api._user_canEdit(0, 2)
    assert api._user_canEdit(0, 3)
    assert api._user_canEdit(1, 1)
    assert api._user_canEdit(2, 2)
    assert api._user_canEdit(3, 3)

    # Check invalid permissions
    assert not api._user_canEdit(None, 1)
    assert not api._user_canEdit(None, 2)
    assert not api._user_canEdit(None, 3)
    assert not api._user_canEdit(1, 2)
    assert not api._user_canEdit(1, 3)
    assert not api._user_canEdit(2, 1)
    assert not api._user_canEdit(2, 3)
    assert not api._user_canEdit(3, 1)
    assert not api._user_canEdit(1, 3)
    assert not api._user_canEdit(1, 0)
    assert not api._user_canEdit(2, 0)
    assert not api._user_canEdit(3, 0)

def test_gen_password_hash():
    # Test proper hash/salt lengths
    hash, salt = restAPI.gen_password_hash('testPassword')
    assert len(hash) == 32
    assert len(salt) == 16

    # Test random salt results in different hash/salt for identical password
    hash2, salt2 = restAPI.gen_password_hash('testPassword')
    assert hash != hash2
    assert salt != salt2

def test_check_userAuth(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test with correct passwords
    assert api._check_userAuth('userA', 'test_pass101A')
    assert api._check_userAuth('userB', 'test_pass101B')

    # Test with incorrect passwords
    assert not api._check_userAuth('userA', 'incorrect_test_pass101A')
    assert not api._check_userAuth('userB', 'incorrect_test_pass101B')

    # Test with non-existing user
    assert not api._check_userAuth('not_a_user', 'incorrect_test_pass101B')

    # Test admin
    assert api._check_userAuth('admin', 'root')
    assert not api._check_userAuth('admin', 'not_R00T')

def test_checkApiKey(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Check there are no api keys before authentication
    assert api._restAPI__apiKeys == {}

    # Authenticate users
    keyAdmin = api._api_user_auth({'username':'admin', 'password':'root'})['apiKey']
    keyA = api._api_user_auth({'username':'userA', 'password':'test_pass101A'})['apiKey']
    keyB = api._api_user_auth({'username':'userB', 'password':'test_pass101B'})['apiKey']

    # Check keys
    assert len(api._restAPI__apiKeys) == 3
    assert api._checkApiKey(keyAdmin) == 0
    assert api._checkApiKey(keyA) == 1
    assert api._checkApiKey(keyB) == 2
    

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
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})
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

    user_id = api._api_user_create({'username':'createUserTest', 'password':'create_User_Password0'})
    assert user_id == {'user_id':1}

    user = api._api_user_get({'user_id':1})
    assert user == {1: {'username':'createUserTest', 'gamesPlayed':0, 'gamesWon':0, 'averageScore':0.0}}

    user_id = api._api_user_id({'username':'createUserTest'})
    assert user_id == {'createUserTest': 1}

    result = api._api_user_auth({'username':'createUserTest', 'password':'create_User_Password0'})
    assert result['success'] == True
    assert result['apiKey']


def test_create_bad_users(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'test_Pass101'})

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'admin', 'password':'test_Pass101'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_create({'username':'deleted_user', 'password':'test_Pass101'})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        result = api._api_user_create({'username':'testUser', 'password':'different_Test_Pass0'})
    assert apiError.value.code == 403


def test_delete_user(tmp_path):
    api = setup_api(tmp_path, users={'testUser':'test_Pass101'})

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
    api = setup_api(tmp_path, users={'testUser':'test_Pass101', 'testUser2':'electric_B00gal00'})

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
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

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
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})

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
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})
    
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3})
    api._api_game_register({'timestamp':1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':8})

    result = api._api_game_registerStats({'user_id':1, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_min':10, 'swing_max':20, 'swing_avg':13.467, 'hit_modeX':0.5, 'hit_modeY':0.0, 'hit_avgX':0.412, 'hit_avgY':-0.142})
    assert result == {'success':True}

    result = api._api_game_registerStats({'user_id':2, 'game_id':0, 'swing_count':139, 'swing_hits':83, 'swing_min':11, 'swing_max':25, 'swing_avg':17.395, 'hit_modeX':0.0, 'hit_modeY':-0.5, 'hit_avgX':0.112, 'hit_avgY':-0.442})
    assert result == {'success':True}

    result = api._api_game_registerStats({'user_id':1, 'game_id':1, 'swing_count':161, 'swing_hits':101, 'swing_min':9, 'swing_max':19, 'swing_avg':11.767, 'hit_modeX':-0.5, 'hit_modeY':0.0, 'hit_avgX':-0.398, 'hit_avgY':0.042})
    assert result == {'success':True}

    result = api._api_game_stats({'user_id':1})
    assert result == {0:{'timestamp':0, 'swing_count':150, 'swing_hits':90, 'hit_percentage':0.6, 'swing_min':10, 'swing_max':20, 'swing_avg':13.467, 'hit_modeX':0.5, 'hit_modeY':0.0, 'hit_avgX':0.412, 'hit_avgY':-0.142},
                      1:{'timestamp':1, 'swing_count':161, 'swing_hits':101, 'hit_percentage':0.6273291925465838, 'swing_min':9, 'swing_max':19, 'swing_avg':11.767, 'hit_modeX':-0.5, 'hit_modeY':0.0, 'hit_avgX':-0.398, 'hit_avgY':0.042}}
    
    result = api._api_game_stats({'user_id':1, 'game_id':[0,1,2]})
    assert result == {0:{'timestamp':0, 'swing_count':150, 'swing_hits':90, 'hit_percentage':0.6, 'swing_min':10, 'swing_max':20, 'swing_avg':13.467, 'hit_modeX':0.5, 'hit_modeY':0.0, 'hit_avgX':0.412, 'hit_avgY':-0.142},
                      1:{'timestamp':1, 'swing_count':161, 'swing_hits':101, 'hit_percentage':0.6273291925465838, 'swing_min':9, 'swing_max':19, 'swing_avg':11.767, 'hit_modeX':-0.5, 'hit_modeY':0.0, 'hit_avgX':-0.398, 'hit_avgY':0.042},
                      2:None}

    result = api._api_game_stats({'game_id':0, 'user_id':2})
    assert result == {0:{'timestamp':0, 'swing_count':139, 'swing_hits':83, 'hit_percentage':0.5971223021582733, 'swing_min':11, 'swing_max':25, 'swing_avg':17.395, 'hit_modeX':0.0, 'hit_modeY':-0.5, 'hit_avgX':0.112, 'hit_avgY':-0.442}}