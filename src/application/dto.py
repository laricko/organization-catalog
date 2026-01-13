from pydantic import BaseModel


class OrganizationDetail(BaseModel):
    name: str
    phone_numbers: list[str]
    address: str
    activities: list[str]