FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app:/app/django_forum"

RUN apt-get update && apt-get install -y \
    netcat-traditional \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock .

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN chmod +x ./docker-entrypoint.sh

RUN mkdir -p ./staticfiles

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["gunicorn", "django_forum.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]