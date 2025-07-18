# FROM python:3.12-slim as base
FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

RUN pip install --upgrade pip && \
    pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root
# RUN poetry run playwright install --with-deps

COPY search_service/ /app/search_service/
COPY templates/ /app/templates

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "search_service.main:app", "--host", "0.0.0.0", "--port", "8000"]