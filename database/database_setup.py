import os
import random
import sqlite3
import hashlib

users = {
    'ninjamike1211': 'password0',
    'aje0714': 'password1',
    'BOT-Lee': 'password2',
    'jpk102pitt': 'password3',
    'testUser': 'testPassword',
}

total_games = 200

try:
    if os.path.isfile('pickle.db'):
        os.remove('pickle.db')

    conn = sqlite3.connect('pickle.db')
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE users(user_id INT, username TEXT, passwordHash BLOB, valid INT, gamesPlayed INT, gamesWon INT, averageScore REAL)')
    cursor.execute('CREATE TABLE games(game_id INT, winner_id INT, loser_id INT, winner_points INT, loser_points INT)')
    cursor.execute('CREATE TABLE friends(userA, userB)')

    for i, (username,password) in enumerate(users.items()):
        pass_hash = bytearray(hashlib.sha256(password.encode()).digest())

        cursor.execute("INSERT INTO users VALUES (?, ?, ?, 1, 0, 0, 0.0)", (i+1, username, pass_hash))

    games = ''
    for i in range(0, total_games):
        user_win = random.randint(1, len(users))
        user_lose = random.randint(1, len(users)-1)
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

    for user in range(1,len(users)+1):
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