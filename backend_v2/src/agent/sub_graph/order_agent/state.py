from dataclasses import dataclass, field
from typing import Optional, List, Annotated

from langchain_core.messages import BaseMessage

@dataclass(kw_only=True)
class InputState:
    user_id: Optional[int]
    product_id: Optional[int]
    quantity: Optional[int]

@dataclass(kw_only=True)
class OrderAgentState(InputState):
    total_amount: Optional[float] = 0.0
    order_id: Optional[int] = None

    stock_available: Optional[int] = None
    order_created: Optional[bool] = False
    stock_updated: Optional[bool] = False

    order_state: Optional[str] = None
