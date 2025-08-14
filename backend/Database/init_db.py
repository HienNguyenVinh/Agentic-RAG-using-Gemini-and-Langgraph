import pandas as pd
from sqlalchemy import create_engine, text
from .user_services import insert_user
from .db_connection import get_db_connection
from .db_connection import db_name, db_user, db_password, db_host, db_port
from .chat_history_services import creat_db_chat_history_table
from .product_services import configuration_for_search



def init_db_tables():
    try:
        with get_db_connection() as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                create_user_table = """
                CREATE TABLE IF NOT EXISTS "user" (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    address VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """

                create_product_table = """
                CREATE TABLE IF NOT EXISTS product (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    author VARCHAR(255),
                    category VARCHAR(255) NOT NULL,
                    highlight TEXT,
                    description TEXT,
                    image_url VARCHAR(200),
                    embedding_vector TEXT,
                    price NUMERIC(10, 2) NOT NULL,
                    stock_quantity INT DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """

                create_order_table = """
                CREATE TABLE IF NOT EXISTS "order" (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL,
                    total_amount NUMERIC(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES "product"(id) ON DELETE CASCADE
                );
                """

                cursor.execute(create_user_table)
                print("Bảng User đã được tạo thành công!")

                cursor.execute(create_product_table)
                print("Bảng Product đã được tạo thành công!")

                cursor.execute(create_order_table)
                print("Bảng Order đã được tạo thành công!")

                creat_db_chat_history_table()

                print("Tất cả các bảng đã được tạo thành công!")

    except Exception as error:
        print(f"Lỗi khi tạo bảng: {error}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            print("Kết nối đến PostgreSQL đã đóng.")


def seed_product_data():
    df = pd.read_csv(r'D:\PythonProject\DemoRag2\backend\Database\product_data\embedding_data.csv')
    df = df.drop(columns=['description_length', 'full_description', 'summarize'], errors='ignore')
    df['image_url'] = "D:\PythonProject\DemoRag2\backend\Database\img.png"

    engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}')
    print("connected!")
    # Upload dữ liệu vào bảng Product
    df.to_sql('product', engine, if_exists='append', index=False)
    print("Thêm product data thành công!")

def seed_data():
    users = [
        ("user1", "Hanoi, Vietnam"),
        ("user2", "Ho Chi Minh City, Vietnam"),
        ("user3", "Da Nang, Vietnam")
    ]

    for user in users:
        insert_user(user[0], user[1])

    seed_product_data()
    


if __name__ == "__main__":
    init_db_tables()
    seed_data()
    configuration_for_search()
    
