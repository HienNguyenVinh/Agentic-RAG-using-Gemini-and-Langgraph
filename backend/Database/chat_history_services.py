from .db_connection import get_db_connection
from typing import Dict, Optional, List
from google.genai import types
from google.genai.types import FunctionCall, FunctionResponse
import json

def creat_db_chat_history_table():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Tạo UUID cho mỗi tin nhắn
                cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

                # Tạo bảng
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS message (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        thread_id VARCHAR(255) NOT NULL,
                        user_question TEXT NOT NULL,
                        bot_answer TEXT NOT NULL,
                        function_call TEXT,
                        function_response TEXT, 
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Tạo index để tăng tốc truy vấn tin nhắn
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_message_thread_id 
                    ON message(thread_id)
                """)
                conn.commit()
    except Exception as error:
        print(f"Lỗi khi tạo bảng: {error}")

def clear_chat_history(thread_id: Optional[str] = None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if thread_id:
                    cursor.execute("DELETE FROM message WHERE thread_id = %s;", (thread_id,))
                else:
                    cursor.execute("TRUNCATE TABLE message;")
                conn.commit()
                print(f"Đã xóa {'tất cả' if not thread_id else 'thread ' + thread_id} dữ liệu trong bảng message.")
    except Exception as error:
        print(f"Lỗi khi xóa dữ liệu: {error}")

def save_message(thread_id: str, user_question: str, bot_answer: str, function_call: str, function_response: str) -> Optional[Dict]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO message (thread_id, user_question, bot_answer, function_call, function_response) VALUES (%s, %s, %s, %s, %s) RETURNING id::text",
                    (thread_id, user_question, bot_answer, function_call, function_response)
                )
                result = cursor.fetchone()
                if result:
                    return result['id']
                return None
    except Exception as error:
        print(f"Lỗi khi lưu tin nhắn: {error}")
        return None

def get_chat_history(thread_id: str, limit: int=20) -> Optional[Dict]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT thread_id, user_question, bot_answer, function_call, function_response, created_at 
                    FROM message 
                    WHERE thread_id = %s 
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (thread_id, limit)
                )
                results = cursor.fetchall()
                if results:
                    return results
                return None
    except Exception as error:
        print(f"Lỗi khi lấy lịch sử trò chuyện: {error}")
        return None
    
def format_chat_history(chat_history: List[Dict]) -> Optional[List]:
    if chat_history:
        formatted_history = []
        for message in reversed(chat_history):
            formatted_history.append(types.Content(role="user", parts=[types.Part(text=message["user_question"])]))
            if message["function_call"]:
                fc_dict = json.loads(message["function_call"])
                formatted_history.append(types.Content(role="model", 
                                                       parts=[types.Part(function_call=FunctionCall(name = fc_dict["name"], args=fc_dict["args"]))]))

            if message["function_response"]:
                fr_dict = json.loads(message["function_response"])
                formatted_history.append(types.Content(role="user", 
                                                       parts=[types.Part(function_response=FunctionResponse(name=fr_dict["name"], response=fr_dict["response"]))]))
                
            formatted_history.append(types.Content(role="model", parts=[types.Part(text=message["bot_answer"])]))
    else:
        return []

    return formatted_history
    