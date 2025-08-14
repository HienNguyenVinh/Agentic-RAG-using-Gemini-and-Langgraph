# Agentic RAG using Gemini and Langgraph

A full-stack web application demonstrating a Retrieval-Augmented Generation (RAG) chat interface and a basic shopping/cart feature.
Frontend: React. Backend: FastAPI. LLM: Google Gemini. Two backend flavors shown below:

* **Backend V1** — direct google-genai SDK + FastAPI (existing).
* **Backend V2** — **Langgraph** orchestration for node/graph-based agents (recommended for complex flows & stateful agents).

---

# ✨ Features

* Interactive real-time chat UI with streaming AI responses.
* RAG pipeline (pgvector + PostgreSQL FTS + reranking).
* Function calling / structured extraction (e.g., extract order info).
* Hybrid search: vector + full-text.
* Shopping cart & order flow (create order, confirm, show status).
* Two backend architectures included: google-genai SDK (V1) and Langgraph graph orchestration (V2).

---

# 🏛️ Backend V1 architecture (google-genai sdk)

* A standard FastAPI app that:

  * Receives chat requests.
  * Runs RAG retrieval (pgvector + FTS).
  * Calls google-genai model (streaming via SDK).
  * Handles order creation via `order_graph` service (sync/async).
* Good for simple pipelines and direct control of prompts and streaming.

![Backend V1 architecture](https://github.com/user-attachments/assets/5ace76d2-7315-4763-8d85-abea14d44ae5)

---

# 🧭 Backend V2 architecture (langgraph)

**Overview**

Backend V2 replaces monolithic controller code with a *graph of nodes* (Langgraph). Each node is a small unit (determine\_agent, rag, ask\_for\_order\_info, extract\_order\_info, create\_order, response...) and the graph runtime manages state merging, branching, retries and checkpointing.

![Backend V2 architecture](backend_v2/static/graph.png)

**Advantages**

* Clear separation of concerns — each step is testable.
* Built-in state merging: nodes return small dicts and the framework merges them into `state`.
* Easy to add validation/conditional branches (e.g., check → ask → extract → create).
* Checkpointing and replay for debugging.
* Good for multi-turn, multi-modal flows and for orchestrating external services.

**Key components in V2**

* `AgentState` dataclass — hold messages, router, retrieved\_products, order fields (all optional defaults).
* Router node — classifies into `order`, `product_infomation`, or `chitchat`.
* `rag_graph` — a subgraph or callable that runs retrieval, returns `retrieved_products`.
* `extract_order_info` — uses `with_structured_output(...)` to reliably parse user replies into `user_id`, `product_id`, `quantity`.
* `create_order` — calls order microservice or DB to persist order and returns `order_state`.
* `response` node — chooses one of 3 specialized prompts (rag\_response, order\_response, chitchat\_response) based on `state.router`, formats the answer and saves it to session history.

**State & Session**

* Chat histories are stored per session (`InMemoryChatMessageHistory` by default). Use `session_id` in `config` to map to histories.
* All fields that nodes may add should exist on the state schema as `Optional[...]` or have defaults — this avoids serialization errors.

---

# 📋 Prerequisites

* Node.js & npm/yarn (frontend).
* Python 3.9+ (backend).
* PostgreSQL with `pgvector` extension for semantic search.
* Google Gemini API key (or other LLM credentials).
* Git.

---

# ⚙️ Getting Started (both backends)

## Clone

```bash
git clone https://github.com/HienNguyenVinh/agentic_rag_using_gemini.git
cd agentic_rag_using_gemini
```

## Backend (common)

```bash
cd backend

# create venv
python -m venv .venv
# activate:
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in `backend/`:

```
DATABASE_URL=postgresql://user:password@host:port/dbname
GEMINI_API_KEY=your_gemini_key
MODEL_NAME=gemini-2.0-flash
# Additional vars for Langgraph variant (if used)
# LANGGRAPH_ENABLED=true
```

Run DB init (if provided):

```bash
python Database/init_db.py
```

---

## Frontend

```bash
cd frontend
npm install
npm start
# or: yarn install && yarn start
```

---

# ▶️ Running Backend V1 (google-genai SDK)

Default: FastAPI app.

```bash
cd backend
# run server (example using uvicorn)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

* `POST /api/chat` — non-streaming chat
* `POST /api/chat/stream` — streaming chat (SSE)
* `GET /api/cart?user_id=1` — fetch cart

---

# ▶️ Running Backend V2 (Langgraph)

V2 includes additional dependencies (langgraph, langchain-google-genai wrappers). Recommended flow below.

### 1. Install langgraph extras

```bash
pip install -r requirements-langgraph.txt
```

### 2. Ensure state dataclasses are optional/defaulted

Make sure `AgentState` looks like:

```python
@dataclass(kw_only=True)
class AgentState(InputState):
    router: Optional[str] = None
    user_query: Optional[str] = None
    retrieved_products: List[Document] = field(default_factory=list)
    order_state: Optional[str] = None
    lack_of_order_info: List[str] = field(default_factory=list)
    user_id: Optional[int] = None
    current_product_id: Optional[int] = None
    current_product_quantity: Optional[int] = None
```

### 3. Start the graph (example)

There are two common ways to run the Langgraph-based backend:

**a) As part of FastAPI** — the graph runs inside request handlers (recommended for HTTP-driven UX). Call `graph.astream` / `graph.ainvoke` from your FastAPI endpoint handlers.

