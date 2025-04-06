import os
import dotenv
import psycopg
from psycopg.rows import dict_row


dotenv.load_dotenv()

db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

def get_db_connection():
    return psycopg.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
        port=db_port,
        row_factory=dict_row    #Trả về kết quả dưới dạng dictionary thay vì tuple
    )
