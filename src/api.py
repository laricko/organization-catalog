from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from application.protocols import OrganizationReadRepositoryProtocol
from infra.db import sessionmaker
from infra.repository import OrganizationRepository

app = FastAPI(title="Organization Directory API")

router = APIRouter(prefix="/organizations", tags=["Organizations"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


async def get_organization_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrganizationReadRepositoryProtocol:
    return OrganizationRepository(session)


@router.get("/{org_id}")
async def get_organization_by_id(
    org_id: UUID,
    org_repo: Annotated[OrganizationReadRepositoryProtocol, Depends(get_organization_repo)],
):
    return await org_repo.get_by_id(org_id)


app.include_router(router)
