import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class HabrError(Exception):
    """Base error for Habr API SDK."""


class HabrHTTPError(HabrError):
    """Non-2xx HTTP response from the Habr API."""

    def __init__(self, status: int, reason: str, body: str = ""):
        self.status = status
        self.reason = reason
        self.body = body
        super().__init__(f"HTTP {status} {reason}: {body[:200]}")


class HabrRateLimitError(HabrHTTPError):
    """HTTP 429: too many requests."""

    def __init__(self, reason: str, body: str = ""):
        super().__init__(429, reason, body)


class HabrTimeoutError(HabrError):
    """Request exceeded the configured timeout (including retries)."""


class HabrClient:
    """Легковесный клиент для Habr API (v2 / kek API)."""

    BASE_URL = "https://habr.com/kek/v2"
    DEFAULT_API_KEY = "***"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    RETRYABLE_STATUSES = frozenset({500, 502, 503, 504})

    def __init__(
        self,
        cookies: str | None = None,
        api_key: str | None = None,
        hl: str = "ru",
        fl: str = "ru",
        timeout: float = 15.0,
        retries: int = 0,
        retry_delay: float = 0.5,
    ):
        self.cookies = cookies or ""
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.hl = hl
        self.fl = fl
        self.timeout = timeout
        self.retries = max(0, int(retries))
        self.retry_delay = retry_delay

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        query_params: dict[str, Any] = {"hl": self.hl, "fl": self.fl}
        if params:
            query_params.update(params)

        if query_params:
            url += "?" + urllib.parse.urlencode(query_params)

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "apikey": self.api_key,
        }
        if self.cookies:
            headers["Cookie"] = self.cookies

        body_bytes = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(data).encode("utf-8")

        last_error: HabrError | None = None
        for attempt in range(self.retries + 1):
            if attempt > 0:
                time.sleep(self.retry_delay * (2 ** (attempt - 1)))
            req = urllib.request.Request(
                url, data=body_bytes, headers=headers, method=method
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                raw_body = ""
                try:
                    raw_body = e.read().decode("utf-8", errors="replace")
                except (OSError, ValueError):
                    pass
                if e.code == 429:
                    raise HabrRateLimitError(e.reason, raw_body)
                if e.code in self.RETRYABLE_STATUSES and attempt < self.retries:
                    last_error = HabrHTTPError(e.code, e.reason, raw_body)
                    continue
                raise HabrHTTPError(e.code, e.reason, raw_body)
            except urllib.error.URLError as e:
                if isinstance(e.reason, TimeoutError):
                    if attempt < self.retries:
                        last_error = HabrTimeoutError(f"timeout after {self.timeout}s")
                        continue
                    raise HabrTimeoutError(f"timeout after {self.timeout}s")
                raise HabrError(str(e))
        raise last_error or HabrError("request failed")

    # --- Users ---

    def get_me(self) -> dict[str, Any]:
        """Получить текущий профиль авторизованного пользователя."""
        return self._request("GET", "/me")

    def get_user_card(self, username: str) -> dict[str, Any]:
        """Получить карточку пользователя (рейтинг, карма, статистика)."""
        return self._request("GET", f"/users/{username}/card")

    def get_user_whois(self, username: str) -> dict[str, Any]:
        """Получить подробную информацию 'О себе' пользователя."""
        return self._request("GET", f"/users/{username}/whois")

    def get_user_articles(self, username: str, page: int = 1) -> dict[str, Any]:
        """Список опубликованных статей пользователя."""
        return self._request(
            "GET", "/articles/", params={"user": username, "page": page}
        )

    # --- Articles ---

    def get_article(self, article_id: str) -> dict[str, Any]:
        """Получить статью по ID."""
        return self._request("GET", f"/articles/{article_id}")

    def get_article_comments(self, article_id: str) -> dict[str, Any]:
        """Получить комментарии к статье."""
        return self._request("GET", f"/articles/{article_id}/comments")

    def get_articles_feed(
        self,
        articles: list[str] | None = None,
        news: list[str] | None = None,
    ) -> dict[str, Any]:
        """Пакетно получить статьи и новости по ID.

        `articles` — список ID статей, `news` — список ID новостей.
        Возвращает словари `articleRefs` / `newsRefs` в ответе API.
        """
        if not articles and not news:
            raise ValueError(
                "get_articles_feed requires at least one article or news id"
            )
        params: dict[str, Any] = {}
        if articles:
            params["articles"] = ",".join(str(a) for a in articles)
        if news:
            params["news"] = ",".join(str(n) for n in news)
        return self._request("GET", "/articles/list/", params=params)

    def get_comments_threads(
        self,
        articles: list[str] | None = None,
        news: list[str] | None = None,
        comments: list[str] | None = None,
    ) -> dict[str, Any]:
        """Пакетно получить ветки комментариев по ID статей/новостей/комментариев."""
        if not (articles or news or comments):
            raise ValueError(
                "get_comments_threads requires at least one article, news, or comment id"
            )
        params: dict[str, Any] = {}
        if articles:
            params["articles"] = ",".join(str(a) for a in articles)
        if news:
            params["news"] = ",".join(str(n) for n in news)
        if comments:
            params["comments"] = ",".join(str(c) for c in comments)
        return self._request("GET", "/comments/thread/", params=params)

    # --- Hubs ---

    def get_hub_info(self, hub_alias: str) -> dict[str, Any]:
        """Получить профиль хаба."""
        return self._request("GET", f"/hubs/{hub_alias}/profile")
