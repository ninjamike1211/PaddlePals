import random

from .database_api import restAPI

def setup_db(dbPath:str, users:dict = None, gen_games:int = 0):
    api = restAPI(dbPath, False, True)

    if users:
        for username,password in users.items():
            api._api_user_create({'username':username, 'password':password})

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

            api._api_game_register({'timestamp':0, 'game_type':0, 'winner_id':user_win, 'loser_id':user_lose, 'winner_points':points_win, 'loser_points':points_lose})
    
    api.close()



if __name__ == '__main__':
    users = {
        'ninjamike1211': 'passUserID1',
        'aje0714': 'passUserID2',
        'BOT-Lee': 'passUserID3',
        'jpk102pitt': 'passUserID4',
        'testUser': 'testPassword',
    }
    gen_games = 200

    setup_db('pickle.db', users, gen_games)
