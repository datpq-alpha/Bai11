"""FastAPI có thể chạy local hoặc triển khai thành Vercel Function."""

import os
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Vercel chỉ cho ghi file tạm trong /tmp. Database này phù hợp để demo,
# nhưng dữ liệu có thể mất khi function được tạo lại.
DEFAULT_DB_PATH = "/tmp/weather.db" if os.getenv("VERCEL") else str(ROOT_DIR / "weather.db")
DB_PATH = Path(os.getenv("WEATHER_DB_PATH", DEFAULT_DB_PATH))

app = FastAPI(title="Bài 11 - Deployed Weather API")


class FavoriteCity(BaseModel):
    city_name: str = Field(min_length=1, max_length=100)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS favorite_cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_name TEXT NOT NULL UNIQUE
            )
            """
        )
        connection.commit()


def get_weather(city: str):
    params = {"q": city, "appid": API_KEY, "units": "metric", "lang": "vi"}
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=10)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    return {
        "city": data["name"],
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
    }


init_database()


@app.get("/")
def home():
    return {"message": "Deployed Weather API đang chạy"}


@app.get("/weather")
def weather(city: str):
    data = get_weather(city)
    if data is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành phố")
    return data


@app.get("/cities")
def list_cities():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, city_name FROM favorite_cities ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/cities", status_code=status.HTTP_201_CREATED)
def add_city(city: FavoriteCity):
    city_name = city.city_name.strip()
    if not city_name:
        raise HTTPException(status_code=422, detail="Tên thành phố không được để trống")

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO favorite_cities (city_name) VALUES (?)", (city_name,)
            )
            connection.commit()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Thành phố đã tồn tại") from error

    return {"id": cursor.lastrowid, "city_name": city_name}


@app.delete("/cities/{city_name}")
def delete_city(city_name: str):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM favorite_cities WHERE city_name = ?", (city_name,)
        )
        connection.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Thành phố không có trong danh sách")
    return {"deleted": city_name}

