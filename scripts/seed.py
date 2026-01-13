import asyncio

from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from uuid_extensions import uuid7

from src.infra.db import (
    DATABASE_URL,
    activities,
    buildings,
    organization_activities,
    organization_phones,
    organizations,
)


async def seed() -> None:
    engine = create_async_engine(DATABASE_URL)

    async with AsyncSession(engine) as session:
        # clean existing data (delete in child-first order to avoid FK issues)

        await session.execute(delete(organization_activities))
        await session.execute(delete(organization_phones))
        await session.execute(delete(organizations))
        await session.execute(delete(activities))
        await session.execute(delete(buildings))

        # buildings
        b1 = uuid7()
        b2 = uuid7()
        b3 = uuid7()
        b4 = uuid7()

        buildings_data = [
            {"id": b1, "address": "ул. Ленина, 1", "lat": 55.7558, "lon": 37.6173},
            {"id": b2, "address": "ул. Куйбышева, 10", "lat": 55.7600, "lon": 37.6200},
            {"id": b3, "address": "пр. Мира, 5", "lat": 55.7700, "lon": 37.6400},
            {"id": b4, "address": "ул. Московская, 12", "lat": 55.7800, "lon": 37.6500},
        ]
        await session.execute(insert(buildings), buildings_data)

        # activities (10 total to match the requirement)
        # Keep the hierarchy requested and add two extra sibling activities to reach 10
        a_food = uuid7()
        a_meat = uuid7()
        a_milk = uuid7()
        a_confection = uuid7()  # extra under Еда

        a_auto = uuid7()
        a_truck = uuid7()
        a_passenger = uuid7()
        a_spare = uuid7()
        a_accessory = uuid7()
        a_tires = uuid7()  # extra under Автомобили

        activities_data = [
            {"id": a_food, "name": "Еда", "parent_id": None, "level": 1},
            {"id": a_meat, "name": "Мясная продукция", "parent_id": a_food, "level": 2},
            {"id": a_milk, "name": "Молочная продукция", "parent_id": a_food, "level": 2},
            {"id": a_confection, "name": "Кондитерская продукция", "parent_id": a_food, "level": 2},

            {"id": a_auto, "name": "Автомобили", "parent_id": None, "level": 1},
            {"id": a_truck, "name": "Грузовые", "parent_id": a_auto, "level": 2},
            {"id": a_passenger, "name": "Легковые", "parent_id": a_auto, "level": 2},
            {"id": a_spare, "name": "Запчасти", "parent_id": a_passenger, "level": 3},
            {"id": a_accessory, "name": "Аксессуары", "parent_id": a_passenger, "level": 3},
            {"id": a_tires, "name": "Шины", "parent_id": a_auto, "level": 2},
        ]
        await session.execute(insert(activities), activities_data)

        # organizations (5 total). Two organizations share the same building (b1), others in separate buildings
        org1 = uuid7()
        org2 = uuid7()
        org3 = uuid7()
        org4 = uuid7()
        org5 = uuid7()

        organizations_data = [
            {"id": org1, "name": "Ресторан \"У Лукаша\"", "building_id": b1},
            {"id": org2, "name": "Молочный дом", "building_id": b1},
            {"id": org3, "name": "ООО \"Транспорт плюс\"", "building_id": b2},
            {"id": org4, "name": "Автосервис \"Легко\"", "building_id": b3},
            {"id": org5, "name": "Шиномонтаж \"Колесо\"", "building_id": b4},
        ]
        await session.execute(insert(organizations), organizations_data)

        # link organizations to activities
        org_activities_data = [
            {"organization_id": org1, "activity_id": a_food},
            {"organization_id": org1, "activity_id": a_meat},
            {"organization_id": org1, "activity_id": a_confection},

            {"organization_id": org2, "activity_id": a_milk},

            {"organization_id": org3, "activity_id": a_truck},

            {"organization_id": org4, "activity_id": a_passenger},
            {"organization_id": org4, "activity_id": a_spare},
            {"organization_id": org4, "activity_id": a_accessory},

            {"organization_id": org5, "activity_id": a_tires},
        ]
        await session.execute(insert(organization_activities), org_activities_data)

        # organization phones (1-2 per org)
        phones_data = [
            {"organization_id": org1, "phone": "+7 (495) 111-22-33"},
            {"organization_id": org1, "phone": "+7 (495) 111-22-34"},

            {"organization_id": org2, "phone": "+7 (495) 222-33-44"},

            {"organization_id": org3, "phone": "+7 (495) 333-44-55"},

            {"organization_id": org4, "phone": "+7 (495) 444-55-66"},
            {"organization_id": org4, "phone": "+7 (495) 444-55-67"},

            {"organization_id": org5, "phone": "+7 (495) 111-22-33"},
        ]
        await session.execute(insert(organization_phones), phones_data)

        await session.commit()

    await engine.dispose()
    print("Seed completed")


if __name__ == "__main__":
    asyncio.run(seed())
