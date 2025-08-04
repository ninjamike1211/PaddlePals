import time
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

    def run_init_tests():
        # Verify the correct tables are present
        api._dbCursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = api._dbCursor.fetchall()
        print(tables)
        assert tables == [('users',), ('games',), ('user_game_stats',), ('friends',)]

        # Check default user admin is the only user
        api._dbCursor.execute("SELECT user_id, username, valid, gamesPlayed, gamesWon, averageScore FROM users")
        users = api._dbCursor.fetchall()
        assert users == [(0, 'admin', 0, None, None, None)]

        # Verify user cache is empty
        assert len(api._restAPI__user_cache) == 0

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

    # Run test on fresh database
    run_init_tests()

    # Add entries to database to make it "dirty"
    api._api_user_create({'username':'testUserA', 'password':'t3stP@ssw0rd!'})
    api._api_user_create({'username':'testUserB', 'password':'t3stP@ssw0rd!'})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':5})
    api._api_game_registerStats({'user_id':1, 'game_id':0, 'swing_count':161, 'swing_hits':101, 'swing_max':19, 'Q1_hits':25, 'Q2_hits':25, 'Q3_hits':27, 'Q4_hits':24})
    api._api_user_addFriend({'user_id':1, 'friend_id':2})
    api.close()

    # Create fresh database/api, set to clear database
    api = restAPI(tmp_path / 'pickle.db', useAuth=False, clearDB=True)

    # Verify database was actually cleared and initialized
    run_init_tests()


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

    # Check user cache
    assert api._restAPI__user_cache == {1,2}

    # Delete user and check valid
    api._api_user_delete({'user_id':2})
    assert api._is_user_account_valid(1)
    assert not api._is_user_account_valid(2)

    # Check user cache
    assert api._restAPI__user_cache == {1}

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
    api._api_user_addFriend({'user_id':1, 'friend_id':2, 'sender_id':1})

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
    api._api_user_addFriend({'user_id':1, 'friend_id':2, 'sender_id':1})

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

def test_gen_password_hash(tmp_path):
    api = setup_api(tmp_path)

    # Test proper hash/salt lengths
    hash, salt = api._gen_password_hash('testPassword')
    assert len(hash) == 32
    assert len(salt) == 16

    # Test random salt results in different hash/salt for identical password
    hash2, salt2 = api._gen_password_hash('testPassword')
    assert hash != hash2
    assert salt != salt2

