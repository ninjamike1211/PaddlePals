import sqlite3

try:

    conn = sqlite3.connect('pickleDatabase.db')
    cursor = conn.cursor()

    query = input('Enter an SQL query: ')
    cursor.execute(query)
    
    result = cursor.fetchall()
    print(f'Result: {result}')

    cursor.close()

except:
    print("Error!")

finally:
    if conn:
        conn.close()