FROM python:3.11-slim-bookworm as builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm
WORKDIR /app

COPY --from=builder /app/main.py .
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]