

import sqlite3

class WebServer:
    def __init__(self, dbFile = 'pickle.db'):
        self.dbFile = dbFile
        self.dbCon = sqlite3.connect(self.dbFile)
        self.cursor = self.dbCon.cursor()

    def handle_request(self, request_type, uri, params):
        if request_type == 'GET':
            pass

        elif request_type == 'PUSH':
            pass

        elif request_type == 'POST':
            pass


    def close(self):
        self.cursor.close()
        self.dbCon.close()


try:

    server = WebServer()

    while True:

        query = input('Enter an API command: ')
        if query == 'exit':
            break

        cursor.execute(query)
        
        result = cursor.fetchall()
        print(f'Result: {result}')


    cursor.close()

except sqlite3.Error as error:
    print('Error occurred - ', error)

finally:
    if conn:
        conn.close()