**b) As a standalone graph worker** — useful for long-running flows / streaming. Example `main_graph_runner.py`:

```python
import asyncio
from agent.graph import graph  # compiled graph

async def run_once(user_input):
    async for event in graph.astream(
        {"messages": [{"role":"user","content": user_input}]},
        config={"configurable": {"session_id": "1"}},
        stream_mode="values",
    ):
        # event is a dict with messages and state changes
        print(event["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(run_once("I want to buy Norwegian Wood by Haruki Murakami"))
```

Run:

```bash
python main_graph_runner.py
```

### 4. FastAPI integration snippet

Inside your FastAPI endpoint:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/chat/stream")
async def chat_stream(req: Request):
    user_input = await req.json()
    async for event in graph.astream(
        {"messages":[{"role":"user","content": user_input["text"]}]},
        config={"configurable":{"session_id": user_input.get("session_id","1")}},
        stream_mode="values"
    ):
        # translate event into SSE or chunked responses
        yield event
```

### 5. Prompts & Structured Output

* Use `model.with_structured_output(SomeDataclass).ainvoke(...)` for reliable parsing (OrderInfo, Router).
* **Important:** provide docstrings on dataclass schemas used in `with_structured_output(...)` — some wrappers require docstrings to convert schema to tool declarations.
* Keep prompts short and pass only sanitized/limited data (e.g., top-3 retrieved products).

---

# 🔧 Implementation notes & gotchas

* **Never return coroutine objects in `messages`** — always `await` your `.ainvoke(...)` calls before returning model outputs. Storing coroutine objects into `state.messages` causes `NotImplementedError: Unsupported message type: <class 'coroutine'>`.
* **State schema must accept keys nodes return** — make fields `Optional[...]` or provide defaults. Otherwise you’ll get `TypeError: __init__() got an unexpected keyword argument 'router'`.
* **Check `check_order_info` logic** — use `is None` checks to detect missing fields.
* **Session handling** — store chat history per `session_id` and use locks if multi-threaded.
* **Limit prompt size** — pass only the top 3 products from RAG, not the full corpus.
* **Structured extraction** — prefer structured outputs (dataclasses) rather than regex, but always validate parsed values (quantity > 0, product\_id exists).
* **Vector dimension mismatch**: ensure your embedding models/embeddings used at index time and query time have same dimension (error: `different vector dimensions 768 and 3072`).

---

# 🌐 API Endpoints (Backend V2 — Langgraph)

Essential endpoints that your frontend can call (FastAPI wrappers around graph):

* `POST /api/graph/chat` — run graph for a single user message (non-streaming).
* `POST /api/graph/chat/stream` — streaming SSE wrapper around `graph.astream`.
* `GET /api/cart` — fetch current cart for user.
* `POST /api/order` — direct order creation (if you want an endpoint bypassing graph).

(Implement these as simple FastAPI wrappers that call into `graph.ainvoke` / `graph.astream`.)

---

# 🔁 Migrating from V1 → V2 (practical tips)

1. Start by reusing your retrieval and order services as callables used by Langgraph nodes.
2. Move prompt logic into node-specific prompts (rag\_response, order\_response, chitchat\_response).
3. Add small nodes first: `determine_agent` → `rag` → `response`. Then add order flow nodes.
4. Add checkpointing (MemorySaver) only after flow is stable.
5. Write unit tests for nodes (e.g., `extract_order_info` should parse many user phrasings).

---

# Demo

YouTube demo: [https://youtu.be/ip9\_BZqYyn8](https://youtu.be/ip9_BZqYyn8)

---
