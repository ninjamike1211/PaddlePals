import os
import sqlite3
import hashlib
import json
from dataclasses import dataclass

class restAPI:

    @dataclass
    class APIRequest:
        type: str
        endpoint: str
        params: dict[str, str] = None

    class ValidationError(Exception):
        def __init__(self, val, dataType):
            self.message = f'data validation error for value "{val}" to type "{dataType}"'
            super().__init__(self.message)


    def __init__(self, dbFile = 'pickle.db'):
        self.dbFile = dbFile
        self.dbCon = sqlite3.connect(self.dbFile)
        self.cursor = self.dbCon.cursor()


    def check_str(self, string: str):
        if string.find("'") == -1:
            return string
        
        else:
            raise self.ValidationError(string, 'str')

    def check_int(self, val: int):
        try:
            return int(val)
        
        except ValueError as error:
            raise self.ValidationError(val, 'int')

    def check_float(self, val: float):
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


    def decode_request(self, request_type, request:str):
        request_parts = request.split('?')

        if request_type not in ('GET', 'PUT', 'POST', 'DELETE'):
            return f'Unsupported request type: {request_type}', 501
        
        uri_parts = request_parts[0][1:].split('/', 1)
        if len(uri_parts) != 2 or uri_parts[0] != 'pickle':
            return f'Base endpoint must be "pickle/": {request_parts[0]}', 404
        endpoint = uri_parts[1].replace('/', '_')
        
        params = {}
        if len(request_parts) > 1:
            for part in request_parts[1:]:
                param = part.split('=')
                if len(param) != 2:
                    return f'Invalid parameter: {part}', 400

                params[param[0]] = param[1]

        return self.APIRequest(request_type, endpoint, params), 200
            
 
    def execute_request(self, request: APIRequest):

        func = getattr(self, "api_" + request.endpoint, None)
        if func:
            return func(request)
        
        else:
            return f'Endpoint not found: {request.endpoint}', 404
        
            
    def handle_request(self, request_type:str, requestStr:str):
        request, code = self.decode_request(request_type, requestStr)
        if code != 200:
            return request, code
        
        return self.execute_request(request)
            

    def api_user(self, request: APIRequest):

        if request.type == 'GET':
            if 'user_id' not in request.params:
                return f'Invalid parameters for GET pickle/user, must include user ID: {request.params}', 405
            
            user_id = self.check_int(request.params['user_id'])

            if not self.is_user_deleted(user_id) and not self.is_user_valid(user_id):
                return f'User ID {user_id} is not a valid user', 404
            
            if 'objects' in request.params:
                objects = request.params['objects'].split(',')
            else:
                objects = ['username', 'gamesPlayed', 'gamesWon', 'averageScore']

            results = {}
            for object in objects:
                if object in ('username', 'gamesPlayed', 'gamesWon', 'averageScore'):
                    self.cursor.execute(f"SELECT {object} FROM users WHERE user_id=?", (user_id,))
                    results[object] = self.cursor.fetchone()[0]

                else:
                    return f'ERROR: invalid object requested: {object}', 400

            return json.dumps(results), 200
        
        elif request.type == 'PUT':
            if 'user_id' not in request.params:
                return f'Invalid parameters for PUT pickle/user, must include user ID: {request.params}', 400
            
            user_id = self.check_int(request.params['user_id'])
            # TODO: password authentication

            if not self.is_user_valid(user_id):
                return f'User ID {user_id} is not a valid user', 404

            for param, val in request.params.items():

                if param == 'username':
                    if not self.check_username(val):
                        return f'Invalid username {val}', 400
                    
                    if self.is_username_existing(val):
                        return f'Username {val} already exists', 403

                    self.cursor.execute("UPDATE users SET username=? WHERE user_id=?", (val, user_id))

                elif param != 'user_id':
                    print(f'Invalid object parameter: {param}={val}')

            self.dbCon.commit()
            return True, 200
        
        elif request.type == 'POST':
            if 'username' not in request.params or 'password' not in request.params:
                return f'Invalid parameters for POST pickle/user, must include username and password: {request.params}', 400
            
            username = self.check_str(request.params['username'])
            password = self.check_str(request.params['password'])
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
            return user_id, 200
        
        elif request.type == 'DELETE':
            if 'user_id' not in request.params:
                return f'Invalid parameters for DELETE pickle/user, must include user ID: {request.params}', 400
            
            user_id = self.check_int(request.params['user_id'])
            # TODO: password authentication

            if not self.is_user_valid(user_id):
                return f'User ID {user_id} is not a valid user', 404

            self.cursor.execute("UPDATE users SET username='deleted_user', passwordHash=NULL, salt=NULL, valid=0, gamesPlayed=NULL, gamesWon=NULL, averageScore=NULL WHERE user_id=?", (user_id,))
            self.dbCon.commit()
            return True, 200

    
    def api_user_id(self, request: APIRequest):
        if request.type != 'GET':
            return f'Invalid request for pickle/user/id: {request}', 405
        
        if len(request.params) != 1 or 'username' not in request.params:
            return 'GET pickle/user/id requires the parameter "username"', 400
        
        username = request.params['username']
        if not self.check_username(username):
            return f'Invalid username {request.params['username']}', 400
        
        # TODO: password authentication
        
        self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
        userId = self.cursor.fetchone()

        if userId:
            return json.dumps({'user_id':userId[0]}), 200
        
        else:
            return f'Username not found: {username}', 404
        
    def api_user_friends(self, request: APIRequest):
        if 'user_id' not in request.params:
            return 'ERROR: pickle/user/friends must include "user_id" parameter', 400

        user_id = self.check_int(request.params['user_id'])

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404

        if request.type == 'GET':
            self.cursor.execute("SELECT (CASE WHEN userA=? THEN userB ELSE userA END) FROM friends WHERE (userA=? OR userB=?)", (user_id, user_id, user_id,))
            friend_list = self.cursor.fetchall()

            if 'include_username' in request.params and request.params['include_username'] == 'true':
                username_list = []
                for id in friend_list:
                    self.cursor.execute("SELECT username FROM users WHERE user_id=?", (id[0],))
                    username_list.append(self.cursor.fetchone()[0])

                result = []
                for i in range(0, len(friend_list)):
                    result.append({'user_id':friend_list[i][0], 'username':username_list[i]})
                # return [(friend_list[i][0], username_list[i]) for i in range(0, len(friend_list))], 200
            
            else:
                result = []
                for id in friend_list:
                    result.append({'user_id':id[0]})
            
            return json.dumps(result), 200

        elif request.type == 'POST':
            if 'friend_id' in request.params:
                friend_id = self.check_int(request.params['friend_id'])
                if not self.is_user_valid(friend_id):
                    return f'User ID {friend_id} is not a valid user', 404

            elif 'friend_username' in request.params:
                username = self.check_str(request.params['friend_username'])

                self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
                raw_id = self.cursor.fetchone()
                if not raw_id:
                    return f'ERROR: unable to find user with username "{username}"', 404
                
                friend_id = raw_id[0]

            else:
                return 'ERROR: POST pickle/user/friends requires either "friend_id" or "friend_username" parameter.', 400
            
            self.cursor.execute("INSERT INTO friends VALUES (?, ?)", (user_id, friend_id))
            self.dbCon.commit()
            return True, 200

        elif request.type == 'DELETE':
            if 'friend_id' not in request.params:
                return 'ERROR: DELETE pickle/user/friends must include "friend_id" parameter', 400

            friend_id = self.check_int(request.params['friend_id'])

            if not self.is_user_valid(friend_id):
                return f'User ID {friend_id} is not a valid user', 404
            
            self.cursor.execute("DELETE FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (user_id, friend_id, friend_id, user_id))
            self.dbCon.commit()
            return True, 200

        else:
            return f'pickle/user/friends does not support command "{request.type}"', 405
        

    def api_user_games(self, request: APIRequest):
        if request.type != 'GET':
            return f'Invalid request for pickle/user/games', 405
        
        user_id = self.check_int(request.params['user_id'])

        if not self.is_user_valid(user_id):
            return f'User ID {user_id} is not a valid user', 404
        
        if 'won' in request.params:
            if request.params['won'] == 'true':
                self.cursor.execute("SELECT game_id FROM games WHERE winner_id=?", (user_id,))

            elif request.params['won'] == 'false':
                self.cursor.execute("SELECT game_id FROM games WHERE loser_id=?", (user_id,))

            else:
                return f'Invalid value for parameter "won" in GET pickle/user/games: {user_id}', 400
            
        else:
            self.cursor.execute("SELECT game_id FROM games WHERE winner_id=? OR loser_id=?", (user_id, user_id))

        games_list = self.cursor.fetchall()
        result = {'game_ids': [game[0] for game in games_list]}
        return json.dumps(result), 200
        
    
    def api_user_auth(self, request: APIRequest):
        if request.type != 'GET':
            return f'Invalid command type {request.type} for pickle/auth, only GET supported', 405

        if 'username' not in request.params or 'password' not in request.params:
            return f'Invalid parameters for POST pickle/user, must include username and password: {request.params}', 400
        
        username = self.check_str(request.params['username'])
        password = self.check_str(request.params['password'])

        if self.check_password(username, password):
            print(f'Authentication successful for user {username}')
            return True, 200
        
        else:
            return f'Authentication failed for user {username}', 401
    

    def api_game(self, request: APIRequest):
        if request.type == 'GET':
            if 'game_id' not in request.params:
                return f'ERROR: GET pickle/game must specify game_id parameter!', 400
            
            game_id = self.check_int(request.params['game_id'])
            
            self.cursor.execute("SELECT * FROM games WHERE game_id=?", (game_id,))
            game = self.cursor.fetchone()

            if not game:
                return f'Game for game_id {game_id} not found', 404

            result = {'game_id':game[0], 'winner_id':game[1], 'loser_id':game[2], 'winner_points':game[3], 'loser_points':game[4]}
            return json.dumps(result), 200
            

        elif request.type == 'POST':
            if any(key not in request.params for key in ('winner_id', 'loser_id', 'winner_points', 'loser_points')):
                print(f'Invalid parameters for POST pickle/game: {request.params}')

            winner_id = self.check_int(request.params['winner_id'])
            loser_id = self.check_int(request.params['loser_id'])
            winner_points = self.check_int(request.params['winner_points'])
            loser_points = self.check_int(request.params['loser_points'])

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

            return game_id, 200

        else:
            return f'ERROR: Endpoint pickle/game does not support request type {request.type}', 405
        
    def api_coffee(self, request: APIRequest):
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