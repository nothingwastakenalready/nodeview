FROM node:24-alpine AS web-build

WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODEVIEW_CONFIG=/config/services.yaml \
    NODEVIEW_UI=/app/web/dist

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY --from=web-build /web/dist ./web/dist
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 nodeview \
    && mkdir -p /config \
    && chown -R nodeview:nodeview /app /config

USER nodeview
EXPOSE 8080

CMD ["uvicorn", "nodeview.api:app", "--host", "0.0.0.0", "--port", "8080"]
