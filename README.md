# Habr API SDK (Python)

Легковесный клиент для работы с API Хабра (v2 / kek API) на чистом Python без внешних зависимостей.

## Возможности
- Чтение профиля текущего пользователя (`get_me`)
- Получение карточки пользователя (`get_user_card`)
- Получение расширенной информации «О себе» (`get_user_whois`)
- Получение списка статей пользователя (`get_user_articles`)
- Получение статьи по ID (`get_article`)
- Получение комментариев к статье (`get_article_comments`)
- Информация о хабах (`get_hub_info`)

## Пример использования
```python
from habr import HabrClient

client = HabrClient(cookies="connect_sid=...")
me = client.get_me()
print(me["alias"], me["id"])
```
