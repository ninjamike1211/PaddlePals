import os
import random
import sqlite3

try:
    if os.path.isfile('pickle.db'):
        os.remove('pickle.db')

    conn = sqlite3.connect('pickle.db')
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE users(user_id, username, passwordHash, valid, gamesPlayed, gamesWon, averageScore)')
    cursor.execute('CREATE TABLE games(game_id, winner_id, loser_id, winner_points, loser_points)')

    cursor.execute("""INSERT INTO users VALUES
                   (0, 'ninjamike1211', 'ah50jkg0q', 1, 0, 0, 0.0),
                   (1, 'aje0714', 'asdfi324hl', 1, 0, 0, 0.0),
                   (2, 'BOT-Lee', '092bhng082h', 1, 0, 0, 0.0),
                   (3, 'jpk102pitt', '3hladf09hy3n', 1, 0, 0, 0.0)
                   """)
    games = ''
    for i in range(0,100):
        user_win = random.randint(0,3)
        user_lose = random.randint(0,2)
        if user_lose >= user_win:
            user_lose += 1

        points_win = random.randint(0,15)
        if points_win < 11:
            points_win = 11

        if points_win <= 11:
            points_lose = random.randint(0,10)
        else:
            points_lose = points_win - 2

        games += f'({i}, {user_win}, {user_lose}, {points_win}, {points_lose}),'
    
    cursor.execute(f'INSERT INTO games VALUES {games[:-1]}')

    conn.commit()

    for user in range(0,4):
        cursor.execute(f'SELECT COUNT(*) FROM games WHERE winner_id={user} OR loser_id={user}')
        gamesPlayed = cursor.fetchone()[0]

        cursor.execute(f'SELECT COUNT(*) FROM games WHERE winner_id={user}')
        gamesWon = cursor.fetchone()[0]

        cursor.execute(f'SELECT AVG(CASE WHEN winner_id={user} THEN winner_points ELSE loser_points END) FROM games WHERE winner_id={user} OR loser_id={user}')
        averageScore = cursor.fetchone()[0]

        cursor.execute(f'UPDATE users SET gamesPlayed={gamesPlayed}, gamesWon={gamesWon}, averageScore={averageScore} WHERE user_id={user}')

    conn.commit()


    cursor.close()

except sqlite3.Error as error:
    print('Error occurred - ', error)

finally:
    if conn:
        conn.close()