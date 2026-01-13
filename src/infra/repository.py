from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto import OrganizationDetail


class OrganizationRepository:
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
            return
        return OrganizationDetail.model_validate(row)
