# Code to query the SQLite database.
# The following resource was used as reference material:
#   https://www.geeksforgeeks.org/python-sqlite-connecting-to-database/

import sqlite3

try:

    conn = sqlite3.connect('pickle.db')
    cursor = conn.cursor()

    while True:

        query = input('Enter an SQL query: ')
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