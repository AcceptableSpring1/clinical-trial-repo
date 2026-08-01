FROM python:3.14-slim
WORKDIR /app

ENV UV_CACHE_DIR=/tmp/uv-cache

COPY pyproject.toml .
RUN pip install uv && uv sync
COPY . ./
# Copy in the source code

EXPOSE 8000

# Setup an app user so the container doesn't run as the root user
RUN useradd app && mkdir -p /tmp/uv-cache && chown -R app:app /tmp/uv-cache /app

USER app

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]