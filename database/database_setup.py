import os
import random
import sqlite3

try:
    if os.path.isfile('pickleDatabase.db'):
        os.remove('pickleDatabase.db')

    conn = sqlite3.connect('pickleDatabase.db')
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE users(user_id, username, passwordHash, gamesPlayed, gamesWon, averageScore)')
    cursor.execute('CREATE TABLE games(game_id, winner_id, loser_id, winner_points, loser_points)')

    cursor.execute("""INSERT INTO users VALUES
                   (0, 'ninjamike1211', 'ah50jkg0q', 10, 2, 3.9),
                   (1, 'aje0714', 'asdfi324hl', 72, 59, 8.5),
                   (2, 'BOT-Lee', '092bhng082h', 5, 1, 2.3),
                   (3, 'jpk102pitt', '3hladf09hy3n', 21, 11, 6.3)
                   """)
    games = ''
    for i in range(0,10):
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

    cursor.close()

except:
    print("Error!")

finally:
    if conn:
        conn.close()