# Original tests (init, request plumbing, endpoints)
import json
from unittest.mock import MagicMock, patch

import pytest

from habr.client import HabrClient


def test_init_defaults():
    client = HabrClient()
    assert client.cookies == ""
    assert client.api_key == HabrClient.DEFAULT_API_KEY
    assert client.hl == "ru"
    assert client.fl == "ru"


def test_init_custom():
    client = HabrClient(cookies="test=1", api_key="custom_key", hl="en", fl="en")
    assert client.cookies == "test=1"
    assert client.api_key == "custom_key"
    assert client.hl == "en"
    assert client.fl == "en"


@patch("urllib.request.urlopen")
def test_request_get_params_and_headers(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"alias": "NQAI", "id": 123}).encode(
        "utf-8"
    )
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient(cookies="sid=xyz", api_key="test_api_key")
    data = client.get_me()

    assert data == {"alias": "NQAI", "id": 123}
    assert mock_urlopen.call_count == 1

    req = mock_urlopen.call_args[0][0]
    assert req.method == "GET"
    assert req.headers["Apikey"] == "test_api_key"
    assert req.headers["Cookie"] == "sid=xyz"
    assert "hl=ru" in req.full_url
    assert "fl=ru" in req.full_url
    assert req.full_url.startswith("https://habr.com/kek/v2/me?")


@patch("urllib.request.urlopen")
def test_get_user_card(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"scoreStats": {"score": 42}}).encode(
        "utf-8"
    )
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient()
    res = client.get_user_card("NQAI")

    assert res["scoreStats"]["score"] == 42
    req = mock_urlopen.call_args[0][0]
    assert "/users/NQAI/card" in req.full_url


