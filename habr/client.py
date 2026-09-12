import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Optional, List

class HabrClient:
    """Легковесный клиент для Habr API (v2 / kek API)."""

    BASE_URL = "https://habr.com/kek/v2"
    DEFAULT_API_KEY = "***"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    def __init__(self, cookies: Optional[str] = None, api_key: Optional[str] = None, hl: str = "ru", fl: str = "ru"):
        self.cookies = cookies or ""
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.hl = hl
        self.fl = fl

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        query_params = {"hl": self.hl, "fl": self.fl}
        if params:
            query_params.update(params)

        if query_params:
            url += "?" + urllib.parse.urlencode(query_params)

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "apikey": self.api_key
        }
        if self.cookies:
            headers["Cookie"] = self.cookies

        body_bytes = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def get_me(self) -> Dict[str, Any]:
        """Получить текущий профиль авторизованного пользователя."""
        return self._request("GET", "/me")

    def get_user_card(self, username: str) -> Dict[str, Any]:
        """Получить карточку пользователя (рейтинг, карма, статистика)."""
        return self._request("GET", f"/users/{username}/card")

    def get_user_whois(self, username: str) -> Dict[str, Any]:
        """Получить подробную информацию 'О себе' пользователя."""
        return self._request("GET", f"/users/{username}/whois")

    def get_user_articles(self, username: str, page: int = 1) -> Dict[str, Any]:
        """Список опубликованных статей пользователя."""
        return self._request("GET", "/articles/", params={"user": username, "page": page})

    def get_article(self, article_id: str) -> Dict[str, Any]:
        """Получить статью по ID."""
        return self._request("GET", f"/articles/{article_id}")

    def get_article_comments(self, article_id: str) -> Dict[str, Any]:
        """Получить комментарии к статье."""
        return self._request("GET", f"/articles/{article_id}/comments")

    def get_hub_info(self, hub_alias: str) -> Dict[str, Any]:
        """Получить профиль хаба."""
        return self._request("GET", f"/hubs/{hub_alias}/profile")
