FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-flask \
    python3-requests \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py .

EXPOSE 5000
CMD ["python3", "app.py"]