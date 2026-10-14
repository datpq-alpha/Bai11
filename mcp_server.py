"""MCP server cung cấp các công cụ thời tiết cho Gemini qua stdio."""

import os
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 15

mcp = FastMCP("weather-assistant-tools")


def response_data(response: requests.Response):
    """Đổi response của backend thành dữ liệu dễ hiểu cho mô hình."""
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.ok:
        return payload

    detail = payload.get("detail", "Backend không xử lý được yêu cầu")
    return {
        "success": False,
        "status_code": response.status_code,
        "error": detail,
    }


@mcp.tool()
def get_current_weather(city: str):
    """Xem thời tiết hiện tại của một thành phố.

    Args:
        city: Tên thành phố, ví dụ Hanoi, Hue hoặc Da Nang.
    """
    try:
        response = requests.get(
            f"{API_URL}/weather",
            params={"city": city.strip()},
            timeout=REQUEST_TIMEOUT,
        )
        return response_data(response)
    except requests.RequestException as error:
        return {"success": False, "error": f"Không kết nối được backend: {error}"}


@mcp.tool()
def list_favorite_cities():
    """Lấy danh sách các thành phố yêu thích đã lưu."""
    try:
        response = requests.get(f"{API_URL}/cities", timeout=REQUEST_TIMEOUT)
        return response_data(response)
    except requests.RequestException as error:
        return {"success": False, "error": f"Không kết nối được backend: {error}"}


@mcp.tool()
def save_favorite_city(city: str):
    """Lưu một thành phố vào danh sách yêu thích.

    Args:
        city: Tên thành phố cần lưu.
    """
    try:
        response = requests.post(
            f"{API_URL}/cities",
            json={"city_name": city.strip()},
            timeout=REQUEST_TIMEOUT,
        )
        return response_data(response)
    except requests.RequestException as error:
        return {"success": False, "error": f"Không kết nối được backend: {error}"}


@mcp.tool()
def delete_favorite_city(city: str):
    """Xóa một thành phố khỏi danh sách yêu thích.

    Args:
        city: Tên thành phố cần xóa.
    """
    city_path = quote(city.strip(), safe="")
    try:
        response = requests.delete(
            f"{API_URL}/cities/{city_path}", timeout=REQUEST_TIMEOUT
        )
        return response_data(response)
    except requests.RequestException as error:
        return {"success": False, "error": f"Không kết nối được backend: {error}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")

