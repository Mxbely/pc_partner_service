# FROM python:3.12-slim as base
FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

# RUN apt-get update && apt-get install -y locales && locale-gen uk_UA.UTF-8
# ENV LANG=uk_UA.UTF-8

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

# CMD "xvfb-run -a poetry run uvicorn search_service.main:app --host 0.0.0.0 --port 8000"
CMD ["xvfb-run", "-a", "poetry", "run", "uvicorn", "search_service.main:app", "--host", "0.0.0.0", "--port", "8000"]