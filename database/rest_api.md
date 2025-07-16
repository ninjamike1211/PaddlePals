# PickleConnect Rest API

The PickleConnect database system is based on a RESTful API, which allows the android app to query the database over a network connection using standard HTTP requests. Below is a list of endpoints.

# Endpoints:
    

## pickle/user
- `pickle/user/get`
    ---
    Retrieves data about a specific user, specifically notated by user_id. By default, all accessible user data will be returned, but the `objects` parameter can be used to query for specific values.

    **params**:
    - `user_id`: The user_id of the account(s) to query data from. May be passed as an int or a list of ints
    - `values` *(optinoal)*: A list of values to query for each user. The following are recognized values: `username`, `gamesPlayed`, `gamesWon`, `averageScore`. By default, all supported values will be queried

    **returns**: dictionary or list of dictionaries in the following format
    ```js
    {
        "(user_id)": {"username":(username), "gamesPlayed":(gamesPlayed), "gamesWon":(gamesWon), "averageScore":(averageScore)},
        // OR
        "(user_id)": {"(value1_name)":(value1_val), ...},
        ...
    }
    ```

- `pickle/user/set`
    ---
    Used to modify user data, such as username. For each value to modify, include a parameter of that value's name and its new value.

    **params**:
    - `user_id`: The user_id of the account to modify data
    - `username` *(optional*): value to set the username

    **returns**:
    ```js
    {"success":(true/false)}
    ```

- `pickle/user/create`
    ---
    Creates a user account in the database with a given username and password.

    **params**:
    - `username`: username for new user
    - `password`: password for new user

    **returns**:
    ```js
    {"user_id":(user_id)}
    ```

- `pickle/user/delete`
    ---
    Deletes a user account from the database. This does not remove the user ID, but instead removes the user data (games played/won, average score, etc), removes their password hash, and replaces their username with "deleted_user". All game records which this user participated in will remain in the database, with their user_id returning the "deleted_user" username, and with no other data accessible.

    **params**:
    - `user_id`: the user ID of the account to delete.

    **returns**:
    ```js
    {"success":(true/false)}
    ```

- `pickle/user/id`
    ---
    Returns a user ID used by the database for a given username, if the request sender has permission to view the requested user.

    **params**:
    - `username`: the username(s) of the user(s) to request ID for. May be a string or a list of strings

    **returns**:
    ```js
    {
        "(username)":(user_id),
        ...
    }
    ```

- `pickle/user/friends`
    ---
    Returns a list of user IDs/usernames who the current user is friends with.

    **params**:
    - `user_id`: the user ID to query list of friends from

    **returns**:
    ```js
    {
        "(friend_id)":{"username":(username), "gamesPlayed":(gamesPlayed), "winRate":(winPercentage)},
        ...
    }
    ```

- `pickle/user/addFriend`
    ---
    Adds a friend to the user's friend list. The friend to add is specified with either their user ID (`friend_id`), or their username (`friend_username`). Only one of these may be included in the request.

    **params**:
    - `user_id`: user ID of the current user
    - `friend_id` *(optional)*: user ID of the friend to add to friends list
    - `friend_username` *(optional)*: username of the friend to add to friends list

    **returns**:
    ```js
    {"success":(true/false)}
    ```

- `pickle/user/removeFriend`
    ---
    Removes a friend from the user's friend list, specified using the friends user ID (`friend_id`).

    **params**:
    - `user_id`: user ID of the current user
    - `friend_id`: user ID of the friend to remove from friends list

    **returns**:
    ```js
    {"success":(true/false)}
    ```

- `pickle/user/games`
    ---
    Returns a list of game IDs for which the given user (by user ID) has participated in. Optionally, the `won` parameter can be used to filter for games that the user either won or lost.

    **params**:
    - `user_id`: the user ID to request the games list from
    - `won` *(optional)*: either "true" or "false", filters for games that the user either won or lost.
    - `opponent_id`: *(optional)*: filter games by the user ID of a specific opponent
    - `min_time` *(optional)*: minimum timestamp to search through
    - `max_time` *(optional)*: maximum timestamp to search through

    **returns**:
    ```js
    {"game_ids":[game_id1, game_id2, ...]}
    ```

- `pickle/user/auth`
    ---
    Authenticates using a username and password, returns an API token for accessing user account data.

    **params**:
    - `username`: account username
    - `password`: account password

    **returns**:
    ```js
    {"success":(true/false), "apiKey":(api_key)}
    ```

## pickle/game
- `pickle/game/get`
    ---
    Returns the data for a given game, specified by `game_id`. This data includes (in this order): game ID, winner user ID, loser user ID, winner points, loser points

    **params**:
    - `game_id`: the game ID(s) of the game to request, as either an int or a list of ints

    **returns**:
    ```js
    {
        "(game_id)": {"timestamp":(timestamp), "game_type":(game_type), "winner_id":(winner_id), "loser_id":(loser_id), "winner_points":(winner_points), "loser_points":(loser_points)},
        ...
    }
    ```

- `pickle/game/stats`
    ---
    Returns the game statistics of a user associated with a specific game ID. Returns `None` for any games which don't have registered game stats

    **params**:
    - `user_id`: the user ID to request the stats of
    - `game_id` *(optional)*: the game ID(s) of the game(s) to request as an int or list of ints

    **returns**:
    ```js
    {
        "(game_id)": {
            "timestamp":(timestamp),
            "swing_count":(swing_count),
            "swing_hits":(swing_hit),
            "hit_percentage":(hit_percentage),
            "swing_min":(swing_min),
            "swing_max":(swing_max),
            "swing_avg":(swing_avg),
            "hit_modeX":(hit_modeX),
            "hit_modeY":(hit_modeY),
            "hit_avgX":(hit_avgX),
            "hit_avgY":(hit_avgY)
        },
        ...
        "(game_id)":null,
        ...
    }
    ```

- `pickle/game/register`
    ---
    Used to register a game in the database. All information about the game must be provided. Returns the game ID of the newly registered game.

    **params**:
    - `timestamp`: Unix timestamp (int) of when the game began
    - `game_type`: an int representing the game type
    - `winner_id`: user ID of the winning player
    - `loser_id`: user ID of the losing played
    - `winner_points`: the number of points scored by the winning player
    - `loser_points`: the number of points scored by the losing player

    **returns**:
    ```js
    {"game_id":(game_id)}
    ```

- `pickle/game/registerStats`
    ---
    Registers game stats for a specific user associated with a specific game

    **params**:
    - `user_id`: the user ID of the stats to record
    - `game_id`: the game ID of the game
    - `swing_count`: number of swings user performed in the game
    - `swing_hits`: number of swings which hit the ball by user in the game
    - `swing_min`: minimum swing speed
    - `swing_max`: maximum swing speed
    - `swing_avg`: average swing speed
    - `hit_modeX`: x coordinate of mode hit position
    - `hit_modeY`: y coordinate of mode hit position
    - `hit_avgX`: x coordinate of average hit position
    - `hit_avgY`: y coordinate of average hit position

    **returns**:
    ```js
    {"success":(true/false)}
    ```
