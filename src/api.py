import os
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto import GeoBBox, OrganizationDetail
from application.protocols import OrganizationReadRepositoryProtocol
from domain.entities import GeoPoint
from infra.db import sessionmaker
from infra.repository import OrganizationReadRepository

app = FastAPI(title="Organization Directory API")

API_SECURITY_KEY = os.getenv(
    "API_KEY",
    "defaultkey-123456789",
)
API_KEY_SCHEME = APIKeyHeader(name="X-API-Key")


def require_api_key(api_key: str | None = Security(API_KEY_SCHEME)) -> None:
    if api_key != API_SECURITY_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
    dependencies=[Depends(require_api_key)]
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


async def get_organization_read_repo(
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
        OrganizationReadRepositoryProtocol, Depends(get_organization_read_repo)
    ],
    name: str | None = Query(default=None),
    building: str | None = Query(default=None),
    phone: str | None = Query(default=None),
    activity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[OrganizationDetail]:
    """Возвращает список организаций, подходящих под фильтры."""
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
    summary="Карточка организации по идентификатору",
    description=(
        "Возвращает карточку организации: название, адрес, "
        "телефоны и виды деятельности."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Организация найдена",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Организация с таким ID не найдена",
        },
    },
)
async def get_organization_by_id(
    org_id: UUID,
    org_repo: Annotated[
        OrganizationReadRepositoryProtocol, Depends(get_organization_read_repo)
    ],
):
    """Возвращает организацию по её идентификатору."""
    organization = await org_repo.get_by_id(organization_id=org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


@router.get(
    "/geo/bbox",
    response_model=list[OrganizationDetail],
    summary="Найти организации в прямоугольной области",
    description=(
        "Возвращает все организации, здания которых находятся внутри "
        "прямоугольной области, заданной координатами.\n\n"
        "Используется фильтрация по координатам зданий (lat/lon)."
    ),
)
async def list_organizations_within_bbox(
    org_repo: Annotated[
        OrganizationReadRepositoryProtocol, Depends(get_organization_read_repo)
    ],
    min_lat: float = Query(..., description="Минимальная широта (нижняя граница)"),
    min_lon: float = Query(..., description="Минимальная долгота (левая граница)"),
    max_lat: float = Query(..., description="Максимальная широта (верхняя граница)"),
    max_lon: float = Query(..., description="Максимальная долгота (правая граница)"),
):
    """Возвращает организации, находящиеся в пределах bounding box."""
    bbox = GeoBBox(
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
    )
    return await org_repo.list_within_bbox(bbox=bbox)


@router.get(
    "/geo/radius",
    response_model=list[OrganizationDetail],
    summary="Найти организации в радиусе от точки",
    description=(
        "Возвращает все организации, находящиеся в пределах радиуса от заданной точки.\n\n"
        "Реализация использует приближённый расчёт через bounding box (квадрат вокруг точки)."
    ),
)
async def list_organizations_within_radius(
    org_repo: Annotated[
        OrganizationReadRepositoryProtocol, Depends(get_organization_read_repo)
    ],
    lat: float = Query(..., description="Широта центра"),
    lon: float = Query(..., description="Долгота центра"),
    radius_meters: float = Query(..., gt=0, description="Радиус в метрах"),
):
    """Возвращает организации в радиусе от точки."""
    center = GeoPoint(lat=lat, lon=lon)
    return await org_repo.list_within_radius(
        center=center,
        radius_meters=radius_meters,
    )


app.include_router(router)
