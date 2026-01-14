from dataclasses import dataclass, field
from uuid import UUID

from uuid_extensions import uuid7


class DomainError(Exception):
    pass


@dataclass(slots=True)
class AggregateRoot:
    id: UUID = field(default_factory=uuid7)


@dataclass(slots=True, kw_only=True)
class Organization(AggregateRoot):
    name: str
    phone_numbers: set[str] = field(default_factory=set)
    activity_ids: set[UUID] = field(default_factory=set)
    building_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class GeoPoint:
    """Value object representing a geographical point."""

    lat: float
    lon: float


@dataclass(slots=True, kw_only=True)
class Building(AggregateRoot):
    address: str
    point: GeoPoint


class ActivityLevelError(DomainError):
    pass


@dataclass(slots=True, kw_only=True)
class Activity(AggregateRoot):
    name: str
    parent_id: UUID | None = None
    level: int

    def __post_init__(self) -> None:
        if self.level not in {1, 2, 3}:
            raise ActivityLevelError("Activity nesting level must be 1..3.")
