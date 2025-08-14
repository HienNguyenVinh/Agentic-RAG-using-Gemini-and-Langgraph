from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, StateGraph, END
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from mxbai_rerank import MxbaiRerankV2
from typing import TypedDict, cast, Dict, List, Any
from dotenv import load_dotenv
import logging
import asyncio
import os

from .tools import vector_search, full_text_search
from .prompt import GENERATE_QUERY_SYSTEM_PROMPT, RERANK_SYSTEM_PROMPT  
from .states import RAGState
 
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv('GEMINI_MODEL')

async def generates_keyword(
        state: RAGState, *, config: RunnableConfig
) -> Dict[str, str]:
    """
    Generate search queries for vector and full-text search from a user query.

    Args:
        user_query (str): The raw user query or request text.
        config (RunnableConfig): Runtime configuration passed by the graph runner.

    Returns:
        Dict[str, str]: A dictionary with keys:
            - "vector_search_query": query optimized for vector search (semantic).
            - "fts_keyword": keyword(s) optimized for full-text search.
    """

    class Response(TypedDict):
        vector_search_query: str
        fts_keyword: str

    logger.info("___generating queries...")
    model = ChatGoogleGenerativeAI(model=GEMINI_MODEL)
    messages = [
        {"role": "system", "content": GENERATE_QUERY_SYSTEM_PROMPT},
        {"role": "human", "content": state.user_query}
    ]
    response = cast(Response, await model.with_structured_output(Response).ainvoke(messages))
    logger.info(f"___vts query: {response['vector_search_query']}, fts keyword: {response['fts_keyword']}")

    return response

async def hybrid_search(
    state: RAGState, *, config: RunnableConfig
) -> Dict[str, List[Document]]:
    """
    Perform hybrid retrieval by running both vector search and full-text search,
    then merge and deduplicate the results.

    Args:
        state (RAGState): State object carrying the extraction results (expects
            state.vector_search_query and state.fts_keyword to be set).
        config (RunnableConfig): Runtime configuration passed by the graph runner.

    Returns:
        Dict[str, List[Document]]: A dictionary with key:
            - "retrieved_products": list of merged and deduplicated Document objects
              returned from vector and full-text searches.
    """

    logger.info("___retrieving products...")
    results = await asyncio.gather(
        vector_search(state.vector_search_query),
        full_text_search(state.fts_keyword),
        return_exceptions=True
    )

    vector_results, fts_results = results
    if isinstance(vector_results, Exception):
        logger.error("Vector search failed", exc_info=vector_results)
        vector_results = []
    if isinstance(fts_results, Exception):
        logger.error("Full-text search failed", exc_info=fts_results)
        fts_results = []

    seen = set()
    combined: List[Document] = []
    for doc in vector_results + fts_results:
        uid = doc.metadata.get("name")
        if uid and uid not in seen:
            combined.append(doc)
            seen.add(uid)

    return {"retrieved_products": combined}

from langchain.schema import Document
from typing import List

def format_products(products: List[Document]) -> str:
    """
    Format a list of Document objects into a human-readable text block.

    Args:
        products (List[Document]): List of product Documents (with metadata and page_content).

    Returns:
        str: Multi-line string describing each product (name, author, category, price,
             score and description) suitable for display in prompts or messages.
    """

    lines = []
    for idx, doc in enumerate(products, start=1):
        md = doc.metadata
        lines.append(f"Sản phẩm #{idx}:")
        lines.append(f"- Tên       : {md.get('name', '—')}")
        lines.append(f"- Tác giả   : {md.get('author', '—')}")
        lines.append(f"- Thể loại  : {md.get('category', '—')}")
        lines.append(f"- Giá       : {md.get('price', 'Liên hệ để trao đổi giá chi tiết.')}")
        lines.append(f"- Đánh giá  : {md.get('score', '—')}")
        desc = doc.page_content.strip()
        if desc:
            lines.append("- Mô tả     :")
            for line in desc.splitlines():
                lines.append(f"  {line}")
        lines.append("-" * 40)

    if lines and lines[-1].startswith("-"):
        lines.pop()

    return "\n".join(lines)

class RerankResponse(TypedDict):
    reranked_list: list[str]
    found: bool

async def rerank(
        state: RAGState, *, config: RunnableConfig
) -> Dict[str, RerankResponse]:
    """
    Re-rank retrieved products according to the original user query using the LLM.
    Updates state.retrieved_products and state.found.

    Args:
        state (RAGState): State containing state.user_query and state.retrieved_products.
        config (RunnableConfig): Runtime configuration passed by the graph runner.

    Returns:
        Dict[str, RerankResponse]: A dictionary with keys:
            - "retrieved_products": the reranked list (may be the original list on failure).
            - "found" (bool): whether the LLM indicated relevant items were found.
    """

    logger.info("___reranking...")
    model = MxbaiRerankV2("mixedbread-ai/mxbai-rerank-base-v2")
    query = state.user_query
    documents = format_products(state.retrieved_products)

    try:
        results = model.rank(query, documents, return_documents=True, top_k=5)
        logger.info("___rerank successed...")
        found = True
    except Exception as e:
        logger.error("Rerank failed, fallback to original", exc_info=e)
        results = state.retrieved_products
        found = False

    return {"retrieved_products": results, "found": found}

def respond(
        state: RAGState, *, config: RunnableConfig
) -> Dict[str, Any]:
    """
    Prepare the final retrieval output to be returned by the RAG pipeline.
    Limits the number of returned results for the response stage.

    Args:
        state (RAGState): State containing state.retrieved_products and state.found.
        config (RunnableConfig): Runtime configuration passed by the graph runner.

    Returns:
        Dict[str, Any]: A dictionary with key:
            - "retrieved_products": top-N search results (or a user-facing message
              string if no matching products were found).
    """

    if state.found:
        search_results = state.retrieved_products
    else:
        search_results = "Không tìm thấy sản phẩm phù hợp!"
    logger.info("___product retrieval completed...")
    return {"retrieved_products": search_results[:5]}
    

builder = StateGraph(RAGState)

builder.add_node(generates_keyword)
builder.add_node(hybrid_search)
builder.add_node(rerank)
builder.add_node(respond)

builder.add_edge(START, "generates_keyword")
builder.add_edge("generates_keyword", "hybrid_search")
builder.add_edge("hybrid_search", "rerank")
builder.add_edge("rerank", "respond")
builder.add_edge("respond", END)

rag_graph = builder.compile()