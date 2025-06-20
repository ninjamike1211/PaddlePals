import sqlite3
import hashlib
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

    def gen_password_hash(self, password:str):
        return bytearray(hashlib.sha256(password.encode()).digest())
        
    def is_user_valid(self, user_id):
        self.cursor.execute("SELECT valid FROM users WHERE user_id=?", (user_id,))
        valid = self.cursor.fetchone()
        return valid and valid[0]


    def decode_request(self, request_type, request:str):
        request_parts = request.split('?')

        if request_type not in ('GET', 'PUT', 'POST', 'DELETE'):
            print(f'Invalid request type: {request_type}')
            return False
        
        uri_parts = request_parts[0][1:].split('/', 1)
        if len(uri_parts) != 2 or uri_parts[0] != 'pickle':
            print(f'Invalid URI: {request_parts[0]}')
            return False
        endpoint = uri_parts[1].replace('/', '_')
        
        params = {}
        if len(request_parts) > 1:
            for part in request_parts[1:]:
                param = part.split('=')
                if len(param) != 2:
                    print(f'Invalid parameter: {part}')
                    return False

                params[param[0]] = param[1]

        return self.APIRequest(request_type, endpoint, params)
            
 
    def execute_request(self, request: APIRequest):

        func = getattr(self, "api_" + request.endpoint, None)
        if func:
            return func(request)
        
        else:
            print(f'Endpoint not found: {request.endpoint}')
            return False
        
            
    def handle_request(self, request_type:str, requestStr:str):
        request = self.decode_request(request_type, requestStr)
        if not(request):
            return False
        
        return self.execute_request(request)
            

    def api_user(self, request: APIRequest):

        if request.type == 'GET':
            if 'user_id' not in request.params:
                print(f'Invalid parameters for GET pickle/user, must include user ID: {request.params}')
                return False
            
            user_id = self.check_int(request.params['user_id'])
            
            if 'objects' in request.params:
                objects = request.params['objects'].split(',')
                get_objects = ''

                for i, object in enumerate(objects):
                    if object in ('username', 'gamesPlayed', 'gamesWon', 'averageScore'):
                        get_objects += object
                        if i < len(objects)-1:
                            get_objects += ','

                    else:
                        print(f'ERROR: invalid object requested: {object}')
                        return False
        
            else:
                get_objects = 'username,gamesPlayed,gamesWon,averageScore'

            self.cursor.execute(f"SELECT {get_objects} FROM users WHERE user_id=?", (user_id,))
            result = self.cursor.fetchone()
            return result
        
        elif request.type == 'PUT':
            if 'user_id' not in request.params:
                print(f'Invalid parameters for PUT pickle/user, must include user ID: {request.params}')
                return False
            
            user_id = self.check_int(request.params['user_id'])
            # TODO: password authentication

            if not self.is_user_valid(user_id):
                print(f'User ID {user_id} is not a valid user')
                return False

            for param, val in request.params.items():

                if param == 'username':
                    self.cursor.execute("UPDATE users SET username=? WHERE user_id=?", (self.check_str(val), user_id))

                elif param != 'user_id':
                    print(f'Invalid object parameter: {param}={val}')

            self.dbCon.commit()
            return True
        
        elif request.type == 'POST':
            if 'username' not in request.params or 'password' not in request.params:
                print(f'Invalid parameters for POST pickle/user, must include username and password: {request.params}')
                return False
            
            username = self.check_str(request.params['username'])
            password = self.check_str(request.params['password'])
            # TODO: password authentication
            # TODO: check that username doesn't already exist

            pass_hash = self.gen_password_hash(password)

            self.cursor.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
            user_id = self.cursor.fetchone()[0] + 1

            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, 1, 0, 0, 0.0)", (user_id, username, pass_hash))
            self.dbCon.commit()
            return user_id
        
        elif request.type == 'DELETE':
            if 'user_id' not in request.params:
                print(f'Invalid parameters for DELETE pickle/user, must include user ID: {request.params}')
                return False
            
            user_id = self.check_int(request.params['user_id'])
            # TODO: password authentication

            if not self.is_user_valid(user_id):
                print(f'User ID {user_id} is not a valid user')
                return False

            self.cursor.execute("UPDATE users SET username='deleted_user', passwordHash=NULL, valid=0, gamesPlayed=0, gamesWon=0, averageScore=0.0 WHERE user_id=?", (user_id,))
            self.dbCon.commit()
            return True

    
    def api_user_id(self, request: APIRequest):
        if request.type != 'GET' or len(request.params) != 1 or 'username' not in request.params or request.params['username'] == 'deleted_user':
            print(f'Invalid request for pickle/user/id: {request}')
            return False
        
        username = self.check_str(request.params['username'])
        # TODO: password authentication
        
        self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
        userId = self.cursor.fetchone()

        if userId:
            return userId[0]
        
        else:
            print(f'Username not found: {username}')
            return False
        
    def api_user_friends(self, request: APIRequest):
        if 'user_id' not in request.params:
            print('ERROR: pickle/user/friends must include "user_id" parameter')
            return False

        user_id = self.check_int(request.params['user_id'])

        if not self.is_user_valid(user_id):
            print(f'User ID {user_id} is not a valid user')
            return False

        if request.type == 'GET':
            self.cursor.execute("SELECT (CASE WHEN userA=? THEN userB ELSE userA END) FROM friends WHERE (userA=? OR userB=?)", (user_id, user_id, user_id,))
            friend_list = self.cursor.fetchall()

            if 'include_username' in request.params and request.params['include_username'] == 'true':
                username_list = []
                for id in friend_list:
                    self.cursor.execute("SELECT username FROM users WHERE user_id=?", (id[0],))
                    username_list.append(self.cursor.fetchone()[0])

                return [(friend_list[i][0], username_list[i]) for i in range(0, len(friend_list))]
            
            else:
                return [id[0] for id in friend_list]

        elif request.type == 'POST':
            if 'friend_id' in request.params:
                friend_id = self.check_int(request.params['friend_id'])
                if not self.is_user_valid(friend_id):
                    print(f'User ID {friend_id} is not a valid user')
                    return False

            elif 'friend_username' in request.params:
                username = self.check_str(request.params['friend_username'])

                self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
                raw_id = self.cursor.fetchone()
                if not raw_id:
                    print(f'ERROR: unable to find user with username "{username}"')
                    return False
                
                friend_id = raw_id[0]

            else:
                print('ERROR: POST pickle/user/friends requires either "friend_id" or "friend_username" parameter.')
                return False
            
            self.cursor.execute("INSERT INTO friends VALUES (?, ?)", (user_id, friend_id))
            self.dbCon.commit()
            return True

        elif request.type == 'DELETE':
            if 'friend_id' not in request.params:
                print('ERROR: DELETE pickle/user/friends must include "friend_id" parameter')
                return False

            friend_id = self.check_int(request.params['friend_id'])

            if not self.is_user_valid(friend_id):
                print(f'User ID {friend_id} is not a valid user')
                return False
            
            self.cursor.execute("DELETE FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (user_id, friend_id, friend_id, user_id))
            self.dbCon.commit()
            return True

        else:
            print(f'pickle/user/friends does not support command "{request.type}"')
        

    def api_user_games(self, request: APIRequest):
        if request.type != 'GET':
            print(f'Invalid request for pickle/user/games')
            return False
        
        user_id = self.check_int(request.params['user_id'])

        if not self.is_user_valid(user_id):
            print(f'User ID {user_id} is not a valid user')
            return False
        
        if 'won' in request.params:
            if request.params['won'] == 'true':
                self.cursor.execute("SELECT game_id FROM games WHERE winner_id=?", (user_id,))

            elif request.params['won'] == 'false':
                self.cursor.execute("SELECT game_id FROM games WHERE loser_id=?", (user_id,))

            else:
                print(f'Invalid value for parameter "won" in GET pickle/user/games: {user_id}')
                return False
            
        else:
            self.cursor.execute("SELECT game_id FROM games WHERE winner_id=? OR loser_id=?", (user_id, user_id))

        games_list = self.cursor.fetchall()
        return games_list
        
    
    def api_user_auth(self, request: APIRequest):
        if request.type != 'GET':
            print(f'Invalid command type {request.type} for pickle/auth, only GET supported')
            return False

        if 'username' not in request.params or 'password' not in request.params:
            print(f'Invalid parameters for POST pickle/user, must include username and password: {request.params}')
            return False
        
        username = self.check_str(request.params['username'])
        password = self.check_str(request.params['password'])

        pass_hash = self.gen_password_hash(password)

        self.cursor.execute("SELECT passwordHash FROM users WHERE username=?", (username,))
        real_hash = self.cursor.fetchone()

        if real_hash and pass_hash == real_hash[0]:
            print(f'Authentication successful for user {username}')
            return True
        
        else:
            print(f'Authentication failed for user {username}')
            return False
    

    def api_game(self, request: APIRequest):
        if request.type == 'GET':
            if 'game_id' not in request.params:
                print(f'ERROR: GET pickle/game must specify game_id parameter!')
                return False
            
            game_id = self.check_int(request.params['game_id'])
            
            self.cursor.execute("SELECT * FROM games WHERE game_id=?", (game_id,))
            game = self.cursor.fetchone()
            return game
            

        elif request.type == 'POST':
            if any(key not in request.params for key in ('winner_id', 'loser_id', 'winner_points', 'loser_points')):
                print(f'Invalid parameters for POST pickle/game: {request.params}')

            winner_id = self.check_int(request.params['winner_id'])
            loser_id = self.check_int(request.params['loser_id'])
            winner_points = self.check_int(request.params['winner_points'])
            loser_points = self.check_int(request.params['loser_points'])

            if not self.is_user_valid(winner_id):
                print(f'User ID {winner_id} is not a valid user')
                return False
            
            if not self.is_user_valid(loser_id):
                print(f'User ID {loser_id} is not a valid user')
                return False

            self.cursor.execute("SELECT game_id FROM games ORDER BY game_id DESC LIMIT 1")
            gameId = self.cursor.fetchone()[0] + 1

            self.cursor.execute(
                "INSERT INTO games VALUES (?, ?, ?, ?, ?)",
                (gameId, winner_id, loser_id, winner_points, loser_points))
            self.dbCon.commit()

            self.updateUserGameStats(winner_id)
            self.updateUserGameStats(loser_id)

            return gameId

        else:
            print(f'ERROR: Endpoint pickle/game does not support request type {request.type}')
            return False
        

    def updateUserGameStats(self, user_id):

        if not self.is_user_valid(user_id):
            return False

        self.cursor.execute('SELECT COUNT(*) FROM games WHERE winner_id=? OR loser_id=?', (user_id, user_id))
        gamesPlayed = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM games WHERE winner_id=', (user_id,))
        gamesWon = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT AVG(CASE WHEN winner_id=? THEN winner_points ELSE loser_points END) FROM games WHERE winner_id=? OR loser_id=?', (user_id, user_id, user_id))
        averageScore = self.cursor.fetchone()[0]

        self.cursor.execute('UPDATE users SET gamesPlayed=?, gamesWon=?, averageScore=? WHERE user_id=?', (gamesPlayed, gamesWon, averageScore, user_id))
        self.dbCon.commit()
        return True


    def close(self):
        self.cursor.close()
        self.dbCon.close()