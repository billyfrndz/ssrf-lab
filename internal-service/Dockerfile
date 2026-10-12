FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-flask \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["python3", "app.py"]