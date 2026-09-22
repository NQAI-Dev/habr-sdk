# Habr API SDK (Python)

Легковесный клиент для работы с API Хабра (v2 / kek API) на чистом Python без внешних зависимостей.

## Возможности
- Чтение профиля текущего пользователя (`get_me`)
- Получение карточки пользователя (`get_user_card`)
- Получение расширенной информации «О себе» (`get_user_whois`)
- Получение списка статей пользователя (`get_user_articles`)
- Получение статьи по ID (`get_article`)
- Получение комментариев к статье (`get_article_comments`)
- Пакетная загрузка статей и новостей по ID (`get_articles_feed`)
- Пакетная загрузка веток комментариев (`get_comments_threads`)
- Лента публикаций с сортировкой и фильтрами (`get_articles`)
- Список хабов и профиль хаба (`get_hubs`, `get_hub_info`)
- Список компаний (`get_companies`)
- Обработка ошибок: `HabrHTTPError`, `HabrRateLimitError` (429), `HabrTimeoutError`
- Таймауты и повторные попытки с экспоненциальной задержкой (5xx и таймауты)

## Пример использования
```python
from habr import HabrClient

client = HabrClient(cookies="connect_sid=...")
me = client.get_me()
print(me["alias"], me["id"])
```

## Обработка ошибок

```python
from habr import HabrClient
from habr.client import HabrRateLimitError, HabrHTTPError, HabrTimeoutError

client = HabrClient(timeout=10, retries=2, retry_delay=0.5)

try:
    article = client.get_article("123456")
except HabrRateLimitError:
    ...  # HTTP 429 — подождать и повторить позже
except HabrTimeoutError:
    ...  # превышен таймаут (включая все повторные попытки)
except HabrHTTPError as e:
    ...  # e.status, e.reason, e.body
```

Повторные попытки выполняются автоматически для HTTP 500/502/503/504 и таймаутов,
с экспоненциальной задержкой `retry_delay * 2^(n-1)`. Ошибки 429 и 4xx не повторяются.

## Пакетные запросы

```python
# Статьи и новости одним запросом
refs = client.get_articles_feed(articles=["100", "200"], news=["5"])

# Ветки комментариев по статьям и комментариям
threads = client.get_comments_threads(articles=["100"], comments=["1", "2"])
```

## Лента публикаций

```python
# Топ статей за всё время (по рейтингу)
feed = client.get_articles(sort="rating", page=1, per_page=20)
for pub_id in feed["publicationIds"]:
    article = feed["publicationRefs"][pub_id]
    print(article["titleHtml"], article["statistics"]["score"])

# Статьи хаба
feed = client.get_articles(hub="go", sort="date")

# Публикации компании
feed = client.get_articles(company="yandex")
```

## Хабы и компании

```python
# Список хабов
hubs = client.get_hubs(page=1)
for hub_id in hubs["hubIds"]:
    print(hub_id, hubs["hubRefs"][hub_id]["alias"])

# Профиль конкретного хаба
hub = client.get_hub_info("go")

# Список компаний
companies = client.get_companies(page=1)
for alias in companies["companyIds"]:
    c = companies["companyRefs"][alias]
    print(c["alias"], c["titleHtml"])
```

## Тестирование
```bash
pytest
```
Тестовый набор изолирован от сети (mock urllib.request) и проверяет формирование URL, заголовков и разбор ответов.
