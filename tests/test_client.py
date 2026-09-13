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
    mock_resp.read.return_value = json.dumps({"alias": "NQAI", "id": 123}).encode("utf-8")
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
    mock_resp.read.return_value = json.dumps({"scoreStats": {"score": 42}}).encode("utf-8")
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
