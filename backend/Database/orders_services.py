from typing import Optional, Dict, List
from .init_db import get_db_connection
from decimal import Decimal

def create_new_order(user_id: int, product_id: int, quantity: int, total_amount: float) -> bool:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                total_amount = Decimal(total_amount)
                cursor.execute("""INSERT INTO "order" (user_id, product_id, quantity, total_amount) 
                                VALUES (%s, %s, %s, %s)""", 
                                (user_id, product_id, quantity, total_amount)
                                )
                conn.commit()
                return True
    except Exception as e:
        print(e)
        return False

def get_all_orders(user_id: int) -> Optional[List[Dict]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT p.name AS product_name, o.quantity, o.total_amount
                    FROM "order" o
                    JOIN Product p ON o.product_id = p.id
                    WHERE o.user_id = %s
                ''', (user_id,))
                results = cursor.fetchall()
                # print(results)
                return results
    except Exception as e:
        print(e)
        return None