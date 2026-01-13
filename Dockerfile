FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN pip install uv
RUN uv sync

COPY . .

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]