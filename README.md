# Bài 11 — Đưa Weather App lên Internet

## Mục tiêu LAB

Bài 11 giữ lại ứng dụng và phần kiểm thử của Bài 10, đồng thời triển khai:

- Backend FastAPI lên Vercel.
- Frontend lên Streamlit Community Cloud tại <https://share.streamlit.io>.
- API key và URL backend được cấu hình bằng biến môi trường/secrets, không ghi cứng trong code.

## Cấu hình hoạt động như thế nào?

Hai giá trị cần cấu hình nằm ở hai dịch vụ khác nhau:

| Tên | Nơi sử dụng | Local | Khi deploy |
|---|---|---|---|
| `OPENWEATHER_API_KEY` | Backend | File `.env` | Environment Variables của Vercel |
| `API_URL` | Frontend | File `.env` | `st.secrets` trên Streamlit Cloud |

Frontend ưu tiên `st.secrets["API_URL"]`; nếu không có secrets thì mới đọc `API_URL` từ `.env`. Vì thế sau khi Vercel sinh URL, ta chỉ cấu hình URL đó trên Streamlit Cloud, không sửa code và không commit `.env`.

Không đặt `OPENWEATHER_API_KEY` ở frontend: Streamlit chỉ gọi backend, còn backend mới là nơi gọi OpenWeatherMap.

## 1. Chạy local

Mở Terminal tại thư mục `Bai11`.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r frontend/requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r frontend/requirements.txt
cp .env.example .env
```

Sửa `.env`:

```env
OPENWEATHER_API_KEY=api_key_that_cua_em
API_URL=http://localhost:8000
```

Chạy trong hai Terminal:

```powershell
python -m uvicorn backend.main:app --reload
```

```powershell
python -m streamlit run frontend/app.py
```

Chạy test bằng `python -m pytest -v`. Năm test có cách hoàn thiện giống Bài 10.

## 2. Đưa mã nguồn lên GitHub

Tạo một GitHub repository cho riêng Bài 11 rồi đẩy toàn bộ nội dung thư mục này lên. Trước khi push, kiểm tra chắc chắn không có `.env`, `weather.db` hoặc `.streamlit/secrets.toml` trong commit.

`pyproject.toml` chỉ cho Vercel biết FastAPI entrypoint là `backend.main:app`. Không cần chuyển file backend sang thư mục khác.

## 3. Deploy backend lên Vercel

1. Đăng nhập <https://vercel.com> và chọn **Add New → Project**.
2. Import GitHub repository của Bài 11.
3. Nếu Bài 11 là một repository riêng, giữ **Root Directory** là thư mục gốc (`./`).
4. Trong **Environment Variables**, thêm:

   ```text
   OPENWEATHER_API_KEY = api_key_that_cua_em
   ```

5. Bấm **Deploy**.
6. Vercel trả về URL dạng `https://ten-du-an.vercel.app`.
7. Kiểm tra:
   - `https://ten-du-an.vercel.app/`
   - `https://ten-du-an.vercel.app/docs`
   - `https://ten-du-an.vercel.app/weather?city=Hanoi`

Nếu dùng Vercel CLI thay cho giao diện:

```powershell
npm install -g vercel
vercel
vercel env add OPENWEATHER_API_KEY
vercel --prod
```

Sau khi thêm hoặc đổi biến môi trường, hãy redeploy để bản production nhận cấu hình mới.

### Lưu ý về SQLite trên Vercel

Vercel Function chỉ có vùng ghi tạm `/tmp`. Bản này tự dùng `/tmp/weather.db` khi chạy trên Vercel nên chức năng yêu thích có thể demo, nhưng dữ liệu **không bền vững**: có thể mất sau cold start/deploy và có thể khác nhau giữa các instance. Sản phẩm thật cần database ngoài như PostgreSQL/Supabase/Neon; phần đó nằm ngoài phạm vi LAB.

## 4. Deploy frontend lên Streamlit Community Cloud

File `frontend/requirements.txt` được đặt cạnh entrypoint để Streamlit Cloud tự cài đúng thư viện cho frontend.

1. Mở <https://share.streamlit.io> và chọn **Create app**.
2. Chọn repository và branch chứa Bài 11.
3. Đặt **Main file path** là:

   ```text
   frontend/app.py
   ```

4. Mở **Advanced settings → Secrets** và nhập URL backend vừa nhận từ Vercel:

   ```toml
   API_URL = "https://ten-du-an.vercel.app"
   ```

5. Chọn phiên bản Python tương thích, sau đó bấm **Deploy**.

Không tạo hoặc commit `.streamlit/secrets.toml`. Khi cần đổi backend, vào **App settings → Secrets**, sửa `API_URL` rồi lưu; code không cần thay đổi.

## 5. Kiểm tra sản phẩm online

1. Mở URL `streamlit.app`.
2. Tra cứu `Hanoi` và kiểm tra nhiệt độ.
3. Nhìn dòng **Backend** trên giao diện, xác nhận đó là URL Vercel chứ không phải localhost.
4. Thử lưu/xóa thành phố, đồng thời nhớ giới hạn SQLite tạm thời ở trên.

## Nguồn hướng dẫn chính thức

- [FastAPI trên Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- [Quản lý secrets trên Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Tổ chức file cho Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)

## Yêu cầu nộp bài

Repository đã được **fork** vào tài khoản GitHub của em và **clone** về máy từ đầu buổi học. Vì vậy, em không chạy `git init` và không tạo repository mới.

1. Chạy kiểm thử và xác nhận ứng dụng local hoạt động:

   ```powershell
   python -m pytest -v
   ```

   Kết quả kiểm thử cần hiển thị `5 passed`.

2. Kiểm tra remote và các file đã thay đổi:

   ```powershell
   git remote -v
   git status
   ```

   Địa chỉ `origin` phải là repository trong tài khoản GitHub của em. Đảm bảo `.env`, `.vercel`, `.streamlit/secrets.toml`, `weather.db` và API key không được chuẩn bị commit.

3. Thêm bài làm và tạo commit:

   ```powershell
   git add .
   git status
   git commit -m "Hoan thanh Bai 11"
   ```

4. Đẩy nhánh hiện tại lên repository đã fork:

   ```powershell
   git push origin HEAD
   ```

5. Mở repository của em trên GitHub và xác nhận commit mới nhất đã xuất hiện.

6. Nộp đầy đủ:

   - Đường dẫn repository GitHub đã fork.
   - Đường dẫn commit mới nhất của bài làm.
   - URL backend đã deploy trên Vercel.
   - URL frontend đã deploy trên Streamlit Community Cloud.
   - Ảnh chụp ứng dụng online tra cứu thời tiết thành công.
   - Ảnh chụp Terminal có kết quả `5 passed`.

Không nộp API key, file `.env`, `weather.db`, thư mục `.venv` hoặc cấu hình secrets.
