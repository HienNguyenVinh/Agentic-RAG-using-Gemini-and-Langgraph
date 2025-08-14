from dataclasses import dataclass, field
from typing import List, Optional
from langchain_core.documents import Document


@dataclass(kw_only=True)
class RAGState():
    user_query: Optional[str]

    vector_search_query: Optional[str] = None
    fts_keyword: Optional[str] = None
    
    products_by_vector_search: List[Document] = field(default_factory=list)
    products_by_fts: List[Document] = field(default_factory=list)

    found: Optional[bool] = False

    retrieved_products: List[Document] = field(default_factory=list)