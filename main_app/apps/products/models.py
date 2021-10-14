import uuid
from fastapi import Request, FastAPI
from pydantic import BaseModel, UUID4, Field, validator
from pymongo import ReturnDocument
#from bson.objectid import ObjectId

from typing import Optional, List
from .product_exceptions import ProductAlreadyExist, ProductNotExist, CategoryAlreadyExist, CategoryNotExist


# Category block 

class BaseProductCategory(BaseModel):
	id: Optional[UUID4] = Field(alias="_id")
	name: str = ""
	slug: str = ""

	class Config:
		allow_population_by_field_name = True

	def exist_get_db(self, categories_db):
		# try get category by id, if it is specified
		if self.id:
			category = categories_db.find_one(
				{"_id": self.id}
			)
			if not category:
				return False, None
			return True, BaseProductCategory(**category)
		# try find category by slug, if it is specified
		elif self.slug.__len__() > 0:
			category = categories_db.find_one(
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
	parent_id: UUID4 = None

class BaseCategoryUpdate(BaseModel):
	name: str
	slug: str
	description: str = None
	imgsrc: Optional[list] = []
	menu_order: int = 0
	parent_id: UUID4 = None

class BaseCategory(BaseModel):
	id: UUID4 = Field(default_factory = uuid.uuid4, alias="_id")
	name: str
	slug: str
	description: str = None
	imgsrc: Optional[list] = []
	menu_order: int = 0
	parent_id: UUID4 = None

	def insert_db(self, categories_db):
		category_exist = categories_db.find_one(
			{"slug": self.slug}
		)
		if category_exist:
			raise CategoryAlreadyExist
		result = categories_db.insert_one(
			self.dict(by_alias=True)
		)
	def delete_db(self, categories_db):
		categories_db.delete_one(
			{"_id": self.id}
		)
	def update_db(self, categories_db):
		updated_category = categories_db.find_one_and_update(
			{"_id": self.id},
			{"$set": self.dict(by_alias=True)},
			return_document=ReturnDocument.AFTER
		)
		if updated_category:
			category = BaseCategory(**updated_category)
			return category
		return None

# Product block

class BaseProductUpdate(BaseModel):
	name: str
	description: str = None
	imgsrc: Optional[list] = []
	price: int = None
	sale_price: int = None
	weight: Optional[str] = None
	categories: List[BaseProductCategory] = []

class BaseProductCreate(BaseModel):
	name: str
	description: str = None
	imgsrc: Optional[list] = []
	price: int = None
	sale_price: int = None
	weight: Optional[str] = None
	categories: List[BaseProductCategory] = []

class BaseProduct(BaseModel):
#	id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
	id: UUID4 = Field(default_factory = uuid.uuid4, alias="_id")
	name: str
	description: str = None
	imgsrc: Optional[list] = []
	price: int = None
	sale_price: int = None
	weight: Optional[str] = None
	categories: List[BaseProductCategory] = []


	def check_categories(self, categories_db):
		for indx, category in enumerate(self.categories, start = 0):
			print('category is', category)
			is_exist, cat = category.exist_get_db(categories_db)
			print('cat is', cat)
			if is_exist:
				self.categories[indx] = cat
			else:
				self.categories.remove(category)

	def insert_db(self, app: FastAPI):
		product_exist = app.products_db.find_one(
			{"_id": self.id}
		)
		if product_exist:
			raise ProductAlreadyExist
		self.check_categories(app.categories_db)

		result = app.products_db.insert_one(
			self.dict(by_alias=True)
		)
		print('insert result is', result)

	def delete_db(self, products_db):
		products_db.delete_one(
			{"_id": self.id}
		)
	def update_db(self, request: Request):
		self.check_categories(request.app.categories_db)
#		print('self dict is', self.dict())
		updated_product = request.app.products_db.find_one_and_update(
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
#		allow_population_by_field_name = True
#		arbitrary_types_allowed = True
#		json_encoders = {ObjectId: str}
		schema_extra = {
			"example": {
				"name": "some product name is here",
			}
		}

