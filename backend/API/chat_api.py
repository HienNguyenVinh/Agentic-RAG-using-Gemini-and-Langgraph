from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from RagCore import RagAgent
from google import genai
from dotenv import load_dotenv
from settings import MODEL_NAME
import logging
import json
from typing import AsyncGenerator
import os


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

rag = RagAgent(client=client, model_name=MODEL_NAME)

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__)

router = APIRouter()

class Query(BaseModel):
    query: str
    thread_id: str

class Response(BaseModel):
    answer: str

@router.post("/chat")
async def get_answer(query: Query):
    try:
        logging.info(f"Received query: {query.query}")
        answer = rag.get_answer(query=query.query, thread_id=query.thread_id)
        logging.info(f"Answer: {answer}")
        if not answer:
            raise ValueError("Can't get answer")
        
        return Response(answer=answer)

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500,
                            detail="Internal Server Error: " + str(e))


async def text_generator(query: str, thread_id: str) -> AsyncGenerator[str, None]:
    try:
        async for text in rag.get_stream_answer(query=query, thread_id=thread_id):
            if text:
                yield f"data: {json.dumps({'context': text})}\n\n"
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)})})"
        

@router.post("/chat/stream")
async def get_stream_answer(query: Query):
    return StreamingResponse(
        text_generator(query.query, query.thread_id),
        media_type="text/event-stream",
    )
    