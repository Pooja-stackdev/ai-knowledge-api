# app/api/routes/roles.py

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies.authorization import require_permission
from app.api.dependencies.role import get_role_service
from app.schemas.role import RoleCreateRequest, RoleResponse, RoleUpdateRequest
from app.services.auth.role_service import RoleService

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=list[RoleResponse],
    dependencies=[
        Depends(require_permission("role.read"))
    ],
)
def get_roles(
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    return service.get_roles()


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("role.create"))
    ],
)
def create_role(
    request: RoleCreateRequest,
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    return service.create_role(
        name=request.name,
        description=request.description,
        permission_ids=request.permission_ids,
    )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[
        Depends(require_permission("role.update"))
    ],
)
def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    return service.update_role(
        role_id=role_id,
        name=request.name,
        description=request.description,
        permission_ids=request.permission_ids,
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_permission("role.delete"))
    ],
)
def delete_role(
    role_id: int,
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
) -> None:
    service.delete_role(role_id)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[
        Depends(require_permission("role.read"))
    ],
)
def get_role(
    role_id: int,
    service: Annotated[
        RoleService,
        Depends(get_role_service),
    ],
):
    return service.get_role(role_id)