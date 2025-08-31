import logging

from dependency_injector.wiring import inject, Provide
from flask import Blueprint, request

from src.api.middleware import post_data_required
from src.api.responses import create_response
from src.api.schemas import TodoSchema
from src.dependency_container import DependencyContainer

logger = logging.getLogger(__name__)
blueprint = Blueprint('todo', __name__)


@blueprint.route('/todo', methods=['POST'])
@post_data_required
@inject
async def create_todo(
    json_data,
    todo_service=Provide[DependencyContainer.todo_service]
):
    validated_data = TodoSchema().load(json_data)
    todo = await todo_service.create(validated_data)
    return create_response(todo, TodoSchema, status_code=201)

@blueprint.route('/todo/<int:id>', methods=['PATCH'])
@post_data_required
@inject
async def update_todo(
    json_data,
    id,
    todo_service=Provide[DependencyContainer.todo_service]
):
    validated_data = TodoSchema().load(json_data)
    todo = await todo_service.update(id, validated_data)
    return create_response(todo, TodoSchema)


@blueprint.route('/todo', methods=['GET'])
@inject
async def get_todo(
    todo_service=Provide[DependencyContainer.todo_service]
):
    query_params = request.args.to_dict()
    todos = await todo_service.get_all(query_params)
    return create_response(todos, TodoSchema)


@blueprint.route('/todo/<int:id>', methods=['DELETE'])
@inject
async def delete_todo(
    id,
    todo_service=Provide[DependencyContainer.todo_service]
):
    await todo_service.delete(id)
    return create_response({}, TodoSchema, status_code=204)


@blueprint.route('/todo/<int:id>', methods=['GET'])
@inject
async def retrieve_todo(
    id,
    todo_service=Provide[DependencyContainer.todo_service]
):
    todo = await todo_service.get(id)
    return create_response(todo, TodoSchema)