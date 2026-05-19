FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -e .

COPY . .

EXPOSE 5000

CMD ["flask", "--app", "src.app:create_app", "run", "--host", "0.0.0.0", "--port", "5000"]
