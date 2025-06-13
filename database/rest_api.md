# PickleConnect Rest API

The PickleConnect database system is based on a RESTful API, which allows the android app to query the database over a network connection using standard HTTP requests. Below is a list of endpoints.

## Endpoints:
- `GET pickle/apiToken`
    **params**: username, password
    Authenticates using a username and password, returns an API token for accessing user account data.

- `GET pickle/user`

- `PUT pickle/user`

- `POST pickle/user`

- `DELETE pickle/user`

- `GET pickle/user/id`

- `GET pickle/user/games`

- `GET pickle/game`

- `POST pickle/game`



- `POST pickle/registerUser`
    **params**: username, password
    Creates a user account in the database with a given username and password.

- `GET pickle/getUserID`
    **params**: username, apiToken
    Returns a user ID used by the database for a given username. This request will only be completed if the current user (authenticated by apiToken) is friends with the requested user.

- `GET pickle/getUsername`
    **params**: userId, apiToken
    Returns the username associated with a specific user ID. This request will only be completed if the current user (authenticated by apiToken) is friends with the requested user.

- `GET pickle/getUserStats`
    **params**: userId, apiToken
    Returns the statistics/data associated with a specific user ID. This request will only be completed if the current user (authenticated by apiToken) is friends with the requested user.

- `POST pickle/registerGame`
    **params**: winnerId, loserId, winnerPoints, loserPoints, apiToken,
    Registers a completed game in the database, including the winner and loser user IDs and points of each player. The current user (authenticated by apiToken) must be a participant in the game.

- `GET pickle/getGame`
    **params**: gameId, apiToken
    Returns information on a game of a specific game ID. Returns winner/loser user IDs, and winner/loser points

- `GET pickle/getAllGames`
    **params**: apiToken
    Returns a list of game IDs for all games which the user (authenticated by apiToken) has participated in.