from typing import Annotated, Dict, Optional, Any

from db_helper.orders_services import create_new_order
from db_helper.product_services import check_product_stock, update_product_stock, get_product_by_id

async def create_order(user_id: int, product_id: int, quantity: int) -> Dict[str, Any]:
    """Tạo đơn hàng mới.

    Args:
        user_id (int): Mã người dùng.
        product_id (int): Mã sản phẩm.
        quantity (int): Số lượng sản phẩm.
        total_amount (float): Thành tiền.
        
    Returns:
        order_id và total_amount
    """
    product = get_product_by_id(product_id)

    if product:
        total_amount = product['price'] * quantity
        
        order_id = create_new_order(user_id, product_id, quantity, total_amount)

        return {
            "order_id": order_id,
            "total_amount": total_amount,
            "order_created": True,
        }
    else:
        return {
            "order_created": False
        }

async def check_stock(product_id: int) -> Dict[str, Optional[int]]:
    """Kiểm tra số lượng hàng trong kho.

    Args:
        product_id (int): Mã sản phẩm.
        
    Returns:
        Số lượng sản phẩm trong kho
    """
    available = check_product_stock(product_id)

    return {
        "stock_available": available,
    }

async def update_stock(product_id: int, quantity: int) -> Dict[str, bool]:
    """Cập nhật số lượng sản phẩm còn lại trong kho.

    Args:
        product_id (int): Mã sản phẩm.
        quantity (int): Số lượng sản phẩm.
        
    Returns:
        Cập nhật thành công hay không.
    """
    updated = update_product_stock(product_id, quantity)

    return {
        "stock_updated": True if updated else False,
    }