def test_check_userAuth(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test with correct passwords
    assert api._check_userAuth('userA', 'test_pass101A') == 1
    assert api._check_userAuth('userB', 'test_pass101B') == 2

    # Test with incorrect passwords
    assert api._check_userAuth('userA', 'incorrect_test_pass101A') == None
    assert api._check_userAuth('userB', 'incorrect_test_pass101B') == None

    # Test with non-existing user
    assert api._check_userAuth('not_a_user', 'incorrect_test_pass101B') == None

    # Test admin
    assert api._check_userAuth('admin', 'root') == 0
    assert api._check_userAuth('admin', 'not_R00T') == None

def test_gen_ApiKey(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Record time for expiration timestamps
    min_expiration = time.time() + api.API_KEY_TIMEOUT

    # Generate key/renew pairs
    keyAdmin, renewAdmin = api._gen_ApiKey(0)
    keyA, renewA = api._gen_ApiKey(1)
    keyB, renewB = api._gen_ApiKey(2)

    # Check for uniqueness
    assert keyAdmin != keyA != keyB
    assert renewAdmin != renewA != renewB

    # Check all values in internal dicts
    assert list(api._restAPI__apiKeys.keys()) == [keyAdmin, keyA, keyB]
    assert list(api._restAPI__renewalKeys.keys()) == [renewAdmin, renewA, renewB]

    assert api._restAPI__apiKeys[keyAdmin]['user_id'] == 0
    assert api._restAPI__apiKeys[keyAdmin]['expiration'] >= min_expiration
    assert api._restAPI__renewalKeys[renewAdmin] == 0

    assert api._restAPI__apiKeys[keyA]['user_id'] == 1
    assert api._restAPI__apiKeys[keyA]['expiration'] >= min_expiration
    assert api._restAPI__renewalKeys[renewA] == 1

    assert api._restAPI__apiKeys[keyB]['user_id'] == 2
    assert api._restAPI__apiKeys[keyB]['expiration'] >= min_expiration
    assert api._restAPI__renewalKeys[renewB] == 2

def test_gen_ApiKey_collisions(tmp_path):
    api = setup_api(tmp_path, useAuth=True)

    for i in range(0, 1000000):
        api._gen_ApiKey(0)

    assert len(api._restAPI__apiKeys) == 1000000
    assert len(api._restAPI__renewalKeys) == 1000000

def test_checkApiKey(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Set api key timeout to 5 seconds
    api.API_KEY_TIMEOUT = 5

    # Check there are no api keys before authentication
    assert api._restAPI__apiKeys == {}

    # Authenticate users
    keyAdmin = api._api_user_auth({'username':'admin', 'password':'root'})['apiKey']
    keyA = api._api_user_auth({'username':'userA', 'password':'test_pass101A'})['apiKey']
    keyBVals = api._api_user_auth({'username':'userB', 'password':'test_pass101B'})
    keyB = keyBVals['apiKey']

    # Check keys
    assert len(api._restAPI__apiKeys) == 3
    assert api._checkApiKey(keyAdmin) == 0
    assert api._checkApiKey(keyA) == 1
    assert api._checkApiKey(keyB) == 2

    # Delete user and check that it's auth is invalid, and that the key is removed
    api._api_user_delete({'user_id':2, 'sender_id':2})
    with pytest.raises(restAPI.APIError) as apiError:
        api._checkApiKey(keyB)
    assert apiError.value.code == 401
    assert keyB not in api._restAPI__apiKeys
    assert keyBVals['renewalKey'] not in api._restAPI__renewalKeys

    # wait for timeout
    time.sleep(5)

    # Check that keys are invalid now
    with pytest.raises(restAPI.APIError) as apiError:
        api._checkApiKey(keyAdmin)
    assert apiError.value.code == 498
    with pytest.raises(restAPI.APIError) as apiError:
        api._checkApiKey(keyA)
    assert apiError.value.code == 498

    # Check random invalid API keys don't work
    assert api._checkApiKey(None) == None
    assert api._checkApiKey("") == None
    assert api._checkApiKey("0") == None
    assert api._checkApiKey("0000000000000000") == None # In the incredibly rare chance of a collision, just run it again
    assert api._checkApiKey("0123456789abcdefghijklmnopqrstuvwxyz") == None

def test_user_get_admin(tmp_path):
    api = setup_api(tmp_path)
    
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getUsername({'user_id':0})
    assert apiError.value.code == 404
    
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':0})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':0, 'username':'notAdmin'})
    assert apiError.value.code == 404

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':0})
    assert apiError.value.code == 404
    
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'username':'admin'})
    assert apiError.value.code == 400

