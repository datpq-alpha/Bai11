"""Streamlit đọc cấu hình local từ .env và cấu hình cloud từ st.secrets."""

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def read_setting(name: str, default: str = "") -> str:
    """Ưu tiên Streamlit secrets; nếu chạy local thì dùng .env."""
    try:
        value = st.secrets[name]
    except (KeyError, StreamlitSecretNotFoundError):
        value = os.getenv(name, default)
    return str(value).strip()


API_URL = read_setting("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Weather Cloud", page_icon="☁️")
st.title("☁️ Weather App trên Cloud")
st.caption(f"Backend: {API_URL}")

search_tab, favorites_tab = st.tabs(["Tra cứu", "Đã lưu"])

with search_tab:
    city = st.text_input("Tên thành phố", placeholder="Ví dụ: Hanoi")
    if st.button("Xem thời tiết", type="primary"):
        try:
            response = requests.get(
                f"{API_URL}/weather", params={"city": city.strip()}, timeout=10
            )
            if response.status_code == 200:
                st.session_state["weather"] = response.json()
            else:
                st.session_state.pop("weather", None)
                st.error("Không tìm thấy thành phố.")
        except requests.RequestException:
            st.error("Không kết nối được tới backend. Hãy kiểm tra API_URL.")

    if "weather" in st.session_state:
        data = st.session_state["weather"]
        st.success(data["city"])
        col1, col2 = st.columns(2)
        col1.metric("Nhiệt độ", f"{data['temp']} °C")
        col2.metric("Độ ẩm", f"{data['humidity']} %")
        st.write(data["description"].capitalize())

        if st.button(f"Lưu {data['city']}"):
            try:
                saved = requests.post(
                    f"{API_URL}/cities",
                    json={"city_name": data["city"]},
                    timeout=10,
                )
                if saved.status_code == 201:
                    st.success("Đã lưu thành phố.")
                elif saved.status_code == 409:
                    st.warning("Thành phố đã có trong danh sách.")
                else:
                    st.error("Không lưu được thành phố.")
            except requests.RequestException:
                st.error("Không kết nối được tới backend.")

with favorites_tab:
    try:
        response = requests.get(f"{API_URL}/cities", timeout=10)
        cities = response.json() if response.status_code == 200 else []
    except requests.RequestException:
        cities = []
        st.error("Không kết nối được tới backend.")

    if not cities:
        st.info("Chưa có thành phố nào được lưu.")
    else:
        for item in cities:
            col_name, col_button = st.columns([3, 1])
            col_name.write(f"📍 {item['city_name']}")
            if col_button.button("Xóa", key=f"delete-{item['id']}"):
                deleted = requests.delete(
                    f"{API_URL}/cities/{item['city_name']}", timeout=10
                )
                if deleted.status_code == 200:
                    st.rerun()
                else:
                    st.error("Không xóa được thành phố.")

