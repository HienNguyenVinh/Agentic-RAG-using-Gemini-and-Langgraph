from langchain_core.messages import AnyMessage
from langchain_core.documents import Document
from langgraph.graph import add_messages
from dataclasses import dataclass, field
from typing import Annotated, List, Optional, Dict

@dataclass(kw_only=True)
class InputState:
    messages: Annotated[List[AnyMessage], add_messages]
    current_chat: List[Dict[str, str]] = field(default_factory=list)

@dataclass(kw_only=True)
class AgentState(InputState):
    router: Optional[str] = None
    user_query: Optional[str] = None
    retrieved_products: List[str] = field(default_factory=list)

    respond: Optional[str] = None
    order_state: Optional[str] = None

    lack_of_order_info: List[str] = field(default_factory=list)
    
    user_name: Optional[int] = None
    user_phone: Optional[str] = None
    user_address: Optional[str] = None
    current_product_id: Optional[int] = None
    current_product_quantity: Optional[int] = None