@patch("urllib.request.urlopen")
def test_get_user_whois(mock_urlopen):
    mock_resp = MagicMock()
    data = {"badgets": [{"title": "author"}]}
    mock_resp.read.return_value = json.dumps(data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient()
    res = client.get_user_whois("NQAI")

    assert res["badgets"][0]["title"] == "author"
    req = mock_urlopen.call_args[0][0]
    assert "/users/NQAI/whois" in req.full_url


@patch("urllib.request.urlopen")
def test_get_user_articles_pagination(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"articleIds": ["1", "2"]}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient()
    res = client.get_user_articles("NQAI", page=2)

    assert res["articleIds"] == ["1", "2"]
    req = mock_urlopen.call_args[0][0]
    assert "user=NQAI" in req.full_url
    assert "page=2" in req.full_url


@patch("urllib.request.urlopen")
def test_get_article_and_comments(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"id": "12345"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient()
    client.get_article("12345")
    assert "/articles/12345?" in mock_urlopen.call_args[0][0].full_url

    client.get_article_comments("12345")
    assert "/articles/12345/comments?" in mock_urlopen.call_args[0][0].full_url


@patch("urllib.request.urlopen")
def test_get_hub_info(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"alias": "go"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient()
    res = client.get_hub_info("go")
    assert res["alias"] == "go"
    assert "/hubs/go/profile?" in mock_urlopen.call_args[0][0].full_url


@patch("urllib.request.urlopen")
def test_empty_response(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b""
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client = HabrClient()
    res = client._request("GET", "/test")
    assert res == {}


import urllib.error
import urllib.request
from unittest.mock import patch

from habr.client import (
    HabrError,
    HabrHTTPError,
    HabrRateLimitError,
    HabrTimeoutError,
)


def make_response(payload: dict, status: int = 200) -> object:
    class FakeResp:
        def __init__(self, raw: bytes):
            self._raw = raw
            self.status = status

        def read(self) -> bytes:
            return self._raw

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return FakeResp(json.dumps(payload).encode("utf-8"))


class TestErrorHandling:
    def test_http_error_raises_habrhttperror_with_status_and_body(self):
        client = HabrClient()
        err = urllib.error.HTTPError(
            "https://habr.com/kek/v2/me",
            404,
            "Not Found",
            {},
            None,  # type: ignore[arg-type]
        )
        err.read = lambda: b'{"code": "NOT_FOUND"}'  # type: ignore[method-assign]
        with patch("urllib.request.urlopen", side_effect=err), pytest.raises(HabrHTTPError) as exc_info:
                client.get_me()
        assert exc_info.value.status == 404
        assert "NOT_FOUND" in exc_info.value.body

    def test_429_raises_ratelimit_error(self):
        client = HabrClient()
        err = urllib.error.HTTPError(
            "https://habr.com/kek/v2/me",
            429,
            "Too Many Requests",
            {},
            None,  # type: ignore[arg-type]
        )
        err.read = lambda: b"rate limited"  # type: ignore[method-assign]
        with patch("urllib.request.urlopen", side_effect=err), pytest.raises(HabrRateLimitError) as exc_info:
                client.get_me()
        assert exc_info.value.status == 429

    def test_500_retried_then_succeeds(self):
        client = HabrClient(retries=2, retry_delay=0)
        err = urllib.error.HTTPError(
            "https://habr.com/kek/v2/me",
            500,
            "Server Error",
            {},
            None,  # type: ignore[arg-type]
        )
        err.read = lambda: b""  # type: ignore[method-assign]
        responses = [err, err, make_response({"alias": "nqai"})]
        with patch("urllib.request.urlopen", side_effect=responses):
            result = client.get_me()
        assert result == {"alias": "nqai"}

    def test_500_exhausts_retries_raises_httperror(self):
        client = HabrClient(retries=1, retry_delay=0)
        err = urllib.error.HTTPError(
            "https://habr.com/kek/v2/me",
            503,
            "Unavailable",
            {},
            None,  # type: ignore[arg-type]
        )
        err.read = lambda: b""  # type: ignore[method-assign]
        with patch("urllib.request.urlopen", side_effect=err) as mock_urlopen, pytest.raises(HabrHTTPError):
                client.get_me()
        assert mock_urlopen.call_count == 2  # initial + 1 retry

    def test_429_not_retried(self):
        client = HabrClient(retries=2, retry_delay=0)
        err = urllib.error.HTTPError(
            "https://habr.com/kek/v2/me",
            429,
            "Too Many Requests",
            {},
            None,  # type: ignore[arg-type]
        )
        err.read = lambda: b""  # type: ignore[method-assign]
        with patch("urllib.request.urlopen", side_effect=err) as mock_urlopen, pytest.raises(HabrRateLimitError):
                client.get_me()
        assert mock_urlopen.call_count == 1

    def test_404_not_retried(self):
        client = HabrClient(retries=2, retry_delay=0)
        err = urllib.error.HTTPError(
            "https://habr.com/kek/v2/me",
            404,
            "Not Found",
            {},
            None,  # type: ignore[arg-type]
        )
        err.read = lambda: b""  # type: ignore[method-assign]
        with patch("urllib.request.urlopen", side_effect=err) as mock_urlopen, pytest.raises(HabrHTTPError):
                client.get_me()
        assert mock_urlopen.call_count == 1

    def test_timeout_raises_habrtimeouterror(self):
        client = HabrClient(timeout=0.1)
        reason = TimeoutError("timed out")
        url_err = urllib.error.URLError(reason)
        with patch("urllib.request.urlopen", side_effect=url_err), pytest.raises(HabrTimeoutError):
                client.get_me()

    def test_timeout_retried_then_raises(self):
        client = HabrClient(timeout=0.1, retries=1, retry_delay=0)
        reason = TimeoutError("timed out")
        url_err = urllib.error.URLError(reason)
        with patch("urllib.request.urlopen", side_effect=url_err) as mock_urlopen, pytest.raises(HabrTimeoutError):
                client.get_me()
        assert mock_urlopen.call_count == 2

    def test_urlerror_wrapped_in_habrerror(self):
        client = HabrClient()
        url_err = urllib.error.URLError("connection refused")
        with patch("urllib.request.urlopen", side_effect=url_err), pytest.raises(HabrError) as exc_info:
                client.get_me()
        assert "connection refused" in str(exc_info.value)

    def test_timeout_passed_to_urlopen(self):
        client = HabrClient(timeout=7.5)
        with patch(
            "urllib.request.urlopen", return_value=make_response({})
        ) as mock_urlopen:
            client.get_me()
        assert mock_urlopen.call_args.kwargs.get("timeout") == 7.5


class TestArticlesFeed:
    def test_feed_joins_article_ids(self):
        client = HabrClient()
        with patch(
            "urllib.request.urlopen", return_value=make_response({"articleRefs": []})
        ) as mock_urlopen:
            client.get_articles_feed(articles=["100", "200"])
        url = mock_urlopen.call_args.args[0].full_url
        assert "articles=100%2C200" in url
        assert "/articles/list/" in url

    def test_feed_supports_news_ids(self):
        client = HabrClient()
        with patch(
            "urllib.request.urlopen", return_value=make_response({"newsRefs": []})
        ) as mock_urlopen:
            client.get_articles_feed(news=["5"])
        url = mock_urlopen.call_args.args[0].full_url
        assert "news=5" in url

    def test_feed_rejects_empty_input(self):
        client = HabrClient()
        with pytest.raises(ValueError):
            client.get_articles_feed()


class TestCommentsThreads:
    def test_threads_articles_param(self):
        client = HabrClient()
        with patch(
            "urllib.request.urlopen", return_value=make_response({"commentRefs": []})
        ) as mock_urlopen:
            client.get_comments_threads(articles=["700"])
        url = mock_urlopen.call_args.args[0].full_url
        assert "articles=700" in url
        assert "/comments/thread/" in url

    def test_threads_comments_param(self):
        client = HabrClient()
        with patch(
            "urllib.request.urlopen", return_value=make_response({"commentRefs": []})
        ) as mock_urlopen:
            client.get_comments_threads(comments=["1", "2"])
        url = mock_urlopen.call_args.args[0].full_url
        assert "comments=1%2C2" in url

    def test_threads_rejects_empty_input(self):
        client = HabrClient()
        with pytest.raises(ValueError):
            client.get_comments_threads()
