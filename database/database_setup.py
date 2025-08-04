import random
import time

from .database_api import restAPI

def setup_db(dbPath:str, users:dict = None, gen_games:int = 0):
    api = restAPI(dbPath, False, True)

    if users:
        for username,password in users.items():
            api._api_user_create({'username':username, 'password':password})

        for i in range(0, gen_games):
            user_win = random.randint(0, len(users))
            user_lose = random.randint(0, len(users)-1)
            if user_lose >= user_win:
                user_lose += 1

            if user_win == 0:
                user_win = -1
            if user_lose == 0:
                user_lose = -1

            points_win = random.randint(0,15)
            if points_win < 11:
                points_win = 11

            if points_win <= 11:
                points_lose = random.randint(0,10)
            else:
                points_lose = points_win - 2

            timestamp = int(time.time() - ((gen_games-i) * 86400))

            api._api_game_register({'timestamp':timestamp, 'game_type':0, 'winner_id':user_win, 'loser_id':user_lose, 'winner_points':points_win, 'loser_points':points_lose})
    
    api.close()



if __name__ == '__main__':
    users = {
        'ninjamike1211': 'passUser_ID1',
        'aje0714': 'passUser_ID2',
        'BOT-Lee': 'passUser_ID3',
        'jpk102pitt': 'passUser_ID4',
        'testUser': 'test_USER_1234',
    }
    gen_games = 200

    print('Generating database...')
    setup_db('database/pickle.db', users, gen_games)
    print("Completed!")
