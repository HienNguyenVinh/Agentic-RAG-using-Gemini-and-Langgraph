from RagCore.Tools.tools import related_products_search, product_search, create_order
from Database.chat_history_services import get_chat_history, format_chat_history, save_message
import json
from typing import AsyncGenerator
from google import genai
from .prompts import RAG_PROMPT


class RagAgent():
    def __init__(self, client, model_name: str="gemini-2.0-flash-lite"):
        self.model_name = model_name
        self.client = client
        self.tools = [related_products_search, product_search, create_order]
    
    def get_answer(self, query: str, thread_id: str) -> str:

        chat_history = format_chat_history(get_chat_history(thread_id=thread_id))
        chat_history.append(genai.types.Content(role="user", parts=[genai.types.Part(text=query)]))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=chat_history,
            config=genai.types.GenerateContentConfig(
                system_instruction=RAG_PROMPT,
                tools=self.tools,
                automatic_function_calling={"disable":False}
            )
        )
        
        print(response.text)
        return response.text


    async def get_stream_answer(self, query: str, thread_id: str) -> AsyncGenerator[str, None]:
        full_response = ""
        model_function_call_str = None
        model_function_response_str = None

        chat_history = format_chat_history(get_chat_history(thread_id=thread_id))
        # print(chat_history)
        chat_history.append(genai.types.Content(role="user", parts=[genai.types.Part(text=query)]))

        async for chunk in await self.client.aio.models.generate_content_stream(
            model=self.model_name,
            contents=chat_history,
            config=genai.types.GenerateContentConfig(
                system_instruction=RAG_PROMPT,
                tools=self.tools,
                automatic_function_calling={"disable":False}
            )
        ):

            if chunk.automatic_function_calling_history:
                for content in chunk.automatic_function_calling_history:
                    if content.parts[0].function_call:
                        fc_dict = {
                            'name': content.parts[0].function_call.name,
                            'args': content.parts[0].function_call.args
                        }
                        model_function_call_str = json.dumps(fc_dict, ensure_ascii=False)

                    if content.parts[0].function_response:
                        fr_dict = {
                            'name': content.parts[0].function_response.name,
                            'response': content.parts[0].function_response.response
                        }
                        model_function_response_str = json.dumps(fr_dict, ensure_ascii=False)
            
            if chunk.text:
                full_response += chunk.text
                yield chunk.text
        
        if full_response:
            # print(model_function_call_str)
            # print("-" * 100)
            # print(model_function_response_str)
            save_message(thread_id, query, full_response, model_function_call_str, model_function_response_str)
