from langgraph.graph import StateGraph, START, END
from typing import Literal, List, Any, Dict

from .tools import check_stock, create_order, update_stock
from .state import InputState, OrderAgentState

async def check_stock_node(state: OrderAgentState) -> Dict[str, Any]:
    """
    Check the available stock for the product in the current state.

    Calls the external `check_stock(product_id)` service and returns its result.
    Expects `state.product_id` to be set. The returned dict should include
    stock-related fields (e.g. `stock_available`) that later nodes or routers will use.

    Returns:
        A dict containing the stock check result from the service.
    """

    result = await check_stock(state.product_id)
    return result

async def create_order_node(state: OrderAgentState) -> Dict[str, Any]:
    """
    Create an order using the current state's user and product information.

    Calls the external `create_order(user_id, product_id, quantity)` service.
    Expects `state.user_id`, `state.product_id`, and `state.quantity` to be set.
    The returned dict should include order outcome fields such as `order_created` (bool),
    `order_id`, and `total_amount`.

    Returns:
        A dict containing the order creation result from the service.
    """

    result = await create_order(state.user_id, state.product_id, state.quantity)
    return result

async def update_stock_node(state: OrderAgentState) -> Dict[str, Any]:
    """
    Update the product stock after a successful order.

    Calls the external `update_stock(product_id, quantity)` service to decrement
    (or otherwise adjust) inventory based on the order quantity.
    Expects `state.product_id` and `state.quantity` to be set.

    Returns:
        A dict containing the stock update result from the service.
    """

    result = await update_stock(state.product_id, state.quantity)
    return result

def router_check(state: OrderAgentState) -> str:
    """
    Decide whether to proceed with order creation or respond to the user.

    Logic:
      - If `state.stock_available >= state.quantity` returns "create_order".
      - Otherwise returns "respond".

    Returns:
        The name of the next node as a string: "create_order" or "respond".
    """

    if state.stock_available >= state.quantity:
        return "create_order"
    else:
        return "respond"
    
def router_create(state: OrderAgentState) -> str:
    """
    Decide next step after attempting to create an order.

    Logic:
      - If `state.order_created` is truthy, return "update_stock".
      - Otherwise return "respond".

    Returns:
        The name of the next node as a string: "update_stock" or "respond".
    """

    if state.order_created:
        return "update_stock"
    else:
        return "respond"
    

def respond_node(state: OrderAgentState) -> Dict[str, List[str]]:
    """
    Build a human-readable order summary from the current state.

    Reads fields such as `user_id`, `product_id`, `quantity`, `total_amount`,
    `order_id`, and `order_created` from the state and formats a concise summary
    string returned under the key `order_state`.

    Returns:
        A dict with a single key 'order_state' mapping to the formatted summary string.
    """

    summary = (
        f"Order Summary:\n"
        f"• user_id: {state.user_id}\n"
        f"• product_id: {state.product_id}\n"
        f"• quantity: {state.quantity}\n"
        f"• total_amount: {state.total_amount}\n"
        f"• order_id: {state.order_id}\n"
        f"• status: {state.order_created}\n"
    )

    return {"order_state": summary}


builder = StateGraph(OrderAgentState, input=InputState)

builder.add_node(check_stock_node)
builder.add_node(create_order_node)
builder.add_node(update_stock_node)
builder.add_node(respond_node)

builder.add_edge(START, "check_stock_node")
builder.add_edge("update_stock_node", "respond_node")
builder.add_edge("respond_node", END)

builder.add_conditional_edges(
    "check_stock_node",
    router_check,
    {
        "create_order": "create_order_node",
        "respond": "respond_node"
    }
)

builder.add_conditional_edges(
    "create_order_node",
    router_create,
    {
        "update_stock": "update_stock_node",
        "respond": "respond_node"
    }
)

order_graph = builder.compile()