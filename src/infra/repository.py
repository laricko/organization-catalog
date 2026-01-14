import math
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto import GeoBBox, OrganizationDetail
from domain.entities import GeoPoint

_BASE_CTES = (
    """
    phones AS (
        SELECT
            op.organization_id,
            array_agg(DISTINCT op.phone) AS phone_numbers
        FROM organization_phones op
        GROUP BY op.organization_id
    )
    """,
    """
    acts AS (
        SELECT
            oa.organization_id,
            array_agg(DISTINCT a.name) AS activities
        FROM organization_activities oa
        JOIN activities a ON a.id = oa.activity_id
        GROUP BY oa.organization_id
    )
    """,
)

_BASE_SELECT = """
SELECT
    o.id AS id,
    o.name AS name,
    b.address AS address,
    COALESCE(p.phone_numbers, ARRAY[]::text[]) AS phone_numbers,
    COALESCE(x.activities, ARRAY[]::text[]) AS activities
FROM organizations o
JOIN buildings b ON b.id = o.building_id
LEFT JOIN phones p ON p.organization_id = o.id
LEFT JOIN acts x ON x.organization_id = o.id
"""


class OrganizationReadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, *, organization_id: UUID) -> OrganizationDetail | None:
        """Возвращает карточку организации по идентификатору."""
        sql = f"""
        WITH {self._build_ctes(None)}
        {_BASE_SELECT}
        WHERE o.id = :org_id
        """
        return await self._execute_one(sql, {"org_id": organization_id})

    async def search(
        self,
        *,
        name: str | None,
        building: str | None,
        phone: str | None,
        activity: str | None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OrganizationDetail]:
        """Ищет организации по фильтрам с логикой AND."""
        assert any([name, building, phone, activity])
        where_sql, params = self._build_where(
            name=name,
            building=building,
            phone=phone,
            activity=activity,
        )
        params.update({"limit": limit, "offset": offset})
        sql = f"""
        WITH {self._build_ctes(activity)}
        {_BASE_SELECT}
        {where_sql}
        ORDER BY o.name
        LIMIT :limit
        OFFSET :offset
        """
        return await self._execute_many(sql, params)

    async def list_within_bbox(self, *, bbox: GeoBBox) -> list[OrganizationDetail]:
        """Возвращает организации, чьи здания попадают в прямоугольник."""
        sql = f"""
        WITH {self._build_ctes(None)}
        {_BASE_SELECT}
        WHERE (b.lat BETWEEN :min_lat AND :max_lat)
          AND (b.lon BETWEEN :min_lon AND :max_lon)
        ORDER BY o.name
        """
        params = {
            "min_lat": bbox.min_lat,
            "max_lat": bbox.max_lat,
            "min_lon": bbox.min_lon,
            "max_lon": bbox.max_lon,
        }
        return await self._execute_many(sql, params)

    async def list_within_radius(
        self,
        *,
        center: GeoPoint,
        radius_meters: float,
    ) -> list[OrganizationDetail]:
        """Ищет организации в радиусе через аппроксимацию bounding box."""
        meters_per_deg = 111_320.0
        dlat = radius_meters / meters_per_deg
        dlon = radius_meters / (meters_per_deg * max(math.cos(math.radians(center.lat)), 1e-12))

        bbox = GeoBBox(
            min_lat=center.lat - dlat,
            max_lat=center.lat + dlat,
            min_lon=center.lon - dlon,
            max_lon=center.lon + dlon,
        )
        return await self.list_within_bbox(bbox=bbox)

    def _build_ctes(self, activity: str | None) -> str:
        parts = list(_BASE_CTES)
        if activity:
            parts.extend(
                [
                    """
                    activity_roots AS (
                        SELECT a.id
                        FROM activities a
                        WHERE a.name ILIKE :activity
                    )
                    """,
                    """
                    activity_subtree AS (
                        SELECT id FROM activity_roots
                        UNION
                        SELECT a1.id
                        FROM activities a1
                        JOIN activity_roots ar ON a1.parent_id = ar.id
                        UNION
                        SELECT a2.id
                        FROM activities a2
                        JOIN activities a1 ON a2.parent_id = a1.id
                        JOIN activity_roots ar ON a1.parent_id = ar.id
                    )
                    """,
                ]
            )
        return ", ".join(part.strip() for part in parts)

    def _build_where(
        self,
        *,
        name: str | None,
        building: str | None,
        phone: str | None,
        activity: str | None,
    ) -> tuple[str, dict[str, object]]:
        conditions: list[str] = []
        params: dict[str, object] = {}

        if name:
            conditions.append("o.name ILIKE :name")
            params["name"] = f"%{name.strip()}%"
        if building:
            conditions.append("b.address ILIKE :building")
            params["building"] = f"%{building.strip()}%"
        if phone:
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM organization_phones op
                    WHERE op.organization_id = o.id AND op.phone = :phone
                )
                """
            )
            params["phone"] = phone
        if activity:
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM organization_activities oa
                    WHERE oa.organization_id = o.id
                      AND oa.activity_id IN (SELECT id FROM activity_subtree)
                )
                """
            )
            params["activity"] = f"%{activity}%"

        if not conditions:
            return "", params

        joined = " AND ".join(f"({condition.strip()})" for condition in conditions)
        return f"WHERE {joined}", params

    async def _execute_many(
        self,
        sql: str,
        params: dict[str, object],
    ) -> list[OrganizationDetail]:
        result = await self.session.execute(text(sql), params)
        rows = result.mappings().all()
        return [OrganizationDetail.model_validate(row) for row in rows]

    async def _execute_one(
        self,
        sql: str,
        params: dict[str, object],
    ) -> OrganizationDetail | None:
        result = await self.session.execute(text(sql), params)
        row = result.mappings().first()
        if not row:
            return None
        return OrganizationDetail.model_validate(row)
