from .repository import Repository
from ..models import SQLTodo


class SQLTodoRepository(Repository):
    DEFAULT_NOT_FOUND_MESSAGE = "The requested todo was not found"
    base_class = SQLTodo

    def _apply_query_params(self, query, query_params):
        query = super()._apply_query_params(query, query_params)

        title_query_param = self.get_query_param("title", query_params)

        if title_query_param is not None:
            query = query.where(SQLTodo.title == title_query_param)

        return query
