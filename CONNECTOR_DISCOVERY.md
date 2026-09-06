# Statsig Connector — Discovery

**Vendor:** Statsig (https://statsig.com)  
**API Base URL:** `https://api.statsig.com/console/v1`  
**Authentication:** Console API Key (STATSIG-API-KEY header)

## Архитектура API
- **Ключевые сущности:** Feature Gates (/gates), эксперименты (/experiments), динамические конфиги (/dynamic_configs), метрики
- **Формат обмена данными:** JSON / HTTPS REST.
- **Обработка ошибок:** Стандартные HTTP-коды (400, 401, 403, 404, 429, 500) с типизацией ответа.
- **Тестовая точка проверки подключения:** `GET /console/v1/gates`.
