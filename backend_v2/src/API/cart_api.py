from fastapi import APIRouter, HTTPException
from db_helper.orders_services import get_all_orders

router = APIRouter()

@router.get("/cart")
async def get_cart(user_id: int):
    try:
        orders = get_all_orders(user_id=user_id)
        if orders:
            return orders
        else:
            return "Fail to get orders!"
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail="Internal Server Error: " + str(e)
                            )