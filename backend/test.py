from RagCore.Tools.tools import related_products_search, product_search, create_order
from Database.orders_services import get_all_orders
from Database.init_db import init_db_tables, seed_data
from Database.chat_history_services import clear_chat_history, format_chat_history, get_chat_history
from RagCore.core import RagAgent
from google import genai
from dotenv import load_dotenv
from settings import MODEL_NAME
import asyncio
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

rag = RagAgent(client=client, model_name=MODEL_NAME)

# res = rag.get_answer("Tôi muốn mua sách về mèo.", "test")

clear_chat_history(thread_id="test")

# print(format_chat_history(get_chat_history(thread_id="test")))


while True:
    query = input("Nhập câu hỏi: ")
    if query == "exit":
        break
    
    async def stream_ans():
        async for chunk in rag.get_stream_answer(query=query, thread_id="test"):
            print(chunk)
    print("-" * 100)

    asyncio.run(stream_ans())


# init_db_tables()
# seed_data()

# res = get_all_orders(1)
# print(res)


# res = related_products_search("sách con mèo")
# print(res)

# res2 = product_search("chuyện con mèo")
# print(res2)

# res3 = create_order(1, 1, 10, 100000)
# print(res3)