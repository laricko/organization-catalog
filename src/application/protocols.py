from typing import Protocol, Sequence
from uuid import UUID

from application.dto import OrganizationDetail


class OrganizationReadRepositoryProtocol(Protocol):
    async def search(
        self,
        *,
        name: str | None,
        building: str | None,
        phone: str | None,
        activity: str | None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OrganizationDetail]:
        """Поиск организаций по набору фильтров."""
        ...

    async def get_by_id(self, *, organization_id: UUID) -> OrganizationDetail | None:
        """Вывод информации об организации по её идентификатору."""
        ...
