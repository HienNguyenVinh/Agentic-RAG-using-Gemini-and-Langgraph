from langchain_core.documents import Document

from db_helper.product_services import get_product_by_name, get_related_product_by_vector, get_related_product_by_word
from .embedding import GeminiEmbedding

async def vector_search(query: str, k: int=5) -> list[Document]:
    """Tìm kiếm sản phẩm dựa trên query của người dùng.

    Args:
        query (str): truy vấn của người dùng đã được rút gọn.
        k (int): số sản phẩm trả về.

    Returns:
        str: Danh sách thông tin sản phẩm nếu tìm thấy.
    """
    embedding = GeminiEmbedding()
    print(query)
    query_vector = embedding.get_embedding(query)
    results = get_related_product_by_vector(query_vector, k=5)
    related_products: list[Document] = []
    
    if results:
        for item in results:
            product = Document(
                page_content=item.get('description'),
                metadata={
                    "name": item.get('name'),
                    "author": item.get('author'),
                    "category": item.get('category'),
                    "highlight": item.get('high_light'),
                    "price": item.get('price') if item.get('price') else "Liên hệ đế trao đổi giá chi tiết.",
                    "score": item.get('distance'),
                }
            )

            related_products.append(product)

    # print(products)
    return related_products

async def full_text_search(keyword: str, k: int=5) -> list[Document]:
    """Tìm kiếm sản phẩm dựa trên keyword trong truy vấn của người dùng.

    Args:
        keyword (str): keyword đã được trích xuất từ truy vấn của người dùng đã được rút gọn.
        k (int): Số sản phẩm trả về

    Returns:
        str: Danh sách thông tin sản phẩm nếu tìm thấy.
    """
    related_products = get_related_product_by_word(keyword, k)
    
    products: list[Document]= []

    if related_products:
        for item in related_products:
            product = Document(
                page_content=item.get('description'),
                metadata={
                    "name": item.get('name'),
                    "author": item.get('author'),
                    "category": item.get('category'),
                    "highlight": item.get('high_light'),
                    "price": item.get('price') if item.get('price') else "Liên hệ đế trao đổi giá chi tiết.",
                    "score": item.get('rank'),
                }
            )
            
            products.append(product)

    # print(products)
    return products
    
def product_search_by_name(product_name: str) -> str:
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