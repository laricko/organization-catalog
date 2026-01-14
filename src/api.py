from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto import OrganizationDetail
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


router = APIRouter(prefix="/organizations", tags=["Organizations"])


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
    organization = await org_repo.get_by_id(org_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


app.include_router(router)
