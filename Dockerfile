FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# 設定 Streamlit 配置
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Cloud SQL 環境變數 (部署時透過 Cloud Run 設定)
# ENV USE_CLOUD_SQL=true
# ENV DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE
# ENV DB_NAME=buying_system
# ENV DB_USER=postgres
# ENV DB_PASSWORD=your_password

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
