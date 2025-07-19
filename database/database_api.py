import os
import sqlite3
import hashlib
import base64
import string

class restAPI:
    """A RESTful API for the database server of PicklePals. Also controls the SQLite database directly"""

    class APIError(Exception):
        """An error triggered by the restAPI itself, including an HTTP error code"""

        def __init__(self, message: str, code: int):
            """Creates an exception for an error triggered by the database, including HTTP error code

            Args:
                message (str): Message to include in the exception
                code (int): HTTP status code to send with the response message
            """
            self.message = message
            self.code = code
            super().__init__(self.message)


    def __init__(self, dbFile:str = 'pickle.db', useAuth:bool = True, clearDB:bool = False):
        """Creates a RESTful API instance and loads an attached SQLite database

        Args:
            dbFile (str, optional): Filepath to the SQLite database file. Defaults to 'pickle.db' in the pwd.
            useAuth (bool, optional): Set to False to disable authentication checks. Defaults to True.
        """
        self.dbFile = dbFile

        if clearDB and os.path.isfile(dbFile):
            os.remove(dbFile)

        self._database = sqlite3.connect(dbFile)
        self._dbCursor = self._database.cursor()
        self._useAuth = useAuth
        self.__apiKeys = {}

        self._dbCursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        count = self._dbCursor.fetchone()[0]
        if count == 0:
            self._init_db()

        
    def handle_request(self, uri:str, params:dict, api_key:str = None):
        """Handles an API request given a url endpoint and parameters

        Args:
            url (str): The api endpoint to post to, in URL format. should start with '/pickle/'
            params (dict): Dictionary of parameters used by the endpoint
            api_key (str, optional): API key for authenticating user. Defaults to None (unauthenticated).

        Raises:
            self.APIError: Any error triggered by the API itself, such as invalid user ID or authentication required

        Returns:
            dict: dictionary of return values (dependent on endpoint)
        """
        try:
            uri_parts = uri[1:].split('/',1)
            if uri_parts[0] != 'pickle':
                raise self.APIError(f'Base endpoint must be "pickle/": {uri_parts[0]}', 404)
            
            endpoint = uri_parts[1].replace('/', '_')

            if self._useAuth and (endpoint not in ("user_create", "user_auth", 'coffee')):
                sender_id = self._checkApiKey(api_key)
                params['sender_id'] = sender_id

                if not api_key:
                    raise self.APIError('Authentication required, please obtain an API key through pickle/user/auth', 401)

                if not sender_id:
                    raise self.APIError('API key not recognized, could be out of date or server has restarted. Try requesting another one with pickle/user/auth', 401)
            
            func = getattr(self, "_api_" + endpoint, None)
            if func:
                return func(params)
            
            else:
                raise self.APIError(f'Endpoint not found: {uri}', 404)
        
        except Exception as error:
            del params
            del api_key
            raise error


    def _init_db(self):
        self._dbCursor.execute('CREATE TABLE users(user_id INT, username TEXT, passwordHash BLOB, salt BLOB, valid INT, gamesPlayed INT, gamesWon INT, averageScore REAL)')
        self._dbCursor.execute('CREATE TABLE games(game_id INT, timestamp INT, game_type INT, winner_id INT, loser_id INT, winner_points INT, loser_points INT)')
        self._dbCursor.execute('CREATE TABLE user_game_stats(user_id INT, game_id INT, swing_count INT, swing_hits INT, swing_min REAL, swing_max REAL, swing_avg REAL, hit_modeX REAL, hit_modeY REAL, hit_avgX REAL, hit_avgY REAL)')
        self._dbCursor.execute('CREATE TABLE friends(userA INT, userB INT)')

        pass_hash, salt = self.gen_password_hash('root')
        self._dbCursor.execute("INSERT INTO users VALUES (0, 'admin', ?, ?, 0, NULL, NULL, NULL)", (pass_hash, salt))
        self._database.commit()
        
        
    def _check_username(self, username: str):
        if not 5 <= len(username) <=25:
            return False
        
        if username in ('admin', 'deleted_user', 'unknown_user'):
            return False
        
        if not username.isascii() or not username.isprintable() or ' ' in username:
            return False

        return True
    
    def _check_password(self, password: str):
        if password in ('password', 'query', '123456789', '123456', 'secret'):
            return False
        
        if not 10 <= len(password) <= 50:
            return False
        
        if not password.isprintable() or not password.isascii():
            return False
        
        if not any(char.isdigit() for char in password):
            return False
        
        if not any(char.isalpha() for char in password):
            return False
        
        if not any(char.isupper() for char in password):
            return False
        
        if not any(char.islower() for char in password):
            return False
        
        if not any(char in password for char in string.punctuation):
            return False
        
        return True
    
    def _is_username_existing(self, username: str):
        self._dbCursor.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
        return self._dbCursor.fetchone()[0] > 0
        
    def _is_user_account_valid(self, user_id: int):
        self._dbCursor.execute("SELECT valid FROM users WHERE user_id=?", (user_id,))
        valid = self._dbCursor.fetchone()
        return valid and valid[0]
    
    def _is_user_id_valid(self, user_id: int):
        return user_id == -1 or self._is_user_account_valid(user_id)
    
    def _is_user_deleted(self, user_id: int):
        self._dbCursor.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
        deleted = self._dbCursor.fetchone()
        return deleted and deleted[0] == 'deleted_user'
    
    def _are_users_friends(self, userA: int, userB: int):
        self._dbCursor.execute("SELECT * FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (userA, userB, userB, userA))
        is_friend = self._dbCursor.fetchone()

        if is_friend:
            return True
        else:
            return False
    
    def _user_canView(self, sender_id: int, user_id: int):
        if not self._useAuth:
            return True

        if sender_id is None:
            return False
        
        if sender_id == 0 or sender_id == user_id:
            return True
        
        return self._are_users_friends(sender_id, user_id)
    
    def _user_canEdit(self, sender_id: int, user_id: int):
        if not self._useAuth or sender_id == 0:
            return True

        if sender_id is None:
            return False
        
        return sender_id == user_id

    @staticmethod
    def gen_password_hash(password:str):
        salt = bytearray(os.urandom(16))
        hash = bytearray(hashlib.sha256(salt + password.encode()).digest())
        return hash, salt
    
    def _check_userAuth(self, username:str, password:str):
        self._dbCursor.execute("SELECT passwordHash, salt FROM users WHERE username=?", (username,))
        data = self._dbCursor.fetchone()
        if not data:
            return False

        dbHash = data[0]
        salt = data[1]
        userHash = bytearray(hashlib.sha256(salt + password.encode()).digest())
        return userHash == dbHash
    
    def _checkApiKey(self, apiKey:str):
        user_id = self.__apiKeys.get(apiKey)
        return user_id
    

    def _api_user_get(self, params: dict):
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters for pickle/user/get, must include user ID: {params}', 400)
        
        user_ids = params['user_id']
        if type(user_ids) is int:
            user_ids = [user_ids]

        result_dict = {}
        for user_id in user_ids:

            if not self._is_user_deleted(user_id) and not self._is_user_account_valid(user_id):
                raise self.APIError(f'User ID {user_id} is not a valid user', 404)

            if not self._user_canView(params.get('sender_id'), user_id):
                raise self.APIError(f'Access forbidden to user ID {user_id}', 403)
            
            if 'objects' in params:
                objects = params['objects']
            else:
                objects = ['username', 'gamesPlayed', 'gamesWon', 'averageScore']

            results = {}
            for object in objects:
                if object in ('username', 'gamesPlayed', 'gamesWon', 'averageScore'):
                    self._dbCursor.execute(f"SELECT {object} FROM users WHERE user_id=?", (user_id,))
                    results[object] = self._dbCursor.fetchone()[0]

                else:
                    raise self.APIError(f'ERROR: invalid object requested: {object}', 400)
            
            result_dict[user_id] = results

        return result_dict
    
    
    def _api_user_set(self, params: dict):
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters for PUT pickle/user, must include user ID: {params}', 400)
        
        user_id = int(params['user_id'])
        
        if not self._user_canEdit(params.get('sender_id'), user_id):
            raise self.APIError(f'Access forbidden to user ID {user_id}', 403)

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        if ('username') not in params.keys():
            raise self.APIError(f'No valid user values where found, nothing to set: {params.keys}', 400)

        for param, val in params.items():
            if param == 'username':
                if not self._check_username(val):
                    raise self.APIError(f'Invalid username {val}', 400)
                
                if self._is_username_existing(val):
                    raise self.APIError(f'Username {val} already exists', 403)

                self._dbCursor.execute("UPDATE users SET username=? WHERE user_id=?", (val, user_id))

            elif param != 'user_id':
                print(f'Invalid object parameter: {param}={val}')

        self._database.commit()
        return {'success':True}
    

    def _api_user_create(self, params: dict):
        if 'username' not in params or 'password' not in params:
            raise self.APIError(f'Invalid parameters for POST pickle/user, must include username and password: {params}', 400)
        
        username = params['username']
        password = params['password']
        # TODO: password authentication
        # TODO: check that username doesn't already exist

        if not self._check_username(username):
            raise self.APIError(f'Invalid username {username}', 400)
        
        if self._is_username_existing(username):
            raise self.APIError(f'Username {username} already exists', 403)
        
        if not self._check_password(password):
            raise self.APIError(f'Invalid password "{password}", must be at least 10 characters long.', 400)

        pass_hash, salt = self.gen_password_hash(password)

        self._dbCursor.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
        user_id = self._dbCursor.fetchone()[0] + 1

        self._dbCursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, 1, 0, 0, 0.0)", (user_id, username, pass_hash, salt))
        self._database.commit()
        return {'user_id':user_id}
    

    def _api_user_delete(self, params: dict):
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters for DELETE pickle/user, must include user ID: {params}', 400)
        
        user_id = int(params['user_id'])
        
        if not self._user_canEdit(params.get('sender_id'), user_id):
            raise self.APIError(f'Access forbidden to user ID {user_id}', 403)

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)

        self._dbCursor.execute("UPDATE users SET username='deleted_user', passwordHash=NULL, salt=NULL, valid=0, gamesPlayed=NULL, gamesWon=NULL, averageScore=NULL WHERE user_id=?", (user_id,))
        self._dbCursor.execute("DELETE FROM friends WHERE userA=? OR userB=?", (user_id, user_id))
        self._dbCursor.execute("DELETE FROM user_game_stats WHERE user_id=?", (user_id,))
        self._database.commit()
        return {'success':True}
            
    
    def _api_user_id(self, params: dict):
        
        if 'username' not in params:
            raise self.APIError('GET pickle/user/id requires the parameter "username"', 400)
        
        usernames = params['username']
        if type(usernames) is not list:
            usernames = [usernames]

        result_dict = {}
        for username in usernames:
            if not self._check_username(username):
                raise self.APIError(f'Invalid username {username}', 400)
            
            self._dbCursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            user_id = self._dbCursor.fetchone()

            if user_id:
                if self._user_canView(params.get('sender_id'), user_id[0]):
                    result_dict[username] = user_id[0]
                else:
                    raise self.APIError(f'Access forbidden to user ID {user_id[0]}', 403)
            
            else:
                raise self.APIError(f'Username not found: {username}', 404)
            
        return result_dict
        
        
    def _api_user_friends(self, params: dict):
        if 'user_id' not in params:
            raise self.APIError('ERROR: pickle/user/friends must include "user_id" parameter', 400)

        user_id = int(params['user_id'])

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)

        self._dbCursor.execute("SELECT (CASE WHEN userA=? THEN userB ELSE userA END) FROM friends WHERE (userA=? OR userB=?)", (user_id, user_id, user_id,))
        friend_list = self._dbCursor.fetchall()

        username_list = []
        for id in friend_list:
            self._dbCursor.execute("SELECT username FROM users WHERE user_id=?", (id[0],))
            username_list.append(self._dbCursor.fetchone()[0])

        games_list = []
        winRate_list = []
        for id in friend_list:
            self._dbCursor.execute("SELECT COUNT(*) FROM games WHERE (winner_id=? AND loser_id=?) OR (winner_id=? AND loser_id=?)", (user_id, id[0], id[0], user_id))
            gameCount = self._dbCursor.fetchone()[0]
            games_list.append(gameCount)

            if gameCount > 0:
                self._dbCursor.execute("SELECT COUNT(*) FROM games WHERE winner_id=? AND loser_id=?", (user_id, id[0]))
                winCount = self._dbCursor.fetchone()[0]
                winRate_list.append(winCount / gameCount)

            else:
                winRate_list.append(None)
                

        result = {}
        for i in range(0, len(friend_list)):
            result[friend_list[i][0]] = {'username':username_list[i], 'gamesPlayed':games_list[i], 'winRate':winRate_list[i]}
        
        return result
    

    def _api_user_addFriend(self, params: dict):
        if 'user_id' not in params:
            raise self.APIError('ERROR: pickle/user/friends must include "user_id" parameter', 400)

        user_id = int(params['user_id'])

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        if 'friend_id' in params:
            friend_id = int(params['friend_id'])
            if not self._is_user_account_valid(friend_id):
                raise self.APIError(f'User ID {friend_id} is not a valid user', 404)

        elif 'friend_username' in params:
            username = params['friend_username']

            self._dbCursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            raw_id = self._dbCursor.fetchone()
            if not raw_id:
                raise self.APIError(f'ERROR: unable to find user with username "{username}"', 404)
            
            friend_id = raw_id[0]

        else:
            raise self.APIError('ERROR: POST pickle/user/friends requires either "friend_id" or "friend_username" parameter.', 400)
        
        # if not self._user_canView(params.get('sender_id'), friend_id):
        #     raise self.APIError(f'Access forbidden to user ID {friend_id}', 403)
        
        self._dbCursor.execute("SELECT COUNT(*) FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (user_id, friend_id, friend_id, user_id))
        existing_count = self._dbCursor.fetchone()[0]

        if existing_count > 0:
            raise self.APIError('Users are already friends', 403)
        
        self._dbCursor.execute("INSERT INTO friends VALUES (?, ?)", (user_id, friend_id))
        self._database.commit()
        return {'success':True}
    

    def _api_user_removeFriend(self, params: dict):
        if 'user_id' not in params:
            raise self.APIError('ERROR: pickle/user/friends must include "user_id" parameter', 400)

        user_id = int(params['user_id'])

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)

        if 'friend_id' not in params:
            raise self.APIError('ERROR: DELETE pickle/user/friends must include "friend_id" parameter', 400)

        friend_id = int(params['friend_id'])

        if not self._is_user_account_valid(friend_id):
            raise self.APIError(f'User ID {friend_id} is not a valid user', 404)
        
        self._dbCursor.execute("DELETE FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (user_id, friend_id, friend_id, user_id))
        self._database.commit()
        return {'success':True}
        

    def _api_user_games(self, params: dict):
        user_id = int(params['user_id'])
        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        if 'opponent_id' in params:
            opponent_id = int(params['opponent_id'])
            if not self._is_user_id_valid(opponent_id):
                raise self.APIError(f'Opponent user ID {opponent_id} is not a valid user', 404)
        else:
            opponent_id = None
        
        request = "SELECT game_id FROM games WHERE "
        request_params = []

        if 'won' in params:
            if bool(params['won']) == True:
                request += "winner_id=?"
                request_params.append(user_id)

                if opponent_id:
                    request += " AND loser_id=?"
                    request_params.append(opponent_id)

            else:
                request += "loser_id=?"
                request_params.append(user_id)

                if opponent_id:
                    request += " AND winner_id=?"
                    request_params.append(opponent_id)
        
        else:
            if opponent_id:
                request += "((winner_id=? AND loser_id=?) OR (winner_id=? AND loser_id=?))"
                request_params.extend((user_id, opponent_id, opponent_id, user_id))

            else:
                request += "(winner_id=? OR loser_id=?)"
                request_params.extend((user_id, user_id))


        if 'min_time' in params:
            request += " AND timestamp >=?"
            request_params.append(int(params['min_time']))

        if 'max_time' in params:
            request += " AND timestamp <=?"
            request_params.append(int(params['max_time']))


        self._dbCursor.execute(request, request_params)
        games_list = self._dbCursor.fetchall()
        result = {'game_ids': [game[0] for game in games_list]}
        return result
        
    
    def _api_user_auth(self, params: dict):
        if 'username' not in params or 'password' not in params:
            raise self.APIError(f'Invalid parameters for POST pickle/user, must include username and password: {params}', 400)
        
        username = params['username']
        password = params['password']

        if self._check_userAuth(username, password):
            self._dbCursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            user_id = self._dbCursor.fetchone()[0]

            rand_val = os.urandom(12)
            api_key = base64.b64encode(rand_val).decode('utf-8')
            self.__apiKeys[api_key] = user_id

            print(f'Authentication successful for user {username}')
            return {'success':True, 'apiKey':api_key}
        
        else:
            raise self.APIError(f'Authentication failed for user {username}', 401)
    

    def _api_game_get(self, params: dict):
        if 'game_id' not in params:
            raise self.APIError(f'ERROR: GET pickle/game must specify game_id parameter!', 400)
        
        game_ids = params['game_id']
        if type(game_ids) is not list:
            game_ids = [game_ids]

        result_dict = {}
        for game_id in game_ids:
            self._dbCursor.execute("SELECT * FROM games WHERE game_id=?", (game_id,))
            game = self._dbCursor.fetchone()

            if not game:
                raise self.APIError(f'Game for game_id {game_id} not found', 404)

            result_dict[game[0]] = {'timestamp':game[1], 'game_type':game[2], 'winner_id':game[3], 'loser_id':game[4], 'winner_points':game[5], 'loser_points':game[6]}
        
        return result_dict
    

    def _api_game_stats(self, params: dict):
        
        user_id = int(params['user_id'])
        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)

        stats = {}
        if 'game_id' in params:
            game_ids = params['game_id']
            if type(game_ids) is not list:
                game_ids = [game_ids]

        else:
            self._dbCursor.execute("SELECT game_id FROM user_game_stats WHERE user_id=?", (user_id,))
            game_ids = [id[0] for id in self._dbCursor.fetchall()]

        for id in game_ids:
                self._dbCursor.execute("SELECT timestamp FROM games WHERE game_id=?", (id,))
                timestamp = self._dbCursor.fetchone()

                if timestamp:
                    self._dbCursor.execute("SELECT * FROM user_game_stats WHERE game_id=? AND user_id=?", (id, user_id))
                    game_stats = self._dbCursor.fetchone()

                    stats[id] = {
                        "timestamp":timestamp[0],
                        "swing_count": game_stats[2],
                        "swing_hits": game_stats[3],
                        "hit_percentage": game_stats[3] / game_stats[2],
                        "swing_min": game_stats[4],
                        "swing_max": game_stats[5],
                        "swing_avg": game_stats[6],
                        "hit_modeX": game_stats[7],
                        "hit_modeY": game_stats[8],
                        "hit_avgX": game_stats[9],
                        "hit_avgY": game_stats[10]
                    }
                else:
                    stats[id] = None

        return stats


    def _api_game_register(self, params: dict):
        if any(key not in params for key in ('timestamp', 'game_type', 'winner_id', 'loser_id', 'winner_points', 'loser_points')):
            print(f'Invalid parameters for POST pickle/game: {params}')

        timestamp = int(params['timestamp'])
        game_type = int(params['game_type'])
        winner_id = int(params['winner_id'])
        loser_id = int(params['loser_id'])
        winner_points = int(params['winner_points'])
        loser_points = int(params['loser_points'])

        if not self._is_user_id_valid(winner_id):
            raise self.APIError(f'User ID {winner_id} is not a valid user', 404)
        
        if not self._is_user_id_valid(loser_id):
            raise self.APIError(f'User ID {loser_id} is not a valid user', 404)

        self._dbCursor.execute("SELECT game_id FROM games ORDER BY game_id DESC LIMIT 1")
        game_id_raw = self._dbCursor.fetchone()
        if game_id_raw:
            game_id = game_id_raw[0] + 1
        else:
            game_id = 0

        self._dbCursor.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?)",
            (game_id, timestamp, game_type, winner_id, loser_id, winner_points, loser_points))
        self._database.commit()

        self.updateUserGameStats(winner_id)
        self.updateUserGameStats(loser_id)

        return {'game_id':game_id}


    def _api_game_registerStats(self, params: dict):
        # if any(key not in params for key in ('timestamp', 'game_type', 'winner_id', 'loser_id', 'winner_points', 'loser_points')):
        #     print(f'Invalid parameters for POST pickle/game: {params}')

        user_id = int(params['user_id'])
        game_id = int(params['game_id'])
        swing_count = int(params['swing_count'])
        swing_hits = int(params['swing_hits'])
        swing_min = float(params['swing_min'])
        swing_max = float(params['swing_max'])
        swing_avg = float(params['swing_avg'])
        hit_modeX = float(params['hit_modeX'])
        hit_modeY = float(params['hit_modeY'])
        hit_avgX = float(params['hit_avgX'])
        hit_avgY = float(params['hit_avgY'])

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        # if not self._is_user_valid(loser_id):
        #     raise self.APIError(f'User ID {loser_id} is not a valid user', 404)

        self._dbCursor.execute(
            "INSERT INTO user_game_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, game_id, swing_count, swing_hits, swing_min, swing_max, swing_avg, hit_modeX, hit_modeY, hit_avgX, hit_avgY))
        self._database.commit()

        # self.updateUserGameStats(winner_id)
        # self.updateUserGameStats(loser_id)

        return {'success':True}

        
    def _api_coffee(self, params: dict):
        raise self.APIError("Why...? We don't serve coffee here, just... idk, go find a cafe or something, maybe there's a pickleball court nearby.", 418)
        

    def updateUserGameStats(self, user_id: int):

        if not self._is_user_account_valid(user_id):
            return False

        self._dbCursor.execute('SELECT COUNT(*) FROM games WHERE winner_id=? OR loser_id=?', (user_id, user_id))
        gamesPlayed = self._dbCursor.fetchone()[0]

        self._dbCursor.execute('SELECT COUNT(*) FROM games WHERE winner_id=?', (user_id,))
        gamesWon = self._dbCursor.fetchone()[0]

        self._dbCursor.execute('SELECT AVG(CASE WHEN winner_id=? THEN winner_points ELSE loser_points END) FROM games WHERE winner_id=? OR loser_id=?', (user_id, user_id, user_id))
        averageScore = self._dbCursor.fetchone()[0]

        self._dbCursor.execute('UPDATE users SET gamesPlayed=?, gamesWon=?, averageScore=? WHERE user_id=?', (gamesPlayed, gamesWon, averageScore, user_id))
        self._database.commit()
        return True
    

    def openCon(self):
        self._database = sqlite3.connect(self.dbFile)
        self._dbCursor = self._database.cursor()

    def close(self):
        self._dbCursor.close()
        self._database.close()
        self.__apiKeys.clear()
