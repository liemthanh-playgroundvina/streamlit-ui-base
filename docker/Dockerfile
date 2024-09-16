FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app
COPY ./static /app/static
COPY ./scripts /app/scripts
RUN chmod +x scripts/*

CMD ["bash"]