import sqlite3
from dataclasses import dataclass

class WebServer:

    @dataclass
    class APIRequest:
        type: str
        endpoint: str
        params: dict[str, str] = None


    def __init__(self, dbFile = 'pickle.db'):
        self.dbFile = dbFile
        self.dbCon = sqlite3.connect(self.dbFile)
        self.cursor = self.dbCon.cursor()


    def decode_request(self, request:str):
        request_parts = request.split(' ')

        if len(request_parts) < 2:
            print(f'Invalid request, insufficient data provided: {request}')
            return False

        request_type = request_parts[0]

        if request_type not in ('GET', 'PUT', 'POST', 'DELETE'):
            print(f'Invalid request type: {request_type}')
            return False
        
        uri_parts = request_parts[1].split('/', 1)
        if len(uri_parts) != 2 or uri_parts[0] != 'pickle':
            print(f'Invalid URI: {request_parts[1]}')
            return False
        endpoint = uri_parts[1].replace('/', '_')
        
        params = {}
        for part in request_parts[2:]:
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
        
            
    def handle_request(self, requestStr:str):
        request = self.decode_request(requestStr)
        if not(request):
            return False
        
        return self.execute_request(request)
            

    def api_user(self, request: APIRequest):

        if request.type == 'GET':
            if 'user_id' not in request.params:
                print(f'Invalid parameters for GET pickle/user, must include user ID: {request.params}')
                return False
            
            if 'objects' in request.params:
                # TODO: implement parameter validation
                get_objects = request.params['objects']
        
            else:
                get_objects = 'username, gamesPlayed, gamesWon, averageScore'

            self.cursor.execute(f"SELECT {get_objects} FROM users WHERE user_id={request.params['user_id']}")
            result = self.cursor.fetchone()
            return result
        
        elif request.type == 'PUT':
            if 'user_id' not in request.params or 'password' not in request.params:
                print(f'Invalid parameters for PUT pickle/user, must include user ID and password: {request.params}')
                return False
            
            # TODO: password authentication

            for param, val in request.params.items():
                if param == 'username':
                    self.cursor.execute(f"UPDATE users SET username='{val}' WHERE user_id={request.params['user_id']}")

                elif param == 'gamesPlayed':
                    self.cursor.execute(f"UPDATE users SET gamesPlayed={val} WHERE user_id={request.params['user_id']}")

                elif param == 'gamesWon':
                    self.cursor.execute(f"UPDATE users SET gamesWon={val} WHERE user_id={request.params['user_id']}")

                elif param == 'averageScore':
                    self.cursor.execute(f"UPDATE users SET averageScore={val} WHERE user_id={request.params['user_id']}")

                elif param != 'user_id':
                    print(f'Invalid object parameter: {param}={val}')

            self.dbCon.commit()
            return True
        
        elif request.type == 'POST':
            if 'username' not in request.params or 'password' not in request.params:
                print(f'Invalid parameters for POST pickle/user, must include username and password: {request.params}')
                return False
            
            # TODO: password authentication

            self.cursor.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
            userId = self.cursor.fetchone()[0] + 1

            self.cursor.execute(f"INSERT INTO users VALUES ({userId}, '{request.params['username']}', '{request.params['password']}', 0, 0, 0.0)")
            self.dbCon.commit()
            return userId
        
        elif request.type == 'DELETE':
            if 'user_id' not in request.params or 'password' not in request.params:
                print(f'Invalid parameters for DELETE pickle/user, must include user ID and password: {request.params}')
                return False
            
            # TODO: password authentication

            self.cursor.execute(f"UPDATE users SET username='deleted_user', passwordHash='', gamesPlayed=0, gamesWon=0, averageScore=0.0 WHERE user_id={request.params['user_id']}")
            self.dbCon.commit()
            return True

    
    def api_user_id(self, request: APIRequest):
        if request.type != 'GET' or len(request.params) != 1 or 'username' not in request.params or request.params['username'] == 'deleted_user':
            print(f'Invalid request for pickle/user/id: {request}')
            return False
        
        self.cursor.execute(f"SELECT user_id FROM users WHERE username='{request.params['username']}'")
        userId = self.cursor.fetchone()

        if userId:
            return userId[0]
        
        else:
            print(f'Username not found: {request.params['username']}')
            return False
        

    def api_user_games(self, request: APIRequest):
        if request.type != 'GET':
            print(f'Invalid request for pickle/user/games')
            return False
        
        if 'won' in request.params:
            if request.params['won'] == 'true':
                self.cursor.execute(f"SELECT game_id FROM games WHERE winner_id={request.params['user_id']}")

            elif request.params['won'] == 'false':
                self.cursor.execute(f"SELECT game_id FROM games WHERE loser_id={request.params['user_id']}")

            else:
                print(f'Invalid value for parameter "won" in GET pickle/user/games: {request.params['won']}')
                return False
            
        else:
            self.cursor.execute(f"SELECT game_id FROM games WHERE winner_id={request.params['user_id']} OR loser_id={request.params['user_id']}")

        games_list = self.cursor.fetchall()
        return games_list
    

    def api_game(self, request: APIRequest):
        if request.type == 'GET':
            if 'game_id' not in request.params:
                print(f'ERROR: GET pickle/game must specify game_id parameter!')
                return False
            
            self.cursor.execute(f"SELECT * FROM games WHERE game_id={request.params['game_id']}")
            game = self.cursor.fetchone()
            return game
            

        elif request.type == 'POST':
            if any(key not in request.params for key in ('winner_id', 'loser_id', 'winner_points', 'loser_points')):
                print(f'Invalid parameters for POST pickle/game: {request.params}')

            self.cursor.execute("SELECT game_id FROM games ORDER BY game_id DESC LIMIT 1")
            gameId = self.cursor.fetchone()[0] + 1

            self.cursor.execute(f"""INSERT INTO games VALUES (
                                {gameId},
                                {int(request.params['winner_id'])},
                                {int(request.params['loser_id'])},
                                {int(request.params['winner_points'])},
                                {int(request.params['loser_points'])}
                                )""")
            self.dbCon.commit()
            return True

        else:
            print(f'ERROR: Endpoint pickle/game does not support request type {request.type}')
            return False


    def close(self):
        self.cursor.close()
        self.dbCon.close()


try:

    server = WebServer()

    while True:

        query = input('Enter an API command: ')
        if query == 'exit':
            break

        result = server.handle_request(query)
        
        print(f'Result: {result}\n')



finally:
    server.close()