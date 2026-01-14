### API

- `GET /organizations` — поиск организаций по фильтрам (логика AND, `ILIKE` для name/building/activity, точное совпадение для phone).
- `GET /organizations/{org_id}` — карточка организации по идентификатору.
- `GET /organizations/geo/bbox` — поиск организаций в прямоугольнике по координатам здания.
- `GET /organizations/geo/radius` — поиск организаций в радиусе от точки (упрощённый расчёт через bounding box, без PostGIS).

### Домен

Проект следует DDD-подходу в рамках bounded context "каталога организаций" Доменная модель включает агрегаты Organization, Activity и Building, а также value object GeoPoint. Инварианты проверяются внутри доменных сущностей.

Отдельное правило домена: **максимум 3 уровня вложенности деятельностей**. Это ограничение инкапсулировано в инварианте агрегата `Activity` (уровень допускается только 1..3).

### Запуск дева

```bash
docker compose up --build
```

Миграции применяются автоматически при старте контейнера `api` (команда `alembic upgrade head` уже включена в `docker-compose.yml`).

### Наполнение тестовыми данными (seed)

```bash
make seed_dev
```

### Примеры запросов

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations?name=%D0%9C%D0%BE%D0%BB%D0%BE%D1%87%D0%BD%D1%8B%D0%B9"
```
ожидаемый результат — 1 организация

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations?building=%D0%9B%D0%B5%D0%BD%D0%B8%D0%BD%D0%B0&activity=%D0%95%D0%B4%D0%B0"
```
ожидаемый результат - 2 организации

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations?phone=%2B7%20%28495%29%20111-22-33"
```
ожидаемый результат — 2 организации

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations/geo/bbox?min_lat=55.75&min_lon=37.60&max_lat=55.78&max_lon=37.65"
```
ожидаемый результат — 5 организаций

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations/geo/radius?lat=55.76&lon=37.62&radius_meters=1500"
```
ожидаемый результат — 4 организации

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations/geo/radius?lat=55.76&lon=37.62&radius_meters=500"
```
ожидаемый результат — 3 организации

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations/geo/radius?lat=55.76&lon=37.62&radius_meters=100"
```

ожидаемый результат — 1 организации
