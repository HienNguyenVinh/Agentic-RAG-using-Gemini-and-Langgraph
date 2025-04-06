from typing import Optional, Dict
from decimal import Decimal
from Database.product_services import check_product_stock, update_product_stock, get_product_by_name, hybrid_search
from Database.orders_services import create_new_order
from RagCore.Embeddings import GeminiEmbedding


def related_products_search(keyword: str) -> str:
    """Tìm kiếm sản phẩm dựa trên keyword và query của người dùng.

    Args:
        keyword (str): Từ khóa tìm kiếm bằng tiếng Việt dựa trên truy vấn của người dùng.

    Returns:
        str: Danh sách thông tin sản phẩm nếu tìm thấy.
    """
    embedding = GeminiEmbedding()
    print(keyword)
    query_vector = embedding.get_embedding(keyword)
    # related_products = get_related_product_by_vector(query_vector)
    related_products = hybrid_search(keyword, query_vector)
    
    full_info = ""
    if related_products:
        for item in related_products:
            if item.get('name'):
                full_info += "###Tên: " + item.get('name') + "\n"
            if item.get('author'):
                full_info += "Tác giả: " + item.get('author') + "\n"
            if item.get('category'):
                full_info += "Thể loại" + item.get('category') + "\n"
            if item.get('high_light'):
                full_info += "Highlight: " + item.get('high_light') + "\n"
            if item.get('description'):
                full_info += "Mô tả" + item['description'] + "\n"
            if item.get('price'):
                full_info += f"\nGiá: {item.get('price')}" + " VND.\n"
            else:
                full_info += "Liên hệ đế trao đổi chi tiết."
    else:
        full_info = "Không tìm thấy sản phẩm nào!"

    # print(full_info)

    return full_info

    

def product_search(product_name: str) -> str:
    """Tìm kiếm sản phẩm dựa trên tên sản phẩm.

    Args:
        product_name (str): Tên sản phẩm cần tìm kiếm.

    Returns:
        Optional[Dict]: Thông tin sản phẩm nếu tìm thấy, None nếu không tìm thấy.
    """
    item = get_product_by_name(product_name=product_name)
    if item:
        full_info = ""
        if item.get('name'):
            full_info += item.get('name') + "\n"
        if item.get('id'):
            full_info += f"ID: {item.get('id')}\n"
        if item.get('author'):
            full_info += item.get('author') + "\n"
        if item.get('category'):
            full_info += item.get('category') + "\n"
        if item.get('high_light'):
            full_info += item.get('high_light') + "\n"
        if item['description']:
            full_info += item['description']
        if item['price']:
            full_info += f"\nGiá: {item['price']}" + " VND.\n"
        else:
            full_info += "Liên hệ đế trao đổi chi tiết."
        if item['stock_quantity']:
            full_info += f"Số lượng trong kho: {item['stock_quantity']}"

        return full_info
    else:
        return("Không tìm thấy sản phẩm nào! Hãy kiểm tra lại tên sản phẩm.")


def create_order(user_id: int, product_id: int, quantity: int, total_amount: float) -> str:
    """Tạo đơn hàng mới.

    Args:
        user_id (int): Mã người dùng.
        product_id (int): Mã sản phẩm.
        quantity (int): Số lượng sản phẩm.
        total_amount (float): Thành tiền.
        
    Returns:
        Trạng thái đơn hàng.
    """
    check_stock = check_product_stock(product_id, quantity)
    if check_stock:
        if create_new_order(user_id, product_id, quantity, total_amount):
            update_product_stock(product_id, quantity)
            return "Tạo đơn hàng thành công!"
        else:
            return "Có lỗi xảy ra. Tạo đơn hàng thất bại!"
    else:
        return "Số lượng trong kho không đủ!"
    
