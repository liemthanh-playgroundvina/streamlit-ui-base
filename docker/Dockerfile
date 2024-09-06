FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

CMD ["streamlit", "run", "app/Home.py", "--server.port", "8501", "--server.maxUploadSize", "5"]