def test_api_user_getUsername(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Get usernames from current user
    assert api._api_user_getUsername({'user_id':1, 'sender_id':1}) == {1:'userA'}
    assert api._api_user_getUsername({'user_id':2, 'sender_id':2}) == {2:'userB'}

    # Get usernames from admin
    assert api._api_user_getUsername({'user_id':1, 'sender_id':0}) == {1:'userA'}
    assert api._api_user_getUsername({'user_id':2, 'sender_id':0}) == {2:'userB'}

    # Get multiple users
    assert api._api_user_getUsername({'user_id':[1,2], 'sender_id':0}) == {1:'userA', 2:'userB'}
    assert api._api_user_getUsername({'user_id':[1,2], 'sender_id':1}) == {1:'userA', 2:'userB'}
    assert api._api_user_getUsername({'user_id':[1,2], 'sender_id':2}) == {1:'userA', 2:'userB'}

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getUsername({'sender_id':0})
    assert apiError.value.code == 400

    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getUsername({})
    assert apiError.value.code == 400

    # Test invalid user IDs
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getUsername({'user_id':0, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getUsername({'user_id':3, 'sender_id':0})
    assert apiError.value.code == 404

    # Test deleted/unknown users
    api._api_user_delete({'user_id':2, 'sender_id':0})
    assert api._api_user_getUsername({'user_id':2, 'sender_id':0}) == {2:'deleted_user'}
    assert api._api_user_getUsername({'user_id':2, 'sender_id':1}) == {2:'deleted_user'}
    assert api._api_user_getUsername({'user_id':-1, 'sender_id':1}) == {-1:'unknown_user'}


def test_api_user_getStats(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3})
    api._api_game_register({'timestamp':1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':8})
    api._api_game_register({'timestamp':2, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':13, 'loser_points':11})

    # get all user info
    userA = api._api_user_getStats({'user_id':1, 'sender_id':0})
    assert userA == {1:{'gamesPlayed':3, 'gamesWon':1, 'averageScore':10.0}}
    userB = api._api_user_getStats({'user_id':2, 'sender_id':0})
    assert userB == {2:{'gamesPlayed':3, 'gamesWon':2, 'averageScore':9.0}}

    # get all user info at once
    users = api._api_user_getStats({'user_id':[1,2], 'sender_id':0})
    assert users == {
        1:{'gamesPlayed':3, 'gamesWon':1, 'averageScore':10.0},
        2:{'gamesPlayed':3, 'gamesWon':2, 'averageScore':9.0}
    }

    # Test getting each individual object
    user = api._api_user_getStats({'user_id':[1,2], 'stats':['gamesPlayed'], 'sender_id':0})
    assert user == {1:{'gamesPlayed':3},
                    2:{'gamesPlayed':3}}

    user = api._api_user_getStats({'user_id':[1,2], 'stats':['gamesWon'], 'sender_id':0})
    assert user == {1:{'gamesWon':1},
                    2:{'gamesWon':2}}

    user = api._api_user_getStats({'user_id':[1,2], 'stats':['averageScore'], 'sender_id':0})
    assert user == {1:{'averageScore':10.0},
                    2:{'averageScore':9.0}}
    
    # Test with no parameters
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({})
    assert apiError.value.code == 400

    # Test invalid users
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':0, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':-1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':3, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':[0,1], 'sender_id':0})
    assert apiError.value.code == 404

    # Test with no user_id parameter
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'incorrect_parameter':'hahaha', 'sender_id':0})
    assert apiError.value.code == 400

    # Test with wrong user_id type
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':'hahaha', 'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid object
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':1, 'stats':['averageScore','not_an_object'], 'sender_id':0})
    assert apiError.value.code == 404

    # Test viewing user without permissions
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':2, 'sender_id':1})
    assert apiError.value.code == 403
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':[1,2], 'sender_id':1})
    assert apiError.value.code == 403

    # Test deleted user
    api._api_user_delete({'user_id':2, 'sender_id':0})
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_getStats({'user_id':2, 'sender_id':0})
    assert apiError.value.code == 404

def test_api_user_setUsername(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test for no user_id
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'not_user_id':1, 'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid perms
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':2, 'username':'invalid_user!!', 'sender_id':1})
    assert apiError.value.code == 403
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'invalid_user!!', 'sender_id':2})
    assert apiError.value.code == 403

    # Test invalid user
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':0, 'username':'invalid_user!!', 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':-1, 'username':'invalid_user!!', 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':-3, 'username':'invalid_user!!', 'sender_id':0})
    assert apiError.value.code == 404

    # Test for no set params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'not_username':'haha', 'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid username
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'bob', 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'admin', 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'deleted_user', 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'unknown_user', 'sender_id':0})
    assert apiError.value.code == 400

    # Test duplicate user
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'userA', 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_setUsername({'user_id':1, 'username':'userB', 'sender_id':0})
    assert apiError.value.code == 400

    # Test valid
    result = api._api_user_setUsername({'user_id':1, 'username':'userANew', 'sender_id':1})
    assert result == {'success':True}
    api._dbCursor.execute("SELECT username FROM users WHERE user_id=1")
    assert api._dbCursor.fetchone() == ('userANew',)

    result = api._api_user_setUsername({'user_id':2, 'username':'userBNew', 'sender_id':2})
    assert result == {'success':True}
    api._dbCursor.execute("SELECT username FROM users WHERE user_id=2")
    assert api._dbCursor.fetchone() == ('userBNew',)

    result = api._api_user_setUsername({'user_id':1, 'username':'userANewNew', 'sender_id':0})
    assert result == {'success':True}
    api._dbCursor.execute("SELECT username FROM users WHERE user_id=1")
    assert api._dbCursor.fetchone() == ('userANewNew',)

    result = api._api_user_setUsername({'user_id':2, 'username':'userBNewNew', 'sender_id':0})
    assert result == {'success':True}
    api._dbCursor.execute("SELECT username FROM users WHERE user_id=2")
    assert api._dbCursor.fetchone() == ('userBNewNew',)

def test_api_user_create(tmp_path):
    api = setup_api(tmp_path, useAuth=True)

    # Create user
    user_id = api._api_user_create({'username':'createUserTest', 'password':'create_User_Password0'})
    assert user_id == {'user_id':1}

    # Check user was created in database
    api._dbCursor.execute("SELECT user_id, username, valid, gamesPlayed, gamesWon, averageScore FROM users WHERE user_id=1")
    assert api._dbCursor.fetchone() == (1, 'createUserTest', 1, 0, 0, 0.0)

    # Check password auth is correct
    assert api._check_userAuth('createUserTest', 'create_User_Password0') == 1

    # Check user cache
    assert api._restAPI__user_cache == {1}

    # Test invalid username
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'bob', 'password':'test_Pass101'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'admin', 'password':'test_Pass101'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'deleted_user', 'password':'test_Pass101'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'unknown_user', 'password':'test_Pass101'})
    assert apiError.value.code == 400

    # Test existing username
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'createUserTest', 'password':'test_Pass101'})
    assert apiError.value.code == 403

    # Test invalid password
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'newUser', 'password':'notvalid'})
    assert apiError.value.code == 400

    # Test missing params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'password':'test_Pass101.5FM'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_create({'username':'testUser'})
    assert apiError.value.code == 400


