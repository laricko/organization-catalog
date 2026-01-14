from dataclasses import dataclass
from typing import Protocol, Sequence
from uuid import UUID

from application.dto import OrganizationDetail
from domain.entities import GeoPoint


@dataclass(frozen=True, slots=True)
class GeoBBox:
    """
    Bounding box (rectangle) on map.

    min_lat/min_lon - bottom-left
    max_lat/max_lon - top-right
    """

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class OrganizationReadRepositoryProtocol(Protocol):
    async def list_by_building(
        self, *, building_id: UUID
    ) -> Sequence[OrganizationDetail]:
        """Список всех организаций, находящихся в конкретном здании."""
        ...

    async def list_by_activity(
        self, *, activity_id: UUID
    ) -> Sequence[OrganizationDetail]:
        """
        Список всех организаций, которые относятся к указанному виду деятельности.
        Должны учитываться вложенные виды деятельности.
        """
        ...

    async def list_within_radius(
        self,
        *,
        center: GeoPoint,
        radius_meters: float,
    ) -> Sequence[OrganizationDetail]:
        """Список организаций в заданном радиусе относительно точки (через координаты здания)."""
        ...

    async def list_within_bbox(
        self,
        *,
        bbox: GeoBBox,
    ) -> Sequence[OrganizationDetail]:
        """Список организаций в прямоугольной области (через координаты здания)."""
        ...

    async def get_by_id(self, *, organization_id: UUID) -> OrganizationDetail | None:
        """Вывод информации об организации по её идентификатору."""
        ...

    async def search_by_name(self, *, query: str) -> Sequence[OrganizationDetail]:
        """Поиск организации по названию."""
        ...
