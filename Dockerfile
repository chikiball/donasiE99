FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r -s /bin/false appuser && mkdir -p /data && chown appuser:appuser /data
USER appuser
ENV PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:8080", "app:app"]
