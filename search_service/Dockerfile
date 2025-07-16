FROM python:3.12-slim as base

RUN pip install --upgrade pip && \
    pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root

COPY search_service/ /app/

EXPOSE 8000

CMD ["poetry", "run", "fastapi", "run", "main.py"]