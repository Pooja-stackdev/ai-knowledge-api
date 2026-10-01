# app/api/routes/permissions.py
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.authorization import require_permission
from app.api.dependencies.permission import get_permission_service
from app.schemas.permission import PermissionResponse
from app.services.auth.permission_service import PermissionService

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=list[PermissionResponse],
    dependencies=[
        Depends(require_permission("role.read"))
    ],
)
def get_permissions(
    service: Annotated[
        PermissionService,
        Depends(get_permission_service),
    ],
):
    return service.get_permissions()