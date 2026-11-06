# Руководство по запуску тестов

**Перед запуском тестов рекомендуется активировать соответствующий профиль Docker.**
```
docker compose --profile test up -d
```

Для запуска полного набора тестов используйте следующие команды:
```
docker compose --profile test exec testapi pytest
# или (для получения подробного вывода)
docker compose --profile test exec testapi pytest -v
```

Тесты в этом проекте разделены на модульные (unit), интеграционные (integration) и сквозные (e2e).

Для запуска тестов определенного типа используйте следующие команды:
```
docker compose --profile test exec testapi pytest -m unit|integration|e2e
```
