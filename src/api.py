from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto import OrganizationDetail
from application.protocols import OrganizationReadRepositoryProtocol
from infra.db import sessionmaker
from infra.repository import OrganizationReadRepository

app = FastAPI(title="Organization Directory API")

router = APIRouter(prefix="/organizations", tags=["Organizations"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


async def get_organization_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrganizationReadRepositoryProtocol:
    return OrganizationReadRepository(session)


@router.get(
    "",
    response_model=list[OrganizationDetail],
    summary="Поиск организаций",
    description=(
        "Поиск организаций по фильтрам с логикой AND. "
        "Фильтры name/building/activity ищутся как подстрока (ILIKE), "
        "phone — точное совпадение. "
        "Фильтр activity учитывает вложенные подкатегории (уровни 2 и 3)."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Список организаций (может быть пустым)",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Не задан ни один фильтр",
        },
    },
)
async def list_organizations(
    org_repo: Annotated[
        OrganizationReadRepositoryProtocol, Depends(get_organization_repo)
    ],
    name: str | None = Query(default=None),
    building: str | None = Query(default=None),
    phone: str | None = Query(default=None),
    activity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[OrganizationDetail]:
    if not any([name, building, phone, activity]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one filter must be provided",
        )

    return await org_repo.search(
        name=name,
        building=building,
        phone=phone,
        activity=activity,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{org_id}",
    response_model=OrganizationDetail,
    summary="Get organization by ID",
    description=(
        "Returns full information about an organization: "
        "its name, address, phone numbers and activity types."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Organization found",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Organization with the given ID does not exist",
        },
    },
)
async def get_organization_by_id(
    org_id: UUID,
    org_repo: Annotated[
        OrganizationReadRepositoryProtocol, Depends(get_organization_repo)
    ],
):
    organization = await org_repo.get_by_id(organization_id=org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


app.include_router(router)
