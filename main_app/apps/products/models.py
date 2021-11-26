import uuid
from fastapi import Request, FastAPI
from pydantic import BaseModel, UUID4, Field, validator
from pymongo import ReturnDocument
#from bson.objectid import ObjectId
from database.main_db import db_provider

from typing import Optional, List
from .product_exceptions import ProductAlreadyExist, ProductNotExist, CategoryAlreadyExist, CategoryNotExist


# Category block 

class BaseProductCategory(BaseModel):
    id: Optional[UUID4] = Field(alias="_id")
    name: str = ""
    slug: str = ""

    class Config:
        allow_population_by_field_name = True

    def exist_get_db(self):
        # try get category by id, if it is specified
        if self.id:
            category = db_provider.categories_db.find_one(
                {"_id": self.id}
            )
            if not category:
                return False, None
            return True, BaseProductCategory(**category)
        # try find category by slug, if it is specified
        elif self.slug.__len__() > 0:
            category = db_provider.categories_db.find_one(
                {"slug": self.slug}
            )
            if not category:
                return False, None
            print('category is', category)
            return True, BaseProductCategory(**category)
        return False, None


class BaseCategoryCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    imgsrc: Optional[list] = []
    menu_order: int = 0
    parent_id: Optional[UUID4]

    def check_exists_slug(self):
        category_exists_dict = db_provider.categories_db.find_one(
            {"slug": self.slug}
        )
        if category_exists_dict:
            return True, BaseCategory(**category_exists_dict)
        return False, None

class BaseCategoryUpdate(BaseModel):
    name: str
    slug: str
    description: Optional[str]
    imgsrc: Optional[list] = []
    menu_order: int = 0
    parent_id: Optional[UUID4]

    def check_exists_slug(self):
        category_dict = db_provider.categories_db.find_one(
            {"slug": self.slug}
        )
        if category_dict:
            return True, BaseCategory(**category_dict)
        return False, None

class BaseCategory(BaseModel):
    id: UUID4 = Field(default_factory = uuid.uuid4, alias="_id")
    name: str
    slug: str
    description: Optional[str]
    imgsrc: Optional[list] = []
    menu_order: int = 0
    parent_id: Optional[UUID4]

    def insert_db(self):
        category_exist = db_provider.categories_db.find_one(
            {"slug": self.slug}
        )
        if category_exist:
            raise CategoryAlreadyExist
        db_provider.categories_db.insert_one(
            self.dict(by_alias=True)
        )
    def delete_db(self):
        db_provider.categories_db.delete_one(
            {"_id": self.id}
        )
    def update_db(self):
        updated_category = db_provider.categories_db.find_one_and_update(
            {"_id": self.id},
            {"$set": self.dict(by_alias=True)},
            return_document=ReturnDocument.AFTER
        )
        print('udated category is', updated_category)
        if updated_category:
            category = BaseCategory(**updated_category)
            return category
        return None 

# Product block
class BaseProductUpdate(BaseModel):
    name: str
    description: Optional[str]
    imgsrc: Optional[list] = []
    price: Optional[int]
    sale_price: Optional[int]
    weight: Optional[str] = None
    categories: List[BaseProductCategory] = []

class BaseProductCreate(BaseModel):
    name: str
    description: Optional[str]
    imgsrc: Optional[list] = []
    price: int
    sale_price: Optional[int]
    weight: Optional[str]
    categories: List[BaseProductCategory] = []


class BaseProduct(BaseModel):
#   id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    id: UUID4 = Field(default_factory = uuid.uuid4, alias="_id")
    slug: str = ""
    name: str
    description: Optional[str]
    imgsrc: Optional[list] = []
    price: int
    sale_price: Optional[int]
    weight: Optional[str]
    categories: Optional[List[BaseProductCategory]] = []

    def get_price(self):
        if self.sale_price:
            return self.sale_price
        return self.price

    def check_categories(self):
        if not self.categories:
            return
        for indx, category in enumerate(self.categories, start = 0):
            print('category is', category)
            is_exist, cat = category.exist_get_db()
            print('cat is', cat)
            if is_exist and cat:
                self.categories[indx] = cat
            else:
                self.categories.remove(category)

    def insert_db(self):
        product_exist = db_provider.products_db.find_one(
            {"_id": self.id}
        )
        if product_exist:
            raise ProductAlreadyExist
        self.check_categories()

        result = db_provider.products_db.insert_one(
            self.dict(by_alias=True)
        )
        print('insert result is', result)

    def check_exists_slug(self):
        product_exists_dict = db_provider.products_db.find_one(
            {"slug": self.slug}
        )
        if product_exists_dict:
            return True, BaseProduct(**product_exists_dict)
        return False, None

    def delete_db(self):
        db_provider.products_db.delete_one(
            {"_id": self.id}
        )
    def update_db(self):
        self.check_categories()
#       print('self dict is', self.dict())
        updated_product = db_provider.products_db.find_one_and_update(
            {"_id": self.id},
            {"$set": self.dict(by_alias=True)},
            return_document=ReturnDocument.AFTER
        )
        print('updated product is', updated_product)
        if updated_product:
            product = BaseProduct(**updated_product)
            return product
        return None
#
    class Config:
#       allow_population_by_field_name = True
#       arbitrary_types_allowed = True
#       json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "some product name is here",
            }
        }

