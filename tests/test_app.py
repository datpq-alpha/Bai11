"""Năm bài tập kiểm thử được giữ lại từ Bài 10."""

import pytest
from fastapi.testclient import TestClient

import backend.main as api


client = TestClient(api.app)


class FakeWeatherResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def json(self):
        return {
            "name": "Hanoi",
            "main": {"temp": 30, "humidity": 70},
            "weather": [{"description": "trời quang", "icon": "01d"}],
        }


@pytest.fixture(autouse=True)
def use_temporary_database(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "test_weather.db")
    api.init_database()


def test_home():
    # TODO 1/5: GET /, kiểm tra status 200 và message có chữ "đang chạy".
    raise NotImplementedError


def test_weather_success(monkeypatch):
    # TODO 2/5: Mock api.requests.get bằng FakeWeatherResponse, rồi kiểm tra /weather.
    raise NotImplementedError


def test_weather_not_found(monkeypatch):
    # TODO 3/5: Mock response status 404 và kiểm tra API của ta cũng trả status 404.
    raise NotImplementedError


def test_add_and_list_city():
    # TODO 4/5: POST Hanoi vào /cities, sau đó GET /cities và kiểm tra danh sách.
    raise NotImplementedError


def test_duplicate_and_delete_city():
    # TODO 5/5: Kiểm tra POST trùng trả 409, DELETE thành công và danh sách trở lại rỗng.
    raise NotImplementedError

