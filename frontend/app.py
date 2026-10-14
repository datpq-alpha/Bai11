"""Streamlit UI: tra cứu, yêu thích và trợ lý Gemini dùng MCP."""

import asyncio
import os
import sys
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
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
GEMINI_API_KEY = read_setting("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-flash-latest"


class BackendResponseError(RuntimeError):
    """Lỗi cấu hình hoặc phản hồi không hợp lệ từ backend."""


def payload_detail(payload) -> str:
    """Lấy thông báo lỗi trong dữ liệu JSON của FastAPI."""
    return str(payload.get("detail", "")) if isinstance(payload, dict) else ""


def require_json(response: requests.Response):
    """Phát hiện URL sai hoặc Vercel Protection trước khi đọc JSON."""
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        if "vercel.com/login" in response.url:
            raise BackendResponseError(
                "API_URL đang bị chuyển tới trang đăng nhập Vercel. Hãy tắt "
                "Deployment Protection cho Production và dùng domain Production."
            )
        raise BackendResponseError(
            "Backend không trả về JSON. Hãy kiểm tra API_URL trong Streamlit Secrets."
        )
    try:
        return response.json()
    except ValueError as error:
        raise BackendResponseError("Backend trả về JSON không hợp lệ.") from error


def nested_error_details(error: BaseException) -> str:
    """Bóc lỗi thật bên trong ExceptionGroup/TaskGroup của MCP."""
    nested = getattr(error, "exceptions", None)
    if nested:
        details = " | ".join(nested_error_details(item) for item in nested)
    else:
        details = f"{type(error).__name__}: {error}"
    if GEMINI_API_KEY:
        details = details.replace(GEMINI_API_KEY, "***")
    return details


def chat_contents(messages: list[dict]) -> list[types.Content]:
    """Đổi lịch sử Streamlit thành định dạng hội thoại của Gemini."""
    return [
        types.Content(
            role="model" if message["role"] == "assistant" else "user",
            parts=[types.Part.from_text(text=message["content"])],
        )
        for message in messages
    ]


async def ask_weather_assistant(messages: list[dict]) -> str:
    """Kết nối MCP server và để Gemini tự gọi công cụ khi cần."""
    child_environment = os.environ.copy()
    child_environment["API_URL"] = API_URL

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT_DIR / "mcp_server.py")],
        env=child_environment,
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            async with genai.Client(api_key=GEMINI_API_KEY).aio as client:
                response = await client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=chat_contents(messages),
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "Bạn là trợ lý thời tiết thân thiện dành cho học sinh THCS. "
                            "Hãy trả lời ngắn gọn bằng tiếng Việt. Khi người dùng hỏi "
                            "thời tiết hiện tại hoặc muốn xem, lưu, xóa thành phố yêu "
                            "thích, phải dùng công cụ MCP phù hợp và dựa trên kết quả "
                            "công cụ; không tự bịa dữ liệu thời tiết. Nếu yêu cầu chưa "
                            "rõ tên thành phố, hãy hỏi lại."
                        ),
                        temperature=0.3,
                        tools=[session],
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            maximum_remote_calls=6
                        ),
                    ),
                )

    return response.text or "Mình chưa tạo được câu trả lời. Em hãy thử hỏi lại nhé."

st.set_page_config(page_title="Weather Cloud", page_icon="☁️")
st.title("☁️ Weather App trên Cloud")
st.caption(f"Backend: {API_URL}")

search_tab, favorites_tab, assistant_tab = st.tabs(
    ["Tra cứu", "Đã lưu", "Trợ lý thời tiết AI"]
)

with search_tab:
    city = st.text_input("Tên thành phố", placeholder="Ví dụ: Hanoi")
    if st.button("Xem thời tiết", type="primary"):
        try:
            response = requests.get(
                f"{API_URL}/weather", params={"city": city.strip()}, timeout=10
            )
            payload = require_json(response)
            if response.status_code == 200:
                st.session_state["weather"] = payload
            elif response.status_code == 404:
                st.session_state.pop("weather", None)
                st.error("Không tìm thấy thành phố.")
            else:
                st.session_state.pop("weather", None)
                detail = payload_detail(payload)
                st.error(detail or f"Backend trả về lỗi {response.status_code}.")
        except BackendResponseError as error:
            st.error(str(error))
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
                payload = require_json(saved)
                if saved.status_code == 201:
                    st.success("Đã lưu thành phố.")
                elif saved.status_code == 409:
                    st.warning("Thành phố đã có trong danh sách.")
                else:
                    detail = payload_detail(payload)
                    st.error(detail or f"Backend trả về lỗi {saved.status_code}.")
            except BackendResponseError as error:
                st.error(str(error))
            except requests.RequestException:
                st.error("Không kết nối được tới backend.")

with favorites_tab:
    try:
        response = requests.get(f"{API_URL}/cities", timeout=10)
        payload = require_json(response)
        if response.status_code == 200:
            cities = payload
        else:
            cities = []
            detail = payload_detail(payload)
            st.error(detail or f"Backend trả về lỗi {response.status_code}.")
    except BackendResponseError as error:
        cities = []
        st.error(str(error))
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
                payload = require_json(deleted)
                if deleted.status_code == 200:
                    st.rerun()
                else:
                    detail = payload_detail(payload)
                    st.error(detail or f"Backend trả về lỗi {deleted.status_code}.")

with assistant_tab:
    st.subheader("🤖 Trợ lý thời tiết AI")
    st.caption(
        "Hỏi tự nhiên, ví dụ: “Thời tiết Hà Nội thế nào?” hoặc "
        "“Lưu Huế vào danh sách yêu thích”."
    )

    if not GEMINI_API_KEY:
        st.warning(
            "Chưa có GEMINI_API_KEY. Hãy thêm key vào file .env khi chạy local "
            "hoặc Streamlit Secrets khi deploy."
        )
    else:
        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = []

        if st.button("Xóa cuộc trò chuyện", key="clear-chat"):
            st.session_state["chat_messages"] = []
            st.rerun()

        for message in st.session_state["chat_messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Hỏi trợ lý về thời tiết...", key="weather-chat")
        if prompt:
            st.session_state["chat_messages"].append(
                {"role": "user", "content": prompt}
            )
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Trợ lý đang kiểm tra dữ liệu..."):
                    try:
                        answer = asyncio.run(
                            ask_weather_assistant(st.session_state["chat_messages"])
                        )
                    except Exception as error:
                        answer = (
                            "Không thể kết nối tới Gemini hoặc MCP server. "
                            f"Chi tiết: {nested_error_details(error)}"
                        )
                    st.markdown(answer)

            st.session_state["chat_messages"].append(
                {"role": "assistant", "content": answer}
            )

