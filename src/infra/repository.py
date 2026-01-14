from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto import OrganizationDetail


class OrganizationReadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, org_id: UUID) -> OrganizationDetail | None:
        stmt = text(
            """
            WITH phones AS (
                SELECT
                    op.organization_id,
                    array_agg(DISTINCT op.phone) AS phone_numbers
                FROM organization_phones op
                GROUP BY op.organization_id
            ),
            acts AS (
                SELECT
                    oa.organization_id,
                    array_agg(DISTINCT a.name) AS activities
                FROM organization_activities oa
                JOIN activities a ON a.id = oa.activity_id
                GROUP BY oa.organization_id
            )
            SELECT
                o.name AS name,
                b.address AS address,
                COALESCE(p.phone_numbers, ARRAY[]::text[]) AS phone_numbers,
                COALESCE(x.activities, ARRAY[]::text[]) AS activities
            FROM organizations o
            JOIN buildings b ON b.id = o.building_id
            LEFT JOIN phones p ON p.organization_id = o.id
            LEFT JOIN acts x ON x.organization_id = o.id
            WHERE o.id = :org_id
            """
        )
        result = await self.session.execute(stmt, {"org_id": org_id})
        row = result.mappings().first()
        if not row:
            return None
        return OrganizationDetail.model_validate(row)

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
        assert any([name, building, phone, activity])
        ctes = [
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
        ]
        where_clauses: list[str] = []
        params: dict[str, object] = {"limit": limit, "offset": offset}

        if name:
            where_clauses.append("o.name ILIKE :name")
            params["name"] = f"%{name.strip()}%"
        if building:
            where_clauses.append("b.address ILIKE :building")
            params["building"] = f"%{building.strip()}%"
        if phone:
            where_clauses.append(
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
            ctes.extend(
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
            where_clauses.append(
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

        where_sql = ""
        if where_clauses:
            joined = " AND ".join(clause.strip() for clause in where_clauses)
            where_sql = f"WHERE {joined}"

        stmt = text(
            f"""
            WITH {", ".join(ctes)}
            SELECT
                o.id as id,
                o.name AS name,
                b.address AS address,
                COALESCE(p.phone_numbers, ARRAY[]::text[]) AS phone_numbers,
                COALESCE(x.activities, ARRAY[]::text[]) AS activities
            FROM organizations o
            JOIN buildings b ON b.id = o.building_id
            LEFT JOIN phones p ON p.organization_id = o.id
            LEFT JOIN acts x ON x.organization_id = o.id
            {where_sql}
            ORDER BY o.name
            LIMIT :limit
            OFFSET :offset
            """
        )
        result = await self.session.execute(stmt, params)
        rows = result.mappings().all()
        return [OrganizationDetail.model_validate(row) for row in rows]
