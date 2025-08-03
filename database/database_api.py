import os
import sqlite3
import hashlib
import base64
import string
import time

class restAPI:
    """A RESTful API for the database server of PicklePals. Also controls the SQLite database directly"""

    API_KEY_TIMEOUT = 30 * 60
    ADMIN_USER = 0
    UNKNOWN_USER = -1

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

        # If set by clearDB, erase the database
        if clearDB and os.path.isfile(dbFile):
            os.remove(dbFile)

        self._database = sqlite3.connect(dbFile)
        self._dbCursor = self._database.cursor()
        self._useAuth = useAuth
        self.__apiKeys = {}
        self.__renewalKeys = {}
        self.__user_cache = set()

        # If the database is uninitialized, initialize it
        self._dbCursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        if self._dbCursor.fetchone()[0] == 0:
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
            # Check that the base of the URI is pickle/
            uri_parts = uri[1:].split('/',1)
            if uri_parts[0] != 'pickle':
                raise self.APIError(f'Base endpoint must be "pickle/": {uri_parts[0]}', 404)
            
            # Replace '/' in URI with '_', as that's the convention used for naming api endpoint functions
            endpoint = uri_parts[1].replace('/', '_')

            # Check if authentication is required (if it's enabled and if the endpoint requires it)
            if self._useAuth and (endpoint not in ("user_create", "user_auth", "user_auth_renew", "coffee")):
                if not api_key:
                    raise self.APIError('Authentication required, please obtain an API key through pickle/user/auth', 401)

                # Check API key, if valid append 'sender_id' to input dictionary for the endpoint to know the sender's user ID
                sender_id = self._checkApiKey(api_key)
                params['sender_id'] = sender_id

                if sender_id == None:
                    raise self.APIError('API key not recognized, could be out of date or server has restarted. Try requesting another one with pickle/user/auth', 401)
            
            # Get the endpoint function, which will be named "self._api_" plus the endpoint URI without pickle and with '/' replaced by '_'
            func = getattr(self, "_api_" + endpoint, None)
            if func:
                return func(params)
            
            else:
                raise self.APIError(f'Endpoint not found: {uri}', 404)
        
        except Exception as error:
            # If any exception happens, we want to delete the input parameters and API key for security
            del params
            del api_key
            raise error


    def _init_db(self):
        # Initializes the SQLite database from scratch (create all tables)
        self._dbCursor.execute('CREATE TABLE users(user_id INT, username TEXT, passwordHash BLOB, salt BLOB, valid INT, gamesPlayed INT, gamesWon INT, averageScore REAL)')
        self._dbCursor.execute('CREATE TABLE games(game_id INT, timestamp INT, game_type INT, winner_id INT, loser_id INT, winner_points INT, loser_points INT)')
        self._dbCursor.execute('CREATE TABLE user_game_stats(user_id INT, game_id INT, swing_count INT, swing_hits INT, swing_max REAL, Q1_hits INT, Q2_hits INT, Q3_hits INT, Q4_hits INT)')
        self._dbCursor.execute('CREATE TABLE friends(userA INT, userB INT)')

        # Generate the admin user and commit to database
        pass_hash, salt = self._gen_password_hash('root')
        self._dbCursor.execute("INSERT INTO users VALUES (0, 'admin', ?, ?, 0, NULL, NULL, NULL)", (pass_hash, salt))
        self._database.commit()
        
        
    def _check_username(self, username: str):
        # Must be between 5 and 25 characters long
        if not 5 <= len(username) <=25:
            return False
        
        # Cannot certain reserved names
        if username in ('admin', 'deleted_user', 'unknown_user'):
            return False
        
        # Must be ascii and only printable characters (no spaces, newlines, etc)
        if not username.isascii() or not username.isprintable() or ' ' in username:
            return False

        return True
    

    def _check_password(self, password: str):
        # Cannot be in a list of common passwords
        if password in ('password', 'querty', '123456789', '123456', 'secret'):
            return False
        
        # Must be between 10 and 50 characters long
        if not 10 <= len(password) <= 50:
            return False
        
        # Must be ascii and cannot contain whitespace (except for spaces)
        if not password.isprintable() or not password.isascii():
            return False
        
        # Must include at least 1 digit
        if not any(char.isdigit() for char in password):
            return False
        
        # Must include at least one uppercase letter
        if not any(char.isupper() for char in password):
            return False
        
        # Must include at least one lower case letter
        if not any(char.islower() for char in password):
            return False
        
        # Must include at least one punctuation mark (any ascii characters that aren't alphanumeric or whitespace)
        if not any(char in password for char in string.punctuation):
            return False
        
        return True
    

    def _is_username_existing(self, username: str):
        # Checks if there is a user with a specific username in the database
        self._dbCursor.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
        return self._dbCursor.fetchone()[0] > 0
        

    def _is_user_account_valid(self, user_id: int):
        # Checks if a user ID is associated with a valid user account (excludes deleted users, admin, unknown users)
        # First check the user cache (if found, it's a recognized account)
        if user_id in self.__user_cache:
            return True
        
        # If not in the cache, check the database manually
        self._dbCursor.execute("SELECT valid FROM users WHERE user_id=?", (user_id,))
        valid = self._dbCursor.fetchone()

        # If user found and valid, add it to the user cache and return status
        if valid and valid[0]:
            self.__user_cache.add(user_id)
            return True
        else:
            return False
    

    def _is_user_id_valid(self, user_id: int):
        # Checks if a user ID is a valid ID (includes unknown users, but not deleted users or admin)
        return user_id == self.UNKNOWN_USER or self._is_user_account_valid(user_id)
    

    def _is_user_deleted(self, user_id: int):
        # Checks if a user ID is associated with a deleted user account
        self._dbCursor.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
        deleted = self._dbCursor.fetchone()
        return deleted and deleted[0] == 'deleted_user'
    

    def _are_users_friends(self, userA: int, userB: int):
        # Checks if two users are friends
        self._dbCursor.execute("SELECT * FROM friends WHERE (userA=? AND userB=?) OR (userA=? AND userB=?)", (userA, userB, userB, userA))
        return True if self._dbCursor.fetchone() else False
    

    def _user_canView(self, sender_id: int, user_id: int):
        # Checks if a sender has permissions to view a user's private data (e.g. stats)
        # If authentication is disabled, anything is allowed
        if not self._useAuth:
            return True

        # If no sender ID was specified, assume access is denied
        if sender_id is None:
            return False
        
        # Admin is allowed to access anything, a user is allowed to access their own data
        if sender_id == self.ADMIN_USER or sender_id == user_id:
            return True
        
        # Friends are allowed to view each other's data
        return self._are_users_friends(sender_id, user_id)
    

    def _user_canEdit(self, sender_id: int, user_id: int):
        # Checks whether a sender has permissions to edit a user's data
        # If auth is disabled anything is allowed. Admin is allowed to do anything
        if not self._useAuth or sender_id == self.ADMIN_USER:
            return True

        # If no sender ID was specified, assume access is denied
        if sender_id is None:
            return False
        
        # Otherwise, only the user is allowed to edit their own data
        return sender_id == user_id

    def _gen_password_hash(self, password:str):
        # Generates a password hash and random salt given a plain text password
        salt = bytearray(os.urandom(16))
        hash = bytearray(hashlib.sha256(salt + password.encode()).digest())
        return hash, salt
    
    def _check_userAuth(self, username:str, password:str):
        # Attempts to authenticate a user from username/password, returns user ID if successful, None if not
        # Pull user auth data based on username
        self._dbCursor.execute("SELECT user_id, passwordHash, salt FROM users WHERE username=?", (username,))
        data = self._dbCursor.fetchone()
        if not data: # If username not found, impossible to authenticate
            return None

        # Verify password using password hash and salt form database
        dbHash = data[1]
        salt = data[2]
        userHash = bytearray(hashlib.sha256(salt + password.encode()).digest())
        if userHash == dbHash:
            return int(data[0])
        else:
            return None
    

    def _gen_ApiKey(self, user_id:int):
        # Generates API and renewal keys for a given user. Automatically registers them in the server
        # Generate random API key
        rand_val = os.urandom(12)
        api_key = base64.b64encode(rand_val).decode('utf-8')

        # Prevent duplicates by continuously generating new keys until a non-duplicate is found
        while api_key in self.__apiKeys:
            rand_val = os.urandom(12)
            api_key = base64.b64encode(rand_val).decode('utf-8')

        # Store API key within local private dictionary
        self.__apiKeys[api_key] = {'user_id':user_id, 'expiration':time.time() + self.API_KEY_TIMEOUT}

        # Generate random renewal key
        rand_val = os.urandom(12)
        renew_key = base64.b64encode(rand_val).decode('utf-8')

        # Prevent duplicates by continuously generating new keys until a non-duplicate is found
        while api_key in self.__renewalKeys:
            rand_val = os.urandom(12)
            renew_key = base64.b64encode(rand_val).decode('utf-8')

        # Store renewal key within local private dictionary
        self.__renewalKeys[renew_key] = user_id
        return api_key, renew_key
    

    def _checkApiKey(self, apiKey:str):
        # Checks if an API is registered, and if so returns the associated user ID
        # Also checks if the API key has expired, and raises an exception if so
        key_info = self.__apiKeys.get(apiKey)

        if not key_info:
            return None
        elif time.time() <  key_info['expiration']:
            return key_info['user_id']
        else:
            raise self.APIError('API key has expired, please renew with the renewal key.', 498)
    

    def _api_user_getUsername(self, params: dict):
        """Retrieves username(s) of user(s) with a given user ID(s).

        Args:
            'user_id' (int | list(int)): user ID(s) of account(s) to retrieve usernames from

        Returns:
            dict: usernames keyed by user ID
        """
        # Must include user_id to get any usernames
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters for pickle/user/getUsername: {params}. Must include user_id as an int or list of ints.', 400)

        # If single user ID passed, wrap it in a list for easier processing
        user_ids = params['user_id']
        if type(user_ids) is int:
            user_ids = [user_ids]

        # Check user ID was either an int (now a list) or was already a list
        if type(user_ids) != list:
            raise self.APIError(f'Invalid user id(s) type: {user_ids}', 400)

        # Loop through each user ID, adding their usernames to a dictionary for output
        result_dict = {}
        for user_id in user_ids:
            # override for unknown users (user ID -1), so the UI correctly displays their status
            if user_id == self.UNKNOWN_USER:
                result_dict[user_id] = 'unknown_user'
                continue

            # We want to be able to retrieve deleted usernames (returns deleted_user, useful for UI)
            # However, any other invalid user type should return an error (as they don't have a username)
            if not self._is_user_deleted(user_id) and not self._is_user_account_valid(user_id):
                raise self.APIError(f'User ID {user_id} is not a valid user', 404)

            # Retrieve username and add to dictionary for output
            self._dbCursor.execute(f"SELECT username FROM users WHERE user_id=?", (user_id,))
            result_dict[user_id] = self._dbCursor.fetchone()[0]

        return result_dict


    def _api_user_getStats(self, params: dict):
        """Retrieves user statistics of specific user(s).
        By default, all accessible user stats be returned, but the `stats` parameter can be used to query for specific values.
        The sender must have appropriate permissions to view these statistics (must be admin or have be friends).

        Args:
            'user_id' (int | list(int)): user ID(s) of account(s) to retrieve stats from

        Returns:
            dict: requested stats keyed by user ID
        """
        # Must include user_id to get any stats
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters for pickle/user/getStats, must include user ID(s): {params}', 400)
        
        # If single user ID passed, wrap it in a list for easier processing
        user_ids = params['user_id']
        if type(user_ids) == int:
            user_ids = [user_ids]

        # Check user ID was either an int (now a list) or was already a list
        if type(user_ids) != list:
            raise self.APIError(f'Invalid user id(s) type: {user_ids}', 400)

        # Loop through each user ID, adding their stats to a dictionary for output
        result_dict = {}
        for user_id in user_ids:
            # Check the user is valid first
            if not self._is_user_account_valid(user_id):
                raise self.APIError(f'User ID {user_id} is not a valid user', 404)

            # Check that we have permissions to view this user's stats
            if not self._user_canView(params.get('sender_id'), user_id):
                raise self.APIError(f'Access forbidden to user ID {user_id}', 403)
            
            # If specific stats requested, use those, otherwise pull all available stats
            if 'stats' in params:
                stats = params['stats']
            else:
                stats = ['gamesPlayed', 'gamesWon', 'averageScore']

            # Retrieve each stat from the database, adding to dictionary
            results = {}
            for stat in stats:
                if stat in ('gamesPlayed', 'gamesWon', 'averageScore'):
                    self._dbCursor.execute(f"SELECT {stat} FROM users WHERE user_id=?", (user_id,))
                    results[stat] = self._dbCursor.fetchone()[0]
                else:
                    raise self.APIError(f'ERROR: unknown stat requested: {stat}', 404)
            
            result_dict[user_id] = results

        return result_dict
    
    
    def _api_user_setUsername(self, params: dict):
        """Changes a user's username to a new one. Raises an APIError if the new username is already taken or invalid.

        Args:
            'user_id' (int): user ID of account to change username
            'username' (str): the new username

        Returns:
            dict: 'success': (bool) True if the username change was successful
        """
        # We need a user ID to know what account to change the username of
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters: {params.keys}. Must include user_id', 400)
        
        # We need a new username for this endpoint
        if 'username' not in params:
            raise self.APIError(f'Invalid parameters: {params.keys}. Must include username', 400)
        username = params['username']
        
        # Check user ID is of a valid account
        user_id = int(params['user_id'])
        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        # Check we have the perms to edit username
        if not self._user_canEdit(params.get('sender_id'), user_id):
            raise self.APIError(f'Access forbidden to user ID {user_id}', 403)

        # Check username is valid
        if not self._check_username(username):
            raise self.APIError(f'Invalid username {username}', 400)
        
        # Check username isn't a duplicate
        if self._is_username_existing(username):
            raise self.APIError(f'Username {username} already exists', 400)

        # Change username in DB
        self._dbCursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        self._database.commit()
        return {'success':True}
    

    def _api_user_create(self, params: dict):
        """Creates a user account in the database with a given username and password.

        Args:
            'username' (str): username for new user
            'password' (str): password for new user

        Returns:
            dict: 'user_id': (int) the user ID of the newly created account.
        """
        # We need a username and password to create an account
        if 'username' not in params or 'password' not in params:
            raise self.APIError(f'Invalid parameters for POST pickle/user: {params}. Must include username and password', 400)
        username = params['username']
        password = params['password']

        # Check username is valid and not duplicate, and password is valid
        if not self._check_username(username):
            raise self.APIError(f'Invalid username {username}', 400)
        
        if self._is_username_existing(username):
            raise self.APIError(f'Username {username} already exists', 403)
        
        if not self._check_password(password):
            raise self.APIError(f'Invalid password "{password}"', 400)

        # Generate a password hash and salt
        pass_hash, salt = self._gen_password_hash(password)

        # Fetch the latest user ID, this user will have the next ID
        self._dbCursor.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
        user_id = self._dbCursor.fetchone()[0] + 1

        # Add user to the database
        self._dbCursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, 1, 0, 0, 0.0)", (user_id, username, pass_hash, salt))
        self._database.commit()

        # Add user to user cache (for faster response time)
        self.__user_cache.add(user_id)
        return {'user_id':user_id}
    

    def _api_user_delete(self, params: dict):
        """Deletes a user account from the database. This does not only remove the user ID, but instead removes the user data
        (games played/won, average score, etc), removes their password hash, and replaces their username with "deleted_user".
        All game records which this user participated in will remain in the database, with their user_id returning the
        "deleted_user" username, and with no other data accessible.

        Args:
            user_id (int): user ID of the account to delete

        Returns:
            dict: 'success': (bool) True if the username change was successful
        """
        # We need to know the user ID to delete a user
        if 'user_id' not in params:
            raise self.APIError(f'Invalid parameters for DELETE pickle/user, must include user ID: {params}', 400)
        user_id = int(params['user_id'])

        # Check that the user account exists and is valid
        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        # Check that we have perms to delete the user
        if not self._user_canEdit(params.get('sender_id'), user_id):
            raise self.APIError(f'Access forbidden to user ID {user_id}', 403)

        # Remove user data, all friend associations, and user game stats
        self._dbCursor.execute("UPDATE users SET username='deleted_user', passwordHash=NULL, salt=NULL, valid=0, gamesPlayed=NULL, gamesWon=NULL, averageScore=NULL WHERE user_id=?", (user_id,))
        self._dbCursor.execute("DELETE FROM friends WHERE userA=? OR userB=?", (user_id, user_id))
        self._dbCursor.execute("DELETE FROM user_game_stats WHERE user_id=?", (user_id,))
        self._database.commit()

        # Remove user from user cache
        if user_id in self.__user_cache:
            self.__user_cache.remove(user_id)
        return {'success':True}
            
    
    def _api_user_id(self, params: dict):
        """Returns a user ID used by the database for a given username, if the request sender has permission to view the requested user.

        Args:
            'username' (str): the username(s) of the user(s) to request ID for. May be a string or a list of strings

        Returns:
            dict: dictionary of user IDs keyed by username
        """
        
        # We need a username to grab a user ID
        if 'username' not in params:
            raise self.APIError('GET pickle/user/id requires the parameter "username"', 400)
        
        # If only a single username provided, wrap it in a list for easier processing
        usernames = params['username']
        if type(usernames) is not list:
            usernames = [usernames]

        # Loop through each username, adding their ID to a dictionary for output
        result_dict = {}
        for username in usernames:
            # Check username is valid before we subject it to a database search
            if not self._check_username(username):
                raise self.APIError(f'Invalid username {username}', 400)
            
            # Fetch the user ID
            self._dbCursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
            user_id = self._dbCursor.fetchone()

            # Add user ID to list, or raise error if it wasn't found
            if user_id:
                result_dict[username] = user_id[0]
            else:
                raise self.APIError(f'Username not found: {username}', 404)
            
        return result_dict
        
        
    def _api_user_friends(self, params: dict):
        """Returns a dictionary of users who the current user is friends with.
        The dict is keyed by user ID and contains username, games played against that user, and win rate against that user.

        Args:
            'user_id' (int): the user ID to query list of friends from

        Returns:
            dict: keyed by user ID and contains username, games played against that user, and win rate against that user
        """
        # We need a user ID to pull from
        if 'user_id' not in params:
            raise self.APIError('ERROR: pickle/user/friends must include "user_id" parameter', 400)
        user_id = int(params['user_id'])

        # Check that the user exists and is valid
        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)

        # Pull list of user IDs of all friends
        self._dbCursor.execute("SELECT (CASE WHEN userA=? THEN userB ELSE userA END) FROM friends WHERE (userA=? OR userB=?)", (user_id, user_id, user_id,))
        friend_list = self._dbCursor.fetchall()

        # Loop through friends, adding their username/stats to a dictionary for output
        result = {}
        for id in friend_list:
            # Grab username from database
            self._dbCursor.execute("SELECT username FROM users WHERE user_id=?", (id[0],))
            username = self._dbCursor.fetchone()[0]

            # Grab the winner of every game the two players have played
            self._dbCursor.execute("SELECT winner_id FROM games WHERE (winner_id=? AND loser_id=?) OR (winner_id=? AND loser_id=?)", (user_id, id[0], id[0], user_id))
            games = self._dbCursor.fetchall()
            gameCount = len(games) # Total number of games is just the length of the list of winners

            # Calculate win rate based on how many times the winner ID was user_id
            if gameCount > 0:
                winCount = games.count((user_id,))
                winRate = winCount / gameCount
            else:
                winRate = None # Exception for if you haven't played any games
                
            # Add'em to the dictionary for output
            result[id[0]] = {'username':username, 'gamesPlayed':gameCount, 'winRate':winRate}
        
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

        user_id = self._check_userAuth(username, password)
        if user_id != None:
            api_key, renew_key = self._gen_ApiKey(user_id)

            print(f'Authentication successful for user {username}')
            return {'apiKey':api_key, 'renewalKey':renew_key}
        
        else:
            raise self.APIError(f'Authentication failed for user {username}', 401)
        

    def _api_user_auth_renew(self, params: dict):
        if 'apiKey' not in params or 'renewalKey' not in params:
            raise self.APIError(f'Invalid parameters for POST pickle/auth/renew, must include apiKey and renewalKey: {params}', 400)
        
        old_key = str(params['apiKey'])
        old_renew_key = str(params['renewalKey'])
        
        renew_key_user = self.__renewalKeys.get(old_renew_key)
        if renew_key_user == None:
            raise self.APIError(f'Key renewal failed, renewal key not recognized', 401)

        old_key_user = self.__apiKeys.get(old_key)
        if old_key_user == None:
            raise self.APIError(f'Key renewal failed, old api key not recognized', 401)

        if old_key_user and old_key_user['user_id'] == renew_key_user:
            self.__apiKeys.pop(old_key)
            api_key, renew_key = self._gen_ApiKey(renew_key_user)
            return {'apiKey':api_key, 'renewalKey':renew_key}
        
        else:
            raise self.APIError(f'Key renewal failed, old api key and renewal key do not match', 401)
    

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
                        "swing_max": game_stats[4],
                        "Q1_hits": game_stats[5],
                        "Q2_hits": game_stats[6],
                        "Q3_hits": game_stats[7],
                        "Q4_hits": game_stats[8]
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

        if game_type not in (0,):
            raise self.APIError(f'Invalid game type {game_type}', 400)
        
        if winner_points > 11:
            if winner_points - loser_points != 2 and winner_points < 15:
                raise self.APIError(f'Invalid game score, {winner_points} to {loser_points}', 400)
        elif winner_points < 11:
            raise self.APIError(f'Invalid game score, {winner_points} to {loser_points}', 400)
        elif loser_points >= 11:
            raise self.APIError(f'Invalid game score, {winner_points} to {loser_points}', 400)

        # Search for duplicate game in database
        game_id = int(f'{winner_id}{loser_id}{timestamp}')
        self._dbCursor.execute("SElECT COUNT(*) FROM games WHERE game_id=?", (game_id,))
        if self._dbCursor.fetchone()[0]:
            raise self.APIError(f'Duplicate game registered!', 403)

        self._dbCursor.execute(
            "INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?)",
            (game_id, timestamp, game_type, winner_id, loser_id, winner_points, loser_points))
        self._database.commit()

        self.updateUserGameStats(winner_id)
        self.updateUserGameStats(loser_id)

        return {'game_id':game_id}


    def _api_game_registerStats(self, params: dict):
        if any(key not in params for key in ('user_id', 'game_id', 'swing_count', 'swing_hits', 'swing_max', 'Q1_hits', 'Q2_hits', 'Q3_hits', 'Q4_hits')):
            print(f'Invalid parameters for pickle/game/registerStats: {params}')

        user_id = int(params['user_id'])
        game_id = int(params['game_id'])
        swing_count = int(params['swing_count'])
        swing_hits = int(params['swing_hits'])
        swing_max = float(params['swing_max'])
        Q1_hits = float(params['Q1_hits'])
        Q2_hits = float(params['Q2_hits'])
        Q3_hits = float(params['Q3_hits'])
        Q4_hits = float(params['Q4_hits'])

        if not self._is_user_account_valid(user_id):
            raise self.APIError(f'User ID {user_id} is not a valid user', 404)
        
        self._dbCursor.execute("SELECT COUNT(*) FROM games WHERE game_id=?", (game_id,))
        if not self._dbCursor.fetchone()[0]:
            raise self.APIError(f'Game ID {game_id} not found in database', 404)
        
        self._dbCursor.execute("SELECT COUNT(*) FROM user_game_stats WHERE game_id=? AND user_id=?", (game_id, user_id))
        if self._dbCursor.fetchone()[0]:
            raise self.APIError(f'Not allowed to register multiple game stats with the same game ID ({game_id}) and user ID ({user_id})', 403)

        if Q1_hits + Q2_hits + Q3_hits + Q4_hits != swing_hits:
            raise self.APIError(f'Individual quadrent hits ({Q1_hits},{Q2_hits},{Q3_hits},{Q4_hits}) don\'t add to the total hits ({swing_hits})', 400)

        self._dbCursor.execute(
            "INSERT INTO user_game_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, game_id, swing_count, swing_hits, swing_max, Q1_hits, Q2_hits, Q3_hits, Q4_hits))
        self._database.commit()

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
        self.__renewalKeys.clear()