def test_api_user_delete(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})
    api._api_user_addFriend({'user_id':1, 'friend_id':2, 'sender_id':0})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_registerStats({'user_id':1, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22})
    api._api_game_registerStats({'user_id':2, 'game_id':0, 'swing_count':139, 'swing_hits':83, 'swing_max':23, 'Q1_hits':21, 'Q2_hits':22, 'Q3_hits':21, 'Q4_hits':19})

    # Check user cache
    assert api._restAPI__user_cache == {1,2}

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'wrong_param':1})
    assert apiError.value.code == 400

    # Test invalid user ID
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':-1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':0, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':3, 'sender_id':0})
    assert apiError.value.code == 404

    # Test without user perms
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':1, 'sender_id':2})
    assert apiError.value.code == 403
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_delete({'user_id':2, 'sender_id':1})
    assert apiError.value.code == 403

    # Test valid deletions
    assert api._api_user_delete({'user_id':1, 'sender_id':1}) == {'success':True}
    assert api._api_user_delete({'user_id':2, 'sender_id':0}) == {'success':True}

    # Verify username is updated
    assert api._api_user_getUsername({'user_id':[1,2], 'sender_id':0}) == {1:'deleted_user', 2:'deleted_user'}

    # Verify in database all data was removed
    api._dbCursor.execute("SELECT * FROM users WHERE user_id=1")
    assert api._dbCursor.fetchall() == [(1, 'deleted_user', None, None, 0, None, None, None)]
    api._dbCursor.execute("SELECT * FROM users WHERE user_id=2")
    assert api._dbCursor.fetchall() == [(2, 'deleted_user', None, None, 0, None, None, None)]

    api._dbCursor.execute("SELECT COUNT(*) FROM friends WHERE userA=1 OR userB=1 OR userA=2 OR userB=2")
    assert api._dbCursor.fetchone() == (0,)

    api._dbCursor.execute("SELECT COUNT(*) FROM user_game_stats WHERE user_id=1 OR user_id=2")
    assert api._dbCursor.fetchone() == (0,)
    
    # Check user cache is deleted
    assert len(api._restAPI__user_cache) == 0


