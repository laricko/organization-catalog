from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationDetail(BaseModel):
    id: UUID = Field(..., description="Идентефикатор организации")
    name: str = Field(
        ..., description="Название организации", examples=["ООО “Рога и Копыта”"]
    )
    phone_numbers: list[str] = Field(
        ...,
        description="Контактные номера",
        examples=["2-222-222", "3-333-333", "8-923-666-13-13"],
    )
    address: str = Field(..., description="Здание, адрес", examples=["Блюхера, 32/1"])
    activities: list[str] = Field(
        ...,
        description="Деятельность",
        examples=["Молочная продукция", "Мясная продукция”"],
    )
