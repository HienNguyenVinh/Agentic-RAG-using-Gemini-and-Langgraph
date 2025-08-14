from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from typing import Dict, Literal, cast, Any, TypedDict
from dataclasses import dataclass
from dotenv import load_dotenv
import logging
import os

from .states import AgentState, InputState
from agent.sub_graph import order_graph, rag_graph
from.prompts import ROUTER_SYSTEM_PROMPT, MORE_INFO_SYSTEM_PROMPT, EXTRACT_ORDER_SYSTEM_PROMPT, RAG_RESPONSE_PROMPT, ORDER_RESPONSE_PROMPT, CHITCHAT_RESPONSE_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL")

model = ChatGoogleGenerativeAI(model=GEMINI_MODEL)

@dataclass
class Router:
    """Routing schema for the bookstore chatbot.
    Field 'router' must be either 'order' or 'product_infomation'."""
    router: Literal["order", "product_infomation", "chitchat"]

@dataclass
class OrderInfo:
    """Order extraction schema.
    All fields are integers. Use 0 to signal unknown/missing values."""
    user_id: int
    product_id: int
    quantity: int


async def determine_agent(
        state: AgentState, *, config: RunnableConfig
) -> Dict[str, str]:
    """
    Classify the user's intent and determine the processing route.

    Args:
        state (AgentState): Current conversation state including messages.
        config (RunnableConfig): Runtime configuration for execution.

    Returns:
        Dict[str, str]: Dictionary with key 'router' set to 'order' or 'product_infomation'.
    """

    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
    ] + state.messages

    logging.info("---ANALYZE AND ROUTE QUERY---")
    logging.info(f"MESSAGES: {state.messages}")
    response = cast(Router, await model.with_structured_output(Router).ainvoke(messages))
    logging.info(f"ROUTER TO {response}")
    print(state.messages[-1].content)
    return {"router": response['router']}

def router_query(state: AgentState) -> Literal["check_order_info", "rag"]:
    """
    Map the router value to the next graph node name.

    Args:
        state (AgentState): Current conversation state with the 'router' value.

    Returns:
        Literal: Next node name ('check_order_info' or 'rag').
    """
    if state.router == "order":
        return "check_order_info"
    elif state.router == "product_infomation":
        return "rag"
    elif state.router == "chitchat":
        return "response"
    else:
        raise ValueError(f"Unknown router type: {state.router}")
    
async def rag(state: AgentState) -> Dict[str, Any]:
    """
    Retrieve product-related information using a RAG pipeline.

    Args:
        state (AgentState): Current conversation state with user messages.

    Returns:
        Dict[str, Any]: Dictionary containing 'retrieved_products'.
    """

    result = await rag_graph.ainvoke({"user_query": state.messages[-1].content})
    # logger.info(f"RETRIEVAL SUCCESSED: {result}")
    return {"retrieved_products": result['retrieved_products']}

def check_order_info(state: AgentState) -> Dict[str, str]:
    """
    Identify missing order details in the state.

    Args:
        state (AgentState): Current conversation state.

    Returns:
        Dict[str, str]: Dictionary with key 'lack_of_order_info' containing missing fields.
    """

    lack_info = []
    if state.user_id is not None:
        lack_info.append("user_id")
    if state.current_product_id is not None:
        lack_info.append("current_product_id")
    if state.current_product_quantity is not None:
        lack_info.append("current_product_quantity")
    return {"lack_of_order_info": lack_info}

def decide_create_or_ask(state: AgentState) -> Literal["create_order", "ask_for_order_info"]:
    """
    Decide whether to create the order or request more information.

    Args:
        state (AgentState): Current conversation state including missing info list.

    Returns:
        Literal: 'create_order' or 'ask_for_order_info'.
    """

    if state.lack_of_order_info:
        return "ask_for_order_info"
    else:
        return "create_order" 

async def ask_for_order_info(
        state: AgentState, *, config: RunnableConfig
) -> Dict[str, list[BaseMessage]]:
    """
    Generate a question to ask the user for missing order information.

    Args:
        state (AgentState): Current conversation state.
        config (RunnableConfig): Runtime configuration.

    Returns:
        Dict[str, list[BaseMessage]]: Dictionary containing the generated question message.
    """

    messages = [
        {"role": "system", "content": MORE_INFO_SYSTEM_PROMPT},
    ] + state.messages

    response = await model.ainvoke(messages)

    return {"messages": [response]}

async def extract_order_info(
        state: AgentState, *, config: RunnableConfig
) -> Dict[str, Any]:
    """
    Extract structured order information from the user's reply.

    Args:
        state (AgentState): Current conversation state.
        config (RunnableConfig): Runtime configuration.

    Returns:
        Dict[str, Any]: Dictionary with user_id, current_product_id, and current_product_quantity.
    """

    messages = [
        {"role": "system", "content": EXTRACT_ORDER_SYSTEM_PROMPT},
    ] + state.messages

    response = cast(OrderInfo, await model.with_structured_output(OrderInfo).ainvoke(messages))

    return {
        "user_id": response.user_id,
        "current_product_id": response.product_id,
        "current_product_quantity": response.quantity,
    }

async def create_order(state: AgentState):
    """
    Submit the order request to the order service.

    Args:
        state (AgentState): State containing all necessary order information.

    Returns:
        Dict[str, Any]: Dictionary with the order state/status.
    """

    result = await order_graph.ainvoke({
        "user_id": state.user_id,
        "product_id": state.current_product_id,
        "quantity": state.current_product_quantity,
    })

    return {
        "order_state": result['order_state']
    }


async def response(
        state: AgentState, *, config: RunnableConfig
) -> Dict[str, str]:
    """
    Generate the final response message for the user.

    Args:
        state (AgentState): Current conversation state.
        config (RunnableConfig): Runtime configuration.

    Returns:
        Dict[str, str]: Dictionary containing the response message list.
    """

    if state.router == "product_infomation":
        prompt = RAG_RESPONSE_PROMPT + "\n\nRETRIEVED_PRODUCTS:\n" + "\n".join(state.retrieved_products)
    elif state.router == "order":
        prompt = ORDER_RESPONSE_PROMPT + "\n\nORDER_STATE:\n" + state.order_state
    elif state.router == "chitchat":
        prompt = CHITCHAT_RESPONSE_PROMPT

    messages = [
        {"role": "system", "content": prompt},
    ] + state.messages

    response = await model.ainvoke(messages)

    return {"messages": [response]}


conn = sqlite3.connect(database="chathistory.db", check_same_thread=False)
checkpointer = SqliteSaver()

builder = StateGraph(AgentState, input=InputState)

builder.add_node(determine_agent)
builder.add_node(rag)
builder.add_node(check_order_info)
builder.add_node(create_order)
builder.add_node(ask_for_order_info)
builder.add_node(extract_order_info)
builder.add_node(response)

builder.add_edge(START, "determine_agent")
builder.add_conditional_edges("determine_agent", router_query)
builder.add_conditional_edges("check_order_info", decide_create_or_ask)
builder.add_edge("ask_for_order_info", "extract_order_info")
builder.add_edge("extract_order_info", "check_order_info")
builder.add_edge("create_order", "response")
builder.add_edge("rag", "response")
builder.add_edge("response", END)

graph = builder.compile(checkpointer=checkpointer)
