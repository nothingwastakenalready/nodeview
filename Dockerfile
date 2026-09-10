FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODEVIEW_CONFIG=/config/services.yaml

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 nodeview \
    && mkdir -p /config \
    && chown -R nodeview:nodeview /app /config

USER nodeview
EXPOSE 8080

CMD ["uvicorn", "nodeview.api:app", "--host", "0.0.0.0", "--port", "8080"]
