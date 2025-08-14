from typing import Optional, Dict, List
from .init_db import get_db_connection
from decimal import Decimal

def configuration_for_search(vector_size: int=768):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TEXT SEARCH DICTIONARY public.vietnamese (
                        TEMPLATE = pg_catalog.simple,
                        STOPWORDS = vietnamese
                    );
                    CREATE TEXT SEARCH CONFIGURATION public.vietnamese (
                        COPY = pg_catalog.english
                    );
                    ALTER TEXT SEARCH CONFIGURATION public.vietnamese
                        ALTER MAPPING
                            FOR asciiword, asciihword, hword_asciipart, hword, hword_part, word
                            WITH vietnamese;
                """)

                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                cursor.execute(f"""
                    ALTER TABLE Product
                    ALTER COLUMN embedding_vector TYPE vector({vector_size})
                    USING embedding_vector::vector({vector_size});
                """)

                cursor.execute("CREATE INDEX ON Product USING ivfflat (embedding_vector vector_cosine_ops);")
                conn.commit()
    except Exception as err:
        print("Lỗi configuration: ",err)

                
def hybrid_search(keyword: str, query_vector: List, rrf_k: int=60, k: int=5) -> Optional[List[Dict]]:
    text_results = get_related_product_by_word(keyword, k=k)
    vector_results = get_related_product_by_vector(query_vector, k=k)
    
    # print(text_results)
    # print("*"*80)
    # print(vector_results)

    if not text_results and not vector_results:
        return None
    if not text_results:
        return sorted(vector_results, key=lambda x: x.get('distance', float('inf')))[:k]
    if not vector_results:
        return text_results[:k]

    all_items_dict = {item['id']: item for item in vector_results}
    all_items_dict.update({item['id']: item for item in text_results}) 

    text_ranks = {item['id']: rank + 1 for rank, item in enumerate(text_results)}
    vector_ranks = {item['id']: rank + 1 for rank, item in enumerate(vector_results)}

    all_ids = set(text_ranks.keys()).union(set(vector_ranks.keys()))

    rrf_scores = {}
    for id_ in all_ids:
        score = 0.0
        text_rank = text_ranks.get(id_)
        if text_rank is not None:
            score += 1.0 / (rrf_k + text_rank)

        vector_rank = vector_ranks.get(id_)
        if vector_rank is not None:
            score += 1.0 / (rrf_k + vector_rank)

        rrf_scores[id_] = score

    # Sắp xếp các ID dựa trên điểm RRF giảm dần
    sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

    final_results = []
    for id_ in sorted_ids[:k]:
        if id_ in all_items_dict:
            item = all_items_dict[id_].copy()
            item['rrf_score'] = rrf_scores[id_]
            print(item['name'])
            print(item['rrf_score'])
            final_results.append(item)
    return final_results


def get_related_product_by_word(keyword: str, k: int=5) -> Optional[List[Dict]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                SELECT id, name, author, category, description, price, stock_quantity,
                       ts_rank(to_tsvector('vietnamese', description || ' ' || name || ' ' || author || ' ' || category), 
                               plainto_tsquery('vietnamese', %s)) AS rank
                FROM Product
                WHERE to_tsvector('vietnamese', description || ' ' || name || ' ' || author || ' ' || category) @@ plainto_tsquery('vietnamese', %s)
                ORDER BY rank DESC
                LIMIT %s;
                """, (keyword, keyword, k)
                )
                results = cursor.fetchall()
                # print(results)
                # print("_" * 80)
                
                return results
            
    except Exception as e:
        # print(f"Lỗi khi tìm kiếm theo word: {e}")
        print(f"Lỗi khi tìm kiếm theo word ({type(e).__name__}): {e}") 
        return None
    
def get_related_product_by_vector(query_vector: List, k: int=5) -> Optional[List[Dict]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, author, category, description, price, stock_quantity, 
                            (embedding_vector <-> %s) AS distance
                    FROM Product 
                    ORDER BY distance 
                    LIMIT %s;
                    """,
                    (str(query_vector), k)
                )

                results = cursor.fetchall()
                # print(results)
                return results
            
    except Exception as e:
        # print(f"Lỗi khi tìm kiếm theo vector: {e}")
        print(f"Lỗi khi tìm kiếm theo vector ({type(e).__name__}): {e}") 
        return None


def check_product_stock(product_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT stock_quantity FROM Product WHERE id = %s;", (product_id,))
                result = cursor.fetchone()

                if result:
                    return result['stock_quantity']
                else:
                    return None

    except Exception as err:
        print(err)
        return None
        
def update_product_stock(product_id: int, quantity: int) -> bool:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE Product
                    SET stock_quantity = stock_quantity - %s
                    WHERE id = %s;
                """, (quantity, product_id)
                )
                conn.commit()
                return True
            
    except Exception as err:
        print(err)
        return False

def get_product_by_name(product_name: str) -> Optional[Dict]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT id, author, category, highlight, description, price, stock_quantity 
                FROM Product
                WHERE LOWER(name) LIKE LOWER(%s);""", 
                ("%" + product_name + "%",)
                )

                result = cursor.fetchone()
                if result:
                    result['price'] = Decimal(result['price'])
                    
                return result

    except Exception as err:
        print(err)
        return None
    
def get_product_by_id(product_id: int) -> Optional[Dict]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT id, author, category, highlight, description, price, stock_quantity 
                FROM Product
                WHERE id = %s;""", 
                (product_id,)
                )

                result = cursor.fetchone()
                if result:
                    result['price'] = Decimal(result['price'])
                    
                return result

    except Exception as err:
        print(err)
        return None


