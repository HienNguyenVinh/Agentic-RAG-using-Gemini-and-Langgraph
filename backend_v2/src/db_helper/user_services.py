from .db_connection import get_db_connection

def insert_user(username, address):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                               INSERT INTO "user" (username, address) 
                               VALUES (%s, %s)""", 
                               (username, address)
                               )
                conn.commit()
                return True
    except Exception as err:
        print(err)
        return False