import os
import sqlite3
import hashlib
import base64

class restAPI:

    class ValidationError(Exception):
        def __init__(self, val, dataType):
            self.message = f'data validation error for value "{val}" to type "{dataType}"'
            super().__init__(self.message)


    def __init__(self, dbFile = 'pickle.db', useAuth = True):
        self.dbFile = dbFile
        self.dbCon = sqlite3.connect(self.dbFile)
        self.cursor = self.dbCon.cursor()
        self.useAuth = useAuth
        self.apiKey_list = {}


    def check_str(self, string: str):
        if string.find("'") == -1:
            return string
        
        else:
            raise self.ValidationError(string, 'str')

    def check_int(self, val):
        try:
            return int(val)
        
        except ValueError as error:
            raise self.ValidationError(val, 'int')

    def check_float(self, val):
        try:
            return float(val)
        
        except ValueError as error:
            raise self.ValidationError(val, 'float')
        
    def check_username(self, username: str):
        return username not in ('admin', 'deleted_user')
    
    def is_username_existing(self, username: str):
        self.cursor.execute("SELECT username FROM users WHERE username=?", (username,))
        return self.cursor.fetchone() is not None

    @staticmethod
    def gen_password_hash(password:str):
        salt = bytearray(os.urandom(16))
        hash = bytearray(hashlib.sha256(salt + password.encode()).digest())
        return hash, salt
    
    def check_password(self, username:str, password:str):
        self.cursor.execute("SELECT passwordHash, salt FROM users WHERE username=?", (username,))
        data = self.cursor.fetchone()
        if not data:
            return False

        dbHash = data[0]
        salt = data[1]
        userHash = bytearray(hashlib.sha256(salt + password.encode()).digest())
        return userHash == dbHash
        
    def is_user_valid(self, user_id):
        self.cursor.execute("SELECT valid FROM users WHERE user_id=?", (user_id,))
        valid = self.cursor.fetchone()
        return valid and valid[0]
    
    def is_user_deleted(self, user_id):
        self.cursor.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
        deleted = self.cursor.fetchone()
        return deleted and deleted[0] == 'deleted_user'
    
    def are_users_friends(self, userA, userB):
        self.cursor.execute("SELECT * FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (userA, userB, userB, userA))
        is_friend = self.cursor.fetchone()

        if is_friend:
            return True
        else:
            return False
    
    def checkApiKey(self, apiKey):
        user_id = self.apiKey_list.get(apiKey)
        return user_id
    
    def user_canView(self, sender_id, user_id):
        if not self.useAuth:
            return True

        if not sender_id:
            return False
        
        if sender_id == 0 or sender_id == user_id:
            return True
        
        return self.are_users_friends(sender_id, user_id)
    
    
    def user_canEdit(self, sender_id, user_id):
        if not self.useAuth or sender_id == 0:
            return True

        if not sender_id:
            return False
        
        if sender_id == 0:
            return True
        
        return sender_id == user_id
        


    def handle_request(self, url:str, params:dict, api_key:str = None):

        url_parts = url[1:].split('/',1)
        if url_parts[0] != 'pickle':
            return f'Base endpoint must be "pickle/": {url_parts[0]}', 404
        
        endpoint = url_parts[1].replace('/', '_')

        if self.useAuth and endpoint != "user_auth":
            sender_id = self.checkApiKey(api_key)
            params['sender_id'] = sender_id

            if not sender_id:
                return f'Authentication required, please obtain an API ket through pickle/user/auth', 401
        
        func = getattr(self, "api_" + endpoint, None)
        if func:
            return func(params)
        
        else:
            return f'Endpoint not found: {url}', 404
    

    def api_user_get(self, params: dict):
        if 'user_id' not in params:
            return f'Invalid parameters for GET pickle/user, must include user ID: {params}', 405
        
        user_ids = params['user_id']
        if type(user_ids) is int:
            user_ids = [user_ids]

        result_dict = {}
        for user_id in user_ids:

            if not self.user_canView(params.get('sender_id'), user_id):
                return f'Access forbidden to user ID {user_id}', 403

            if not self.is_user_deleted(user_id) and not self.is_user_valid(user_id):
                return f'User ID {user_id} is not a valid user', 404
            
            if 'objects' in params:
                objects = params['objects']
            else:
                objects = ['username', 'gamesPlayed', 'gamesWon', 'averageScore']

            results = {}
            for object in objects:
                if object in ('username', 'gamesPlayed', 'gamesWon', 'averageScore'):
                    self.cursor.execute(f"SELECT {object} FROM users WHERE user_id=?", (user_id,))
                    results[object] = self.cursor.fetchone()[0]

                else:
                    return f'ERROR: invalid object requested: {object}', 400
            
            result_dict[user_id] = results

        return result_dict, 200
    
    
    def api_user_set(self, params: dict):
        if 'user_id' not in params:
            return f'Invalid parameters for PUT pickle/user, must include user ID: {params}', 400
        
        user_id = self.check_int(params['user_id'])
        
        if not self.user_canEdit(params.get('sender_id'), user_id):
            return f'Access forbidden to user ID {user_id}', 403

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404

        for param, val in params.items():

            if param == 'username':
                if not self.check_username(val):
                    return f'Invalid username {val}', 400
                
                if self.is_username_existing(val):
                    return f'Username {val} already exists', 403

                self.cursor.execute("UPDATE users SET username=? WHERE user_id=?", (val, user_id))

            elif param != 'user_id':
                print(f'Invalid object parameter: {param}={val}')

        self.dbCon.commit()
        return {'success':True}, 200
    

    def api_user_create(self, params: dict):
        if 'username' not in params or 'password' not in params:
            return f'Invalid parameters for POST pickle/user, must include username and password: {params}', 400
        
        username = self.check_str(params['username'])
        password = self.check_str(params['password'])
        # TODO: password authentication
        # TODO: check that username doesn't already exist

        if not self.check_username(username):
            return f'Invalid username {username}', 400
        
        if self.is_username_existing(username):
            return f'Username {username} already exists', 403

        pass_hash, salt = self.gen_password_hash(password)

        self.cursor.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
        user_id = self.cursor.fetchone()[0] + 1

        self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, 1, 0, 0, 0.0)", (user_id, username, pass_hash, salt))
        self.dbCon.commit()
        return {'user_id':user_id}, 200
    

    def api_user_delete(self, params: dict):
        if 'user_id' not in params:
            return f'Invalid parameters for DELETE pickle/user, must include user ID: {params}', 400
        
        user_id = self.check_int(params['user_id'])
        
        if not self.user_canEdit(params.get('sender_id'), user_id):
            return f'Access forbidden to user ID {user_id}', 403

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404

        self.cursor.execute("UPDATE users SET username='deleted_user', passwordHash=NULL, salt=NULL, valid=0, gamesPlayed=NULL, gamesWon=NULL, averageScore=NULL WHERE user_id=?", (user_id,))
        self.dbCon.commit()
        return {'success':True}, 200
            
    
    def api_user_id(self, params: dict):
        
        if len(params) != 1 or 'username' not in params:
            return 'GET pickle/user/id requires the parameter "username"', 400
        
        usernames = params['username']
        if type(usernames) is not list:
            usernames = [usernames]

        result_dict = {}
        for username in usernames:
            if not self.check_username(username):
                return f'Invalid username {username}', 400
            
            self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            user_id = self.cursor.fetchone()

            if user_id:
                if self.user_canView(params.get('sender_id'), user_id[0]):
                    result_dict[username] = user_id[0]
                else:
                    return f'Access forbidden to user ID {user_id[0]}', 403
            
            else:
                return f'Username not found: {username}', 404
            
        return result_dict, 200
        
        
    def api_user_friends(self, params: dict):
        if 'user_id' not in params:
            return 'ERROR: pickle/user/friends must include "user_id" parameter', 400

        user_id = self.check_int(params['user_id'])

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404

        self.cursor.execute("SELECT (CASE WHEN userA=? THEN userB ELSE userA END) FROM friends WHERE (userA=? OR userB=?)", (user_id, user_id, user_id,))
        friend_list = self.cursor.fetchall()

        username_list = []
        for id in friend_list:
            self.cursor.execute("SELECT username FROM users WHERE user_id=?", (id[0],))
            username_list.append(self.cursor.fetchone()[0])

        result = {}
        for i in range(0, len(friend_list)):
            result[friend_list[i][0]] = {'username':username_list[i]}
        
        return result, 200
    

    def api_user_addFriend(self, params: dict):
        if 'user_id' not in params:
            return 'ERROR: pickle/user/friends must include "user_id" parameter', 400

        user_id = self.check_int(params['user_id'])

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404
        
        if 'friend_id' in params:
            friend_id = self.check_int(params['friend_id'])
            if not self.is_user_valid(friend_id):
                return f'User ID {friend_id} is not a valid user', 404

        elif 'friend_username' in params:
            username = self.check_str(params['friend_username'])

            self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            raw_id = self.cursor.fetchone()
            if not raw_id:
                return f'ERROR: unable to find user with username "{username}"', 404
            
            friend_id = raw_id[0]

        else:
            return 'ERROR: POST pickle/user/friends requires either "friend_id" or "friend_username" parameter.', 400
        
        if not self.user_canView(params.get('sender_id'), friend_id):
            return f'Access forbidden to user ID {friend_id}', 403
        
        self.cursor.execute("INSERT INTO friends VALUES (?, ?)", (user_id, friend_id))
        self.dbCon.commit()
        return {'success':True}, 200
    

    def api_user_removeFriend(self, params: dict):
        if 'user_id' not in params:
            return 'ERROR: pickle/user/friends must include "user_id" parameter', 400

        user_id = self.check_int(params['user_id'])

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404

        if 'friend_id' not in params:
            return 'ERROR: DELETE pickle/user/friends must include "friend_id" parameter', 400

        friend_id = self.check_int(params['friend_id'])

        if not self.is_user_valid(friend_id):
            return f'User ID {friend_id} is not a valid user', 404
        
        self.cursor.execute("DELETE FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (user_id, friend_id, friend_id, user_id))
        self.dbCon.commit()
        return {'success':True}, 200
        

    def api_user_games(self, params: dict):
        user_id = self.check_int(params['user_id'])

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404
        
        if 'won' in params:
            if params['won'] == True:
                self.cursor.execute("SELECT game_id FROM games WHERE winner_id=?", (user_id,))

            elif params['won'] == False:
                self.cursor.execute("SELECT game_id FROM games WHERE loser_id=?", (user_id,))

            else:
                return f'Invalid value for parameter "won" in GET pickle/user/games: {user_id}', 400
            
        else:
            self.cursor.execute("SELECT game_id FROM games WHERE winner_id=? OR loser_id=?", (user_id, user_id))

        games_list = self.cursor.fetchall()
        result = {'game_ids': [game[0] for game in games_list]}
        return result, 200
        
    
    def api_user_auth(self, params: dict):
        if 'username' not in params or 'password' not in params:
            return f'Invalid parameters for POST pickle/user, must include username and password: {params}', 400
        
        username = self.check_str(params['username'])
        password = self.check_str(params['password'])

        if self.check_password(username, password):
            self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            user_id = self.cursor.fetchone()[0]

            rand_val = os.urandom(12)
            api_key = base64.b64encode(rand_val).decode('utf-8')
            self.apiKey_list[api_key] = user_id

            print(f'Authentication successful for user {username}')
            return {'success':True, 'apiKey':api_key}, 200
        
        else:
            return f'Authentication failed for user {username}', 401
    

    def api_game_get(self, params: dict):
        if 'game_id' not in params:
            return f'ERROR: GET pickle/game must specify game_id parameter!', 400
        
        game_ids = params['game_id']
        if type(game_ids) is not list:
            game_ids = [game_ids]

        result_dict = {}
        for game_id in game_ids:
            self.cursor.execute("SELECT * FROM games WHERE game_id=?", (game_id,))
            game = self.cursor.fetchone()

            if not game:
                return f'Game for game_id {game_id} not found', 404

            result_dict[game[0]] = {'winner_id':game[1], 'loser_id':game[2], 'winner_points':game[3], 'loser_points':game[4]}
        
        return result_dict, 200
    

    def api_game_register(self, params: dict):
        if any(key not in params for key in ('winner_id', 'loser_id', 'winner_points', 'loser_points')):
            print(f'Invalid parameters for POST pickle/game: {params}')

        winner_id = self.check_int(params['winner_id'])
        loser_id = self.check_int(params['loser_id'])
        winner_points = self.check_int(params['winner_points'])
        loser_points = self.check_int(params['loser_points'])

        if not self.is_user_valid(winner_id):
            return f'User ID {winner_id} is not a valid user', 404
        
        if not self.is_user_valid(loser_id):
            return f'User ID {loser_id} is not a valid user', 404

        self.cursor.execute("SELECT game_id FROM games ORDER BY game_id DESC LIMIT 1")
        game_id_raw = self.cursor.fetchone()
        if game_id_raw:
            game_id = game_id_raw[0] + 1
        else:
            game_id = 0

        self.cursor.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?)",
            (game_id, winner_id, loser_id, winner_points, loser_points))
        self.dbCon.commit()

        self.updateUserGameStats(winner_id)
        self.updateUserGameStats(loser_id)

        return {'game_id':game_id}, 200

        
    def api_coffee(self, params: dict):
        return "Why...? We don't serve coffee here, just... idk, go find a cafe or something, maybe there's a pickleball court nearby.", 418
        

    def updateUserGameStats(self, user_id):

        if not self.is_user_valid(user_id):
            return False

        self.cursor.execute('SELECT COUNT(*) FROM games WHERE winner_id=? OR loser_id=?', (user_id, user_id))
        gamesPlayed = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM games WHERE winner_id=?', (user_id,))
        gamesWon = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT AVG(CASE WHEN winner_id=? THEN winner_points ELSE loser_points END) FROM games WHERE winner_id=? OR loser_id=?', (user_id, user_id, user_id))
        averageScore = self.cursor.fetchone()[0]

        self.cursor.execute('UPDATE users SET gamesPlayed=?, gamesWon=?, averageScore=? WHERE user_id=?', (gamesPlayed, gamesWon, averageScore, user_id))
        self.dbCon.commit()
        return True


    def close(self):
        self.cursor.close()
        self.dbCon.close()