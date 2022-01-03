from database.main_db import db_provider

from .models import BaseProduct
from .models import BaseCategory
from .product_exceptions import ProductNotExist, CategoryNotExist

from pydantic import UUID4
from typing import List

def search_products_by_name(search_string):
    products_dict = db_provider.products_db.find(
        {
            "name": {
                "$regex": search_string
            }
        }
    ).limit(10)
    products = [BaseProduct(**product).dict() for product in products_dict]
    return products

def get_product_by_id(product_id: UUID4, silent: bool = False) -> BaseProduct:
    product = db_provider.products_db.find_one(
        {"_id": product_id}
    )
    if not product:
        if not silent:
            raise ProductNotExist
        raise 
    product = BaseProduct(**product)
    return product

def get_category_by_id(category_id: UUID4, silent: bool = False) -> BaseCategory:
    category = db_provider.categories_db.find_one(
        {"_id": category_id }
    )
    if not category:
        if not silent:
            raise CategoryNotExist
        raise
    else:
        category = BaseCategory(**category)
        return category

def get_category_products_by_id(category_id: UUID4) -> list:
    category_products_raw = db_provider.products_db.find(
        {"categories": {
            "$elemMatch": {
                "_id": category_id
            }
        }}
    )
    category_products = [BaseProduct(**product).dict() for product in category_products_raw]
    return category_products
