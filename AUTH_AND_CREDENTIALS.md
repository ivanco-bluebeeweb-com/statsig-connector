# Statsig Connector — Auth & Credentials Standard

**Compliance:** AUTH_AND_CREDENTIALS_STANDARD.md (B1–B10)

## Схема аутентификации
- **Метод:** Console API Key (STATSIG-API-KEY header)
- **Хранение:** Секреты сохраняются изолированно в хранилище секретов платформы Imperal.
- **Валидация:** При сохранении ключа выполняется тестовый запрос `GET /console/v1/gates`.
- **Отключение:** Удаление локальных ключей без воздействия на аккаунт вендора.
