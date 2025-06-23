import os
import random
import sqlite3
import hashlib

from .database_api import restAPI

def setup_db(dbPath:str, users:dict = None, gen_games:int = 0):

    try:
        if os.path.isfile(dbPath):
            os.remove(dbPath)

        conn = sqlite3.connect(dbPath)
        cursor = conn.cursor()

        cursor.execute('CREATE TABLE users(user_id INT, username TEXT, passwordHash BLOB, salt BLOB, valid INT, gamesPlayed INT, gamesWon INT, averageScore REAL)')
        cursor.execute('CREATE TABLE games(game_id INT, winner_id INT, loser_id INT, winner_points INT, loser_points INT)')
        cursor.execute('CREATE TABLE friends(userA INT, userB INT)')


        pass_hash, salt = restAPI.gen_password_hash('root')
        cursor.execute("INSERT INTO users VALUES (0, 'admin', ?, ?, 0, NULL, NULL, NULL)", (pass_hash, salt))
        conn.commit()

        if users:
            for i, (username,password) in enumerate(users.items()):
                pass_hash, salt = restAPI.gen_password_hash(password)

                cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, 1, 0, 0, 0.0)", (i+1, username, pass_hash, salt))

            for i in range(0, gen_games):
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

                cursor.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?)", (i, user_win, user_lose, points_win, points_lose))

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


if __name__ == '__main__':
    users = {
        'ninjamike1211': 'password0',
        'aje0714': 'password1',
        'BOT-Lee': 'password2',
        'jpk102pitt': 'password3',
        'testUser': 'testPassword',
    }
    gen_games = 200

    setup_db('pickle.db', users, gen_games)
