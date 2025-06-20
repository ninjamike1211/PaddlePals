# PickleConnect Rest API

The PickleConnect database system is based on a RESTful API, which allows the android app to query the database over a network connection using standard HTTP requests. Below is a list of endpoints.

# Endpoints:
    

## pickle/user
- `GET pickle/user`
    ---
    Retrieves data about a specific user, specifically notated by user_id. By default, all accessible user data will be returned, but the `objects` parameter can be used to query for specific values.

    **params**:
    - `user_id`: The user_id of the account to query data from
    - `objects` *(optinoal)*: A comma separated, spaceless list of values to query from the database. The following are recognized parameters: `username`, `gamesPlayed`, `gamesWon`, `averageScore`

- `PUT pickle/user`
    ---
    Used to modify user data, such as username. For each value to modify, include a parameter of that value's name and its new value.

    **params**:
    - `user_id`: The user_id of the account to modify data
    - `username` *(optional*):

- `POST pickle/user`
    ---
    Creates a user account in the database with a given username and password.

    **params**:
    - `username`:
    - `password`:

- `DELETE pickle/user`
    ---
    Deletes a user account from the database. This does not remove the user ID, but instead removes the user data (games played/won, average score, etc), removes their password hash, and replaces their username with "deleted_user". All game records which this user participated in will remain in the database, with their user_id returning the "deleted_user" username, and with no other data accessible.

    **params**:
    - `user_id`: the user ID of the account to delete.
    - `password`: requires password in addition to apiKey for additional authentication

- `GET pickle/user/id`
    ---
    Returns a user ID used by the database for a given username, if the request sender has permission to view the requested user.

    **params**:
    - `username`: the username of the user to request ID for

- `GET pickle/user/friends`
    ---
    Returns a list of users who the current user is friends with.

    **params**:
    - `user_id`: the user ID to query list of friends from
    - `include_username` *(optional)*: if this is set to `true`, the returned value will include a list of usernames as well

- `POST pickle/user/friends`
    ---
    Adds a friend to the user's friend list. The friend to add is specified with either their user ID (`friend_id`), or their username (`friend_username`). Only one of these may be included in the request.

    **params**:
    - `user_id`: user ID of the current user
    - `friend_id` *(optional)*: user ID of the friend to add to friends list
    - `friend_username` *(optional)*: username of the friend to add to friends list

- `DELETE pickle/user/friends`
    ---
    Removes a friend from the user's friend list, specified using the friends user ID (`friend_id`).

    **params**:
    - `user_id`: user ID of the current user
    - `friend_id`: user ID of the friend to remove from friends list

- `GET pickle/user/games`
    ---
    Returns a list of game IDs for which the given user (by user ID) has participated in. Optionally, the `won` parameter can be used to filter for games that the user either won or lost.

    **params**:
    - `user_id`: the user ID to request the games list from
    - `won` *(optional)*: either "true" or "false", filters for games that the user either won or lost.

- `GET pickle/user/auth`
    ---
    Authenticates using a username and password, returns an API token for accessing user account data.

    **params**:
    - `username`: account username
    - `password`: account password

## pickle/game
- `GET pickle/game`
    ---
    Returns the data for a given game, specified by `game_id`. This data includes (in this order): game ID, winner user ID, loser user ID, winner points, loser points

    **params**:
    - `game_id`: the game ID of the game to request

- `POST pickle/game`
    ---
    Used to register a game in the database. All information about the game must be provided. Returns the game ID of the newly registered game.

    **params**:
    - `winner_id`: user ID of the winning player
    - `loser_id`: user ID of the losing played
    - `winner_points`: the number of points scored by the winning player
    - `loser_points`: the number of points scored by the losing player
