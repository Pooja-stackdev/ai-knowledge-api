from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies.authentication import CurrentUser
from app.api.dependencies.authorization import require_permission
from app.api.dependencies.user import UserServiceDependency
from app.database.models.user import User
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    request: CreateUserRequest,
    current_user: Annotated[User, Depends(require_permission("user.create"))],
    service: UserServiceDependency,
):
    return service.create_user(
        email=request.email,
        password=request.password,
        role_ids=request.role_ids,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[
        Depends(require_permission("user.read")),
    ],
)
def get_user(
    user_id: int,
    current_user: CurrentUser,
    service: UserServiceDependency,
):
    return service.get_user(user_id)

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[
        Depends(require_permission("user.update")),
    ],
)
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: CurrentUser,
    service: UserServiceDependency,
):
    return service.update_user(
        user_id=user_id,
        email=request.email,
        role_ids=request.role_ids,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_permission("user.delete")),
    ],
)
def delete_user(
    user_id: int,
    current_user: CurrentUser,
    service: UserServiceDependency,
):
    service.delete_user(user_id)


