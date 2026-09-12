FROM node:24-alpine AS web-build

WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RAFFAEL_CONFIG=/config/services.yaml \
    RAFFAEL_UI=/app/web/dist \
    RAFFAEL_DATABASE_URL=sqlite:////data/raffael.db

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY --from=web-build /web/dist ./web/dist
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 raffael \
    && mkdir -p /config /data \
    && chown -R raffael:raffael /app /config /data

USER raffael
EXPOSE 8080

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn raffael.api:app --host 0.0.0.0 --port 8080"]
