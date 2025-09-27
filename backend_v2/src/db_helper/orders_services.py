from typing import Optional, Dict, List
from .init_db import get_db_connection
from decimal import Decimal

def create_new_order(user_name: str, user_phone: str, user_address: str, product_id: int, quantity: int, total_amount: float) -> Optional[int]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                total_amount = Decimal(total_amount)
                cursor.execute("""INSERT INTO "order" (user_name, user_phone, user_address, product_id, quantity, total_amount) 
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING id;
                               """, 
                                (user_name, user_phone, user_address, product_id, quantity, total_amount)
                                )
                new_order_id = cursor.fetchone()[0]
                conn.commit()
                return new_order_id
    except Exception as e:
        print(e)
        return None

def get_all_orders(user_name: str) -> Optional[List[Dict]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT p.name AS product_name, o.quantity, o.total_amount
                    FROM "order" o
                    JOIN Product p ON o.product_id = p.id
                    WHERE o.user_name = %s
                ''', (user_name,))
                results = cursor.fetchall()
                # print(results)
                return results
    except Exception as e:
        print(e)
        return None