import logging
from abc import ABC
from typing import Callable

from sqlalchemy import select, insert, update, delete
from werkzeug.datastructures import MultiDict

from src.domain import ApiException, ITEMIZE, ITEMIZED, PAGE, PER_PAGE, \
    DEFAULT_PAGE_VALUE, DEFAULT_PER_PAGE_VALUE
from src.infrastructure.databases.sql_alchemy import database

logger = logging.getLogger(__name__)


class Repository(ABC):
    base_class: Callable
    DEFAULT_NOT_FOUND_MESSAGE = "The requested resource was not found"
    DEFAULT_PER_PAGE = DEFAULT_PER_PAGE_VALUE
    DEFAULT_PAGE = DEFAULT_PAGE_VALUE

    async def create(self, data):
        try:
            query = insert(self.base_class).values(**data)
            created_object_id = await database.execute(query)
            return await self.get(created_object_id)
        except Exception as e:
            logger.error(e)
            raise ApiException("Error creating object")

    async def update(self, object_id, data):
        try:
            query = update(self.base_class).where(self.base_class.id == object_id).values(**data)
            await database.execute(query)
            return await self.get(object_id)
        except Exception as e:
            logger.error(e)
            raise ApiException("Error updating object")

    async def delete(self, object_id):
        try:
            query = delete(self.base_class).where(self.base_class.id == object_id)
            await database.execute(query)
        except Exception as e:
            logger.error(e)
            raise ApiException("Error deleting object")

    async def delete_all(self, query_params):
        if query_params is None:
            raise ApiException("No parameters are required")

        try:
            query = delete(self.base_class)
            query = self.apply_query_params(query, query_params)
            await database.execute(query)
        except Exception as e:
            logger.error(e)
            raise ApiException("Error deleting all objects")

    async def get_all(self, query_params=None):
        try:
            query = select(self.base_class)
            query = self.apply_query_params(query, query_params)

            if self.is_itemized(query_params):
                return await self.create_itemization(query)

            return await self.create_pagination(query_params, query)
        except Exception as e:
            logger.error(e)
            raise ApiException("Error getting all objects")

    async def get(self, object_id):
        query = select(self.base_class).where(self.base_class.id == object_id)
        result = await database.fetch_one(query)
        if not result:
            raise ApiException(self.DEFAULT_NOT_FOUND_MESSAGE, 404)
        return result

    def _apply_query_params(self, query, query_params):
        return query

    def apply_query_params(self, query, query_params):
        if query_params is not None:
            query = self._apply_query_params(query, query_params)
        return query

    async def exists(self, query_params):
        try:
            query = select(self.base_class)
            query = self.apply_query_params(query, query_params)
            result = await database.fetch_one(query)
            return result is not None
        except Exception as e:
            logger.error(e)
            raise ApiException("Error checking if object exists")

    async def find(self, query_params):
        try:
            query = select(self.base_class)
            query = self.apply_query_params(query, query_params)
            result = await database.fetch_one(query)
            if not result:
                raise ApiException(self.DEFAULT_NOT_FOUND_MESSAGE, 404)
            return result
        except Exception as e:
            logger.error(e)
            raise ApiException("Error finding object")

    async def count(self, query_params=None):
        try:
            query = select([self.base_class.id])
            query = self.apply_query_params(query, query_params)
            return await database.count(query)
        except Exception as e:
            logger.error(e)
            raise ApiException("Error counting objects")

    def normalize_query_param(self, value):
        if len(value) == 1 and value[0].lower() in ["true", "false"]:
            if value[0].lower() == "true":
                return True
            return False
        return value if len(value) > 1 else value[0]

    def is_query_param_present(self, key, params, throw_exception=False):
        query_params = self.normalize_query(params)
        if key not in query_params:
            if not throw_exception:
                return False
            raise ApiException(f"{key} is not specified")
        else:
            return True

    def normalize_query(self, params):
        if isinstance(params, MultiDict):
            params = params.to_dict(flat=False)
        return {k: self.normalize_query_param(v) for k, v in params.items()}

    def get_query_param(self, key: str, params, default=None, many=False):
        boolean_array = ["true", "false"]
        if params is None:
            return default
        if not isinstance(params, dict):
            params = self.normalize_query(params)
        selection = params.get(key, default)
        if not isinstance(selection, list):
            if selection is None:
                selection = []
            else:
                selection = [selection]
        new_selection = []
        for index, selected in enumerate(selection):
            if isinstance(selected, str) and selected.lower() in boolean_array:
                new_selection.append(selected.lower() == "true")
            else:
                new_selection.append(selected)
        if not many:
            if len(new_selection) == 0:
                return None
            return new_selection[0]
        return new_selection

    def is_itemized(self, query_params):
        if query_params is None:
            return False
        itemized = self.get_query_param(ITEMIZED, query_params, False)
        itemize = self.get_query_param(ITEMIZE, query_params, False)
        return itemized or itemize

    async def create_pagination(self, query_params, query):
        page = self.get_query_param(PAGE, query_params, self.DEFAULT_PAGE)
        per_page = self.get_query_param(PER_PAGE, query_params, self.DEFAULT_PER_PAGE)

        try:
            page = int(page)
        except ValueError:
            page = self.DEFAULT_PAGE

        try:
            per_page = int(per_page)
        except ValueError:
            per_page = self.DEFAULT_PER_PAGE

        offset = (page - 1) * per_page
        query = query.limit(per_page).offset(offset)
        items = await database.fetch_all(query)
        total = await self.count(query_params)

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'items': items,
        }

    async def create_itemization(self, query):
        items = await database.fetch_all(query)
        return {
            'items': items
        }
