from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent.graph import graph
from google import genai
from dotenv import load_dotenv
import logging
import json
from typing import AsyncGenerator
from utils import new_uuid

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__)

thread_id = new_uuid()
config = {"configurable": {"thread_id": thread_id}}

class Query(BaseModel):
    query: str
    config: dict

class Response(BaseModel):
    answer: str

async def text_generator(query: str, config: dict) -> AsyncGenerator[str, None]:
    try:
        async for event in graph.astream(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
            stream_mode="messages",
        ):
            text = event[0].content
            if text:
                yield f"data: {json.dumps({'context': text})}\n\n"
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)})})"
        
router = APIRouter()

@router.post("/chat/stream")
async def get_stream_answer(query: Query):
    return StreamingResponse(
        text_generator(query.query, query.config),
        media_type="text/event-stream",
    )

@router.post("/chat")
async def get_answer(query: Query):
    try:
        logging.info(f"Received query: {query.query}")
        answer = graph.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
        )
        logging.info(f"Answer: {answer}")
        if not answer:
            raise ValueError("Can't get answer")
        
        return Response(answer=answer)

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500,
                            detail="Internal Server Error: " + str(e))