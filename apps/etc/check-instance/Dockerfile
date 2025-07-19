FROM python:3.13-slim-bookworm AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim-bookworm
WORKDIR /app

COPY main.py .
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]