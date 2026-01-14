### API

- `GET /organizations` — поиск организаций по фильтрам (логика AND, `ILIKE` для name/building/activity, точное совпадение для phone).
- `GET /organizations/{org_id}` — карточка организации по идентификатору.
- `GET /organizations/geo/bbox` — поиск организаций в прямоугольнике по координатам здания.
- `GET /organizations/geo/radius` — поиск организаций в радиусе от точки (упрощённый расчёт через bounding box, без PostGIS).

### Домен

Проект следует DDD-подходу в рамках bounded context «каталога организаций». Доменная модель включает агрегаты Organization, Activity и Building, а также value object GeoPoint. Инварианты проверяются внутри доменных сущностей.

Отдельное правило домена: **максимум 3 уровня вложенности деятельностей**. Это ограничение закреплено в инварианте агрегата `Activity` (уровень допускается только 1..3).

### Запуск сервиса

```bash
docker compose up --build
```

API будет доступен на `http://localhost:8000`.

### Миграции

Миграции применяются автоматически при старте контейнера `api` (команда `alembic upgrade head` уже включена в `docker-compose.yml`).

### Наполнение тестовыми данными (seed)

```bash
make seed_dev
```

### Примеры запросов

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations?name=Молочный"
```
ожидаемый результат — 1 организация

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations?building=Ленина&activity=Еда"
```
ожидаемый результат - 2 организации

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations?phone=+7%20(495)%20111-22-33"
```
ожидаемый результат — 2 организации

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations/geo/bbox?min_lat=55.75&min_lon=37.60&max_lat=55.78&max_lon=37.65"
```
ожидаемый результат — 5 организаций

```bash
curl -H "X-API-Key: defaultkey-123456789" "http://localhost:8000/organizations/geo/radius?lat=55.76&lon=37.62&radius_meters=1500"
```
ожидаемый результат — 3 организации