def test_api_user_id(tmp_path):
    api = setup_api(tmp_path=tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test with invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_id({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_id({'user_id':1})
    assert apiError.value.code == 400

    # Test with invalid username
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_id({'username':'a'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_id({'username':['userA','a']})
    assert apiError.value.code == 400

    # Test with unknown username
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_id({'username':'aNonExistantUser'})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_id({'username':['userA','aNonExistantUser']})
    assert apiError.value.code == 404

    # Valid tests
    assert api._api_user_id({'username':'userA'}) == {'userA':1}
    assert api._api_user_id({'username':'userB'}) == {'userB':2}
    assert api._api_user_id({'username':['userA','userB']}) == {'userA':1, 'userB':2}


def test_api_user_friends(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_friends({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_friends({'not_user_id':1})
    assert apiError.value.code == 400

    # Test invalid userID
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_friends({'user_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_friends({'user_id':-1})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_friends({'user_id':4})
    assert apiError.value.code == 404

    # Ensure no users already have friends
    assert api._api_user_friends({'user_id':1}) == {}
    assert api._api_user_friends({'user_id':2}) == {}
    assert api._api_user_friends({'user_id':3}) == {}

    # Add user friends
    api._api_user_addFriend({'user_id':1, 'friend_id':2})
    api._api_user_addFriend({'user_id':1, 'friend_id':3})

    # Register games (for friend stats)
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':3, 'loser_id':1, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':1, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':2, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':3, 'game_type':0, 'winner_id':1, 'loser_id':3, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':4, 'game_type':0, 'winner_id':3, 'loser_id':1, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':5, 'game_type':0, 'winner_id':3, 'loser_id':1, 'winner_points':11, 'loser_points':3, 'sender_id':0})

    # Pull friend data from each user
    friendsA = api._api_user_friends({'user_id':1})
    assert friendsA == {2:{'username':'userB', 'gamesPlayed':2, 'winRate':0.5}, 3:{'username':'userC', 'gamesPlayed':4, 'winRate':0.25}}
    
    friendsB = api._api_user_friends({'user_id':2})
    assert friendsB == {1:{'username':'userA', 'gamesPlayed':2, 'winRate':0.5}}

    friendsC = api._api_user_friends({'user_id':3})
    assert friendsC == {1:{'username':'userA', 'gamesPlayed':4, 'winRate':0.75}}


def test_api_user_addFriend(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'friend_id':2, 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':2, 'friend_username':'userB', 'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid users
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':0, 'friend_id':1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':-1, 'friend_id':1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':4, 'friend_id':1, 'sender_id':0})
    assert apiError.value.code == 404

    # Test that user has edit perms
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':2, 'sender_id':3})
    assert apiError.value.code == 403

    # Test invalid friend IDs
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':-1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':0, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':4, 'sender_id':0})
    assert apiError.value.code == 404

    # Test invalid friend usernames
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_username':'unknown_user', 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_username':'deleted_user', 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_username':'deleted_user', 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_username':'not_a_user', 'sender_id':0})
    assert apiError.value.code == 404

    # Can't friend yourself
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':1, 'sender_id':1})
    assert apiError.value.code == 403

    # Test valid friend registration
    assert api._api_user_addFriend({'user_id':1, 'friend_id':2, 'sender_id':1}) == {'success':True}
    assert api._api_user_addFriend({'user_id':3, 'friend_username':'userA', 'sender_id':3}) == {'success':True}

    # Verify in database
    api._dbCursor.execute("SELECT * FROM friends")
    assert api._dbCursor.fetchall() == [(1,2), (3,1)]

    # Verify duplicates not allowed
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':1, 'friend_id':3, 'sender_id':1})
    assert apiError.value.code == 403
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_addFriend({'user_id':2, 'friend_username':'userA', 'sender_id':2})
    assert apiError.value.code == 403


def test_api_user_removeFriend(tmp_path):
    api = setup_api(tmp_path=tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})
    api._api_user_addFriend({'user_id':1, 'friend_id':2, 'sender_id':0})
    api._api_user_addFriend({'user_id':1, 'friend_id':3, 'sender_id':0})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':1, 'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'friend_id':2, 'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid user ID
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':0, 'friend_id':1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':-1, 'friend_id':1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':4, 'friend_id':1, 'sender_id':0})
    assert apiError.value.code == 404

    # Test invalid friend ID
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':1, 'friend_id':0, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':1, 'friend_id':-1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':1, 'friend_id':4, 'sender_id':0})
    assert apiError.value.code == 404

    # Test invalid perms
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':1, 'friend_id':2, 'sender_id':3})
    assert apiError.value.code == 403

    # Test with users that aren't friends
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_removeFriend({'user_id':2, 'friend_id':3, 'sender_id':2})
    assert apiError.value.code == 404

    # Test valid friendship removal
    assert api._api_user_removeFriend({'user_id':1, 'friend_id':2, 'sender_id':1}) == {'success':True}
    assert api._api_user_removeFriend({'user_id':3, 'friend_id':1, 'sender_id':3}) == {'success':True}

    # Verify in database
    api._dbCursor.execute("SELECT COUNT(*) FROM friends")
    assert api._dbCursor.fetchone() == (0,)


def test_api_user_games(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B', 'userC':'test_pass101C'})
    api._api_game_register({'timestamp': 0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':9})
    api._api_game_register({'timestamp': 1, 'game_type':0, 'winner_id':2, 'loser_id':3, 'winner_points':11, 'loser_points':5})
    api._api_game_register({'timestamp': 2, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3})
    api._api_game_register({'timestamp': 3, 'game_type':0, 'winner_id':3, 'loser_id':1, 'winner_points':11, 'loser_points':8})
    api._api_game_register({'timestamp': 4, 'game_type':0, 'winner_id':3, 'loser_id':2, 'winner_points':11, 'loser_points':6})
    api._api_game_register({'timestamp': 5, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':2})
    api._api_game_register({'timestamp': 6, 'game_type':0, 'winner_id':2, 'loser_id':3, 'winner_points':11, 'loser_points':1})
    api._api_game_register({'timestamp': 7, 'game_type':0, 'winner_id':1, 'loser_id':3, 'winner_points':11, 'loser_points':7})
    api._api_game_register({'timestamp': 8, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':0})
    api._api_game_register({'timestamp': 9, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':6})
    api._api_game_register({'timestamp':10, 'game_type':0, 'winner_id':3, 'loser_id':1, 'winner_points':11, 'loser_points':8})
    api._api_game_register({'timestamp':11, 'game_type':0, 'winner_id':3, 'loser_id':2, 'winner_points':11, 'loser_points':3})
    api._api_game_register({'timestamp':12, 'game_type':0, 'winner_id':1, 'loser_id':3, 'winner_points':11, 'loser_points':4})
    api._api_game_register({'timestamp':13, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':8})
    api._api_game_register({'timestamp':14, 'game_type':0, 'winner_id':3, 'loser_id':2, 'winner_points':11, 'loser_points':4})
    api._api_game_register({'timestamp':15, 'game_type':0, 'winner_id':2, 'loser_id':3, 'winner_points':11, 'loser_points':9})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid user
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({'user_id':-1, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({'user_id':0, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({'user_id':4, 'sender_id':0})
    assert apiError.value.code == 404

    # Test invalid view perms
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({'user_id':2, 'sender_id':1})
    assert apiError.value.code == 403

    # Test with base parameters
    games = api._api_user_games({'user_id':1, 'sender_id':1})
    assert games == {
        'game_ids':[0,2,3,5,7,8,9,10,12,13]
    }
    games = api._api_user_games({'user_id':2, 'sender_id':2})
    assert games == {
        'game_ids':[0,1,2,4,5,6,8,9,11,13,14,15]
    }
    games = api._api_user_games({'user_id':3, 'sender_id':3})
    assert games == {
        'game_ids':[1,3,4,6,7,10,11,12,14,15]
    }

    # Test with opponent_id
    games = api._api_user_games({'user_id':1, 'opponent_id':2, 'sender_id':1})
    assert games == {
        'game_ids':[0,2,5,8,9,13]
    }
    games = api._api_user_games({'user_id':1, 'opponent_id':3, 'sender_id':1})
    assert games == {
        'game_ids':[3,7,10,12]
    }
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_games({'user_id':1, 'opponent_id':5, 'sender_id':1})
    assert apiError.value.code == 404

    # Test with won
    games = api._api_user_games({'user_id':2, 'won':True, 'sender_id':2})
    assert games == {
        'game_ids':[1,5,6,9,13,15]
    }
    games = api._api_user_games({'user_id':2, 'won':False, 'sender_id':2})
    assert games == {
        'game_ids':[0,2,4,8,11,14]
    }

    # Test with min/max time
    games = api._api_user_games({'user_id':3, 'min_time':7, 'sender_id':3})
    assert games == {
        'game_ids':[7,10,11,12,14,15]
    }
    games = api._api_user_games({'user_id':3, 'max_time':9, 'sender_id':3})
    assert games == {
        'game_ids':[1,3,4,6,7]
    }
    games = api._api_user_games({'user_id':3, 'min_time':5, 'max_time':11, 'sender_id':3})
    assert games == {
        'game_ids':[6,7,10,11]
    }

    # Test with mixes of the parameters
    games = api._api_user_games({'user_id':1, 'won':True, 'opponent_id':2, 'sender_id':1})
    assert games == {
        'game_ids':[0,2,8]
    }
    games = api._api_user_games({'user_id':2, 'won':False, 'opponent_id':3, 'sender_id':2})
    assert games == {
        'game_ids':[4,11,14]
    }
    games = api._api_user_games({'user_id':3, 'won':False, 'opponent_id':1, 'min_time':6, 'max_time':10, 'sender_id':3})
    assert games == {
        'game_ids':[7]
    }


def test_api_user_auth(tmp_path):
    api = setup_api(tmp_path=tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'user_id':1})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'username':'userA'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'password':'test_pass101A'})
    assert apiError.value.code == 400

    # Pull valid authentication
    adminKeys = api._api_user_auth({'username':'admin', 'password':'root'})
    userAKeys = api._api_user_auth({'username':'userA', 'password':'test_pass101A'})
    userBKeys = api._api_user_auth({'username':'userB', 'password':'test_pass101B'})

    # Check keys are recorded properly
    assert api._checkApiKey(adminKeys['apiKey']) == 0
    assert api._checkApiKey(userAKeys['apiKey']) == 1
    assert api._checkApiKey(userBKeys['apiKey']) == 2

    # Check renewal keys work
    assert api._api_user_auth_renew(adminKeys)
    assert api._api_user_auth_renew(userAKeys)
    assert api._api_user_auth_renew(userBKeys)

    # Delete user and verify we can't access
    api._api_user_delete({'user_id':2})
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'username':'userB', 'password':'test_pass101B'})
    assert apiError.value.code == 401

    # Check invalid auth
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'username':'admin', 'password':'nope'})
    assert apiError.value.code == 401
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'username':'userA', 'password':'haha'})
    assert apiError.value.code == 401
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth({'username':'nope', 'password':'hehe'})
    assert apiError.value.code == 401


def test_api_user_auth_renew(tmp_path):
    api = setup_api(tmp_path=tmp_path, users={'userA':'test_pass101A'})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({'apiKey':'asjdflkjsldf'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({'renewalKey':'asjdflkjsldf'})
    assert apiError.value.code == 400

    # Get valid keys, wait for them to expire
    api.API_KEY_TIMEOUT = 1
    adminKeys = api._api_user_auth({'username':'admin', 'password':'root'})
    keys = api._api_user_auth({'username':'userA', 'password':'test_pass101A'})
    time.sleep(1)

    # Test incorrect renewal/API key
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({'apiKey':keys['apiKey'], 'renewalKey':'nope'})
    assert apiError.value.code == 401
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({'apiKey':'nope', 'renewalKey':keys['renewalKey']})
    assert apiError.value.code == 401

    # Test non-matching keys
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({'apiKey':adminKeys['apiKey'], 'renewalKey':keys['renewalKey']})
    assert apiError.value.code == 401
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_user_auth_renew({'apiKey':keys['apiKey'], 'renewalKey':adminKeys['renewalKey']})
    assert apiError.value.code == 401

    # Test valid renewal
    assert api._api_user_auth_renew({'apiKey':keys['apiKey'], 'renewalKey':keys['renewalKey']}).keys() == {'apiKey', 'renewalKey'}
    assert api._api_user_auth_renew({'apiKey':adminKeys['apiKey'], 'renewalKey':adminKeys['renewalKey']}).keys() == {'apiKey', 'renewalKey'}

    # Test old keys are removed
    assert adminKeys['apiKey'] not in api._restAPI__apiKeys
    assert keys['apiKey'] not in api._restAPI__apiKeys
    assert adminKeys['renewalKey'] not in api._restAPI__renewalKeys
    assert keys['renewalKey'] not in api._restAPI__renewalKeys


def test_api_game_get(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})
    api._api_game_register({'timestamp': 0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':9})
    api._api_game_register({'timestamp': 1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':4})
    api._api_game_register({'timestamp': 2, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':13, 'loser_points':11})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_get({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_get({'not_game_id':0})
    assert apiError.value.code == 400

    # Test individual requests
    assert api._api_game_get({'game_id':0}) == {0: {'timestamp': 0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':9}}
    assert api._api_game_get({'game_id':1}) == {1: {'timestamp': 1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':4}}
    assert api._api_game_get({'game_id':2}) == {2: {'timestamp': 2, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':13, 'loser_points':11}}

    # Test batch request
    assert api._api_game_get({'game_id':[0,1,2]}) == {
        0: {'timestamp': 0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':9},
        1: {'timestamp': 1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':4},
        2: {'timestamp': 2, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':13, 'loser_points':11}
    }

    # Test invalid game IDs
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_get({'game_id':3})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_get({'game_id':[1,3]})
    assert apiError.value.code == 404


def test_api_game_stats(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A', 'userB':'test_pass101B'})
    # Create games and register stats
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':11, 'loser_points':8, 'sender_id':0})
    api._api_game_registerStats({'user_id':1, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    api._api_game_registerStats({'user_id':2, 'game_id':0, 'swing_count':139, 'swing_hits':83, 'swing_max':23, 'Q1_hits':21, 'Q2_hits':22, 'Q3_hits':21, 'Q4_hits':19, 'sender_id':0})
    api._api_game_registerStats({'user_id':1, 'game_id':1, 'swing_count':161, 'swing_hits':101, 'swing_max':19, 'Q1_hits':26, 'Q2_hits':24, 'Q3_hits':25, 'Q4_hits':26, 'sender_id':0})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_stats({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_stats({'game_id':0, 'sender_id':0})
    assert apiError.value.code == 400

    # Test valid requests
    assert api._api_game_stats({'user_id':2, 'sender_id':2}) == {
        0:{'timestamp':0, 'swing_count':139, 'swing_hits':83, 'hit_percentage':0.5971223021582733, 'swing_max':23, 'Q1_hits':21, 'Q2_hits':22, 'Q3_hits':21, 'Q4_hits':19}
    }
    assert api._api_game_stats({'user_id':1, 'game_id':1, 'sender_id':1}) == {
        1:{'timestamp':1, 'swing_count':161, 'swing_hits':101, 'hit_percentage':0.6273291925465838, 'swing_max':19, 'Q1_hits':26, 'Q2_hits':24, 'Q3_hits':25, 'Q4_hits':26}
    }
    assert api._api_game_stats({'user_id':1, 'game_id':[0,1,2], 'sender_id':1}) == {
        0:{'timestamp':0, 'swing_count':150, 'swing_hits':90, 'hit_percentage':0.6, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22},
        1:{'timestamp':1, 'swing_count':161, 'swing_hits':101, 'hit_percentage':0.6273291925465838, 'swing_max':19, 'Q1_hits':26, 'Q2_hits':24, 'Q3_hits':25, 'Q4_hits':26},
        2:None
    }

    # Test invalid user
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_stats({'user_id':3, 'sender_id':3})
    assert apiError.value.code == 404

    # Test invalid perms
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_stats({'user_id':1, 'sender_id':2})
    assert apiError.value.code == 403


def test_api_game_register(tmp_path):
    api = setup_api(tmp_path, users={'userA':'test_pass101A', 'userB':'test_pass101B'})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'not_right_params':'haha'})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0})
    assert apiError.value.code == 400

    # Test invalid users
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':0, 'loser_id':2, 'winner_points':11, 'loser_points':7})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':3, 'loser_id':2, 'winner_points':11, 'loser_points':7})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':0, 'winner_points':11, 'loser_points':7})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':3, 'winner_points':11, 'loser_points':7})
    assert apiError.value.code == 404

    # Test invalid scores
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':14, 'loser_points':13})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':15, 'loser_points':7})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':8, 'loser_points':10})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':14})
    assert apiError.value.code == 400
    
    # Register valid games
    assert api._api_game_register(
        {'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7}) == {'game_id':0}
    assert api._api_game_register(
        {'timestamp':1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10}) == {'game_id':1}
    assert api._api_game_register(
        {'timestamp':2, 'game_type':0, 'winner_id':2, 'loser_id':-1, 'winner_points':11, 'loser_points':9}) == {'game_id':2}

    # Verify user stats updated
    assert api._api_user_getStats({'user_id':[1,2], 'objects':['gamesPlayed', 'gamesWon', 'averageScore']}) == {
        1: {'gamesPlayed':2, 'gamesWon':1, 'averageScore':10.5},
        2: {'gamesPlayed':3, 'gamesWon':2, 'averageScore':10.0},
    }
    
    # Verify games in database
    api._dbCursor.execute("SELECT * FROM games")
    assert api._dbCursor.fetchall() == [
        (0, 0, 0, 1, 2, 11, 7, '1:2:0'),
        (1, 1, 0, 2, 1, 12, 10, '2:1:1'),
        (2, 2, 0, 2, -1, 11, 9, '2:-1:2')
    ]

    # Attempt to register duplicate games
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':2, 'winner_points':11, 'loser_points':7})
    assert apiError.value.code == 403
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':1, 'game_type':0, 'winner_id':2, 'loser_id':1, 'winner_points':12, 'loser_points':10})
    assert apiError.value.code == 403
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_register({'timestamp':2, 'game_type':0, 'winner_id':2, 'loser_id':-1, 'winner_points':11, 'loser_points':9})
    assert apiError.value.code == 403


def test_api_game_registerStats(tmp_path):
    api = setup_api(tmp_path, useAuth=True, users={'userA':'test_pass101A'})
    api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':1, 'loser_id':-1, 'winner_points':11, 'loser_points':3, 'sender_id':0})
    api._api_game_register({'timestamp':1, 'game_type':0, 'winner_id':-1, 'loser_id':1, 'winner_points':11, 'loser_points':8, 'sender_id':0})

    # Test invalid params
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'sender_id':0})
    assert apiError.value.code == 400
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':1, 'game_id':0, 'sender_id':0})
    assert apiError.value.code == 400

    # Test invalid user
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':-1, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':0, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':2, 'game_id':0, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 404

    # Test with invalid game ID
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':1, 'game_id':-1, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 404
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':1, 'game_id':2, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 404

    # Test with invalid quandrent hits (don't add to total hits)
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':1, 'game_id':1, 'swing_count':150, 'swing_hits':999999, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 400

    # Register valid stats
    assert api._api_game_registerStats({
        'user_id':1,
        'game_id':0,
        'swing_count':150,
        'swing_hits':90,
        'swing_max':20,
        'Q1_hits':23,
        'Q2_hits':24,
        'Q3_hits':21,
        'Q4_hits':22,
        'sender_id':1
    }) == {'success':True}
    assert api._api_game_registerStats({
        'user_id':1,
        'game_id':1,
        'swing_count':161,
        'swing_hits':101,
        'swing_max':19,
        'Q1_hits':26,
        'Q2_hits':24,
        'Q3_hits':25,
        'Q4_hits':26,
        'sender_id':1
    }) == {'success':True}

    # Verify stats in database
    api._dbCursor.execute("SELECT * FROM user_game_stats")
    assert api._dbCursor.fetchall() == [
        (1,0,150,90,20,23,24,21,22),
        (1,1,161,101,19,26,24,25,26)
    ]

    # Test registering stats for game/user with stats already registered
    with pytest.raises(restAPI.APIError) as apiError:
        api._api_game_registerStats({'user_id':1, 'game_id':1, 'swing_count':150, 'swing_hits':90, 'swing_max':20, 'Q1_hits':23, 'Q2_hits':24, 'Q3_hits':21, 'Q4_hits':22, 'sender_id':0})
    assert apiError.value.code